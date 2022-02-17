from django.db.models import Q
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from api.v1.admin_serializers.assignment import AssignmentListSerializer, AssignmentDetailSerializer, \
    FloatedAssignmentSerializer, FloatedAssignmentListSerializer, \
    ExpertSolutionSerializer, AssignmentSolutionSerializer, ExpertSolutionListSerializer, \
    AssignmentSolutionListSerializer, FloatedAssignmentExpertSerializer, PriceQuoteLogSerializer, \
    FloatedAssignmentDetailSerializer, AssignmentPaymentHistorySerializer, AssignmentMemoListSerializer
from api.v1.admin_serializers.users_serializers import UserDetailsSerializer
from apps.assignment.models import Assignment, FloatedAssignment, FloatedAttachments, ExpertSolutionAttachment, \
    ExpertSolution, AssignmentSolution, AssignmentSolutionAttachment, PriceQuoteLog, AssignmentMemos
from rest_framework.views import APIView
from apps.users.models import User, UserActivityLog
from rest_framework.response import Response
from rest_framework import status as status_code, status
from libraries.Functions import get_token_details
from rest_framework import schemas, authentication, permissions
from django.utils import timezone
import coreapi
import coreschema
import random
from libraries.Functions import file_upload_handler, make_dir
from django.conf import settings
from django.db import transaction
from django.db import IntegrityError
from django.http import JsonResponse
from rest_framework.exceptions import NotFound
from django.core.exceptions import ObjectDoesNotExist
from apps.users.helper import user_active_devices, user_all_devices
from libraries.PushNotification import send_notification
from libraries.Email_model import send_user_notify_email
from rest_framework.generics import get_object_or_404
from apps.users.helper import save_user_activity
from apps.payment.models import PaymentTransaction, AssignmentTransaction
from libraries.permission import HasGroupPermission
from django.contrib.auth.models import Permission, Group


class AssignmentListApi(APIView):
    """
    get:
    Returns the list of assignments corresponding to logged in user.
    """
    permission = (Permission.objects.filter(codename='list_assignments'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'POST': group,

    }

    def get(self, request):
        queryset = Assignment.objects.filter(status=True, is_archive=False)
        ordering = request.GET.get('ordering', None)
        search = request.GET.get('search', None)

        if search:
            queryset = queryset.filter(
                Q(assignment_number__icontains=search) | Q(student__name__icontains=search))

        if ordering:
            try:
                queryset = queryset.order_by(ordering)
            except Exception:
                return Response(
                    {
                        'status': status.HTTP_400_BAD_REQUEST,
                        'message': 'Invalid filter arguments'
                    }, status=status.HTTP_400_BAD_REQUEST
                )
        else:
            queryset = queryset.filter(status=True).order_by('-id')

        paginator = PageNumberPagination()
        result_page = paginator.paginate_queryset(queryset, request)

        serializer = AssignmentListSerializer(result_page, many=True)
        s_data = paginator.get_paginated_response(serializer.data)

        return Response(
            {
                'status': status.HTTP_200_OK,
                'message': 'Assignment List fetched',
                'search_keys': 'assignment_number',
                'data': s_data.data
            },
            status=status.HTTP_200_OK
        )


class AssignmentDetailApi(APIView):
    """
    get:
        Return a list of all the details of a assignment corresponding to logged in user.
    """

    permission = (Permission.objects.filter(codename='view_assignments'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'POST': group,

    }

    def get_object(self, id):
        try:
            return Assignment.objects.get(id=id)
        except Assignment.DoesNotExist:
            return Response(
                {
                    'status': status_code.HTTP_404_NOT_FOUND,
                    'message': 'Assignment not found'
                },
                status=status_code.HTTP_404_NOT_FOUND
            )

    def get(self, request, id):
        assignment = self.get_object(id)
        try:
            serializer = AssignmentDetailSerializer(assignment)
            user = User.objects.get(id=serializer.data['student'])
            userserializer = UserDetailsSerializer(user)
            return Response(
                {
                    'status': status_code.HTTP_200_OK,
                    'message': 'Assignment Details Fetched',
                    'data': {
                        'assignment_detail': serializer.data,
                        'user_detail': userserializer.data
                    }
                },
                status=status_code.HTTP_200_OK
            )
        except AttributeError:

            return Response(
                {
                    'status': status_code.HTTP_404_NOT_FOUND,
                    'message': 'Assignment not found'
                },
                status=status_code.HTTP_404_NOT_FOUND
            )


class FloatAssignmentApi(APIView):
    """
          post:
          A post api for Assignment clarification Upload
          """

    permission = (Permission.objects.filter(codename='add_floated_assignments'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'POST': group,

    }

    schema = schemas.ManualSchema(fields=[
        coreapi.Field(
            "assignment",
            required=True,
            location="form",
            schema=coreschema.Integer(
                description="assignment id should be given here(i.e. 18)"
            )
        ),
        coreapi.Field(
            "experts",
            required=True,
            location="form",
            schema=coreschema.String(
                description="expert id's seperated by comma"
            )
        ),
        coreapi.Field(
            "amount",
            required=True,
            location="form",
            schema=coreschema.String(
                description=""
            )
        ),
        coreapi.Field(
            "deadline",
            required=True,
            location="form",
            schema=coreschema.String(
                description="in the date time format i.e '2019-04-02 09:14:52"
            )
        ),
        coreapi.Field(
            "additional_attachments",
            required=True,
            location="form",
            schema=coreschema.String(
                description="additional files concated with assignments file"
            )
        ),
        coreapi.Field(
            "existing_attachments",
            required=True,
            location="form",
            schema=coreschema.String(
                description="additional files concated with assignments file"
            )
        ),
        coreapi.Field(
            "description",
            required=True,
            location="form",
            schema=coreschema.String(
                description="Enter description"
            )
        ),

    ])

    def post(self, request):
        assignment_serializer = FloatedAssignmentSerializer(data=request.data)
        data = request.data
        if assignment_serializer.is_valid():
            """
            verifying if requested assignment exist .
            """

            try:
                assignment = Assignment.objects.get(id=data['assignment'])
            except ObjectDoesNotExist:
                return Response(
                    {
                        'status': status.HTTP_404_NOT_FOUND,
                        'message': 'assignment coresponding to this user not found'
                    }
                )
            expert_list = data['experts'].split(",")

            for expert in expert_list:
                user = User.objects.get(id=int(expert))

                if FloatedAssignment.objects.filter(assignment=assignment, expert=user).exists():
                    return Response(
                        {
                            'status': status.HTTP_400_BAD_REQUEST,
                            'message': ('assignment already floated to', user.email)
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                assignment_floated = FloatedAssignment.objects.create(
                    assignment=assignment,
                    description=data['description'],
                    expert=user,
                    deadline=data['deadline'],
                    created_on=timezone.now(),
                    updated_on=timezone.now(),
                    amount=data['amount']

                )
                assignment.save()

                if 'additional_attachments' in data:

                    if 'existing_attachments' in data:

                        for file in self.request.data.getlist('additional_attachments'):
                            rndm = random.randint(100000, 9999999)
                            upload_dir = make_dir(
                                settings.MEDIA_ROOT + settings.CUSTOM_DIRS.get('FLOATED_DIR') + '/' + str(
                                    rndm) + '/'
                            )
                            file_name = file_upload_handler(file, upload_dir)
                            attachment = settings.MEDIA_URL + '/' + settings.CUSTOM_DIRS.get(
                                'FLOATED_DIR') + '/' + str(rndm) + '/' + file_name
                            FloatedAttachments.objects.create(
                                assignment=assignment_floated,
                                attachment=attachment,
                                created_on=timezone.now(),
                                updated_on=timezone.now(),

                            )

                        # existing_files = ','.join(map(str, request.data['existing_files']))
                        # print(existing_files)
                        existing_files = request.data['existing_attachments'].split(",")

                        for file in existing_files:
                            FloatedAttachments.objects.create(
                                assignment=assignment_floated,
                                attachment=file,
                                created_on=timezone.now(),
                                updated_on=timezone.now(),

                            )

                    else:

                        for file in self.request.data.getlist('additional_attachments'):
                            rndm = random.randint(100000, 9999999)
                            upload_dir = make_dir(
                                settings.MEDIA_ROOT + settings.CUSTOM_DIRS.get('FLOATED_DIR') + '/' + str(
                                    rndm) + '/'
                            )
                            file_name = file_upload_handler(file, upload_dir)
                            attachment = settings.MEDIA_URL + '/' + settings.CUSTOM_DIRS.get(
                                'FLOATED_DIR') + '/' + str(rndm) + '/' + file_name
                            FloatedAttachments.objects.create(
                                assignment=assignment_floated,
                                attachment=attachment,
                                created_on=timezone.now(),
                                updated_on=timezone.now(),

                            )
                else:
                    if 'existing_attachments' in data:

                        existing_files = request.data['existing_attachments'].split(",")

                        for file in existing_files:
                            FloatedAttachments.objects.create(
                                assignment=assignment_floated,
                                attachment=file,
                                created_on=timezone.now(),
                                updated_on=timezone.now(),

                            )

            return Response(
                {
                    'status': status.HTTP_201_CREATED,
                    'message': 'Assignment Floated'
                },
                status=status_code.HTTP_201_CREATED
            )

            # """
            # if there is no attachments in floated
            #
            # """
            #
            # FloatedAssignment.objects.create(
            #     assignment=assignment,
            #     description=data['description'],
            #     expert=user,
            #     deadline=data['deadline'],
            #     created_on=timezone.datetime.now(),
            #     updated_on=timezone.datetime.now(),
            #     amount=data['amount']
            #
            # )
            # """
            # Changing the status of parent assignment of floated
            #
            # """
            #
            # assignment.updated_on = timezone.datetime.now()
            # assignment.save()

            # else:
            #     """
            #     if attachments are there with the floated
            #     """
            #     try:
            #         with transaction.atomic():
            #             assignmentfloated = FloatedAssignment.objects.create(
            #                 assignment=assignment,
            #                 description=data['description'],
            #                 amount=data['amount'],
            #                 expert=user,
            #                 deadline=data['deadline'],
            #                 created_on=timezone.datetime.now(),
            #                 updated_on=timezone.datetime.now(),
            #
            #             )
            #
            #             """
            #                 Changing the status of parent assignment of floated assignment
            #
            #             """
            #
            #             assignment.updated_on = timezone.datetime.now()
            #             assignment.save()

            # for file in self.request.data.getlist('additional_attachments'):
            #     rndm = random.randint(100000, 9999999)
            #     upload_dir = make_dir(
            #         settings.MEDIA_ROOT + settings.CUSTOM_DIRS.get('FLOATED_DIR') + '/' + str(
            #             rndm) + '/'
            #     )
            #     file_name = file_upload_handler(file, upload_dir)
            #     attachment = settings.MEDIA_URL + '/' + settings.CUSTOM_DIRS.get(
            #         'FLOATED_DIR') + '/' + str(rndm) + '/' + file_name
            #     FloatedAttachments.objects.create(
            #         assignment=assignmentfloated,
            #         attachment=attachment,
            #         created_on=timezone.datetime.now(),
            #         updated_on=timezone.datetime.now(),
            #
            #     )
            #
            # # existing_files = ','.join(map(str, request.data['existing_files']))
            # # print(existing_files)
            # existing_files = request.data['existing_files'].split(",")
            #
            # for file in existing_files:
            #
            #     FloatedAttachments.objects.create(
            #         assignment=assignmentfloated,
            #         attachment=file,
            #         created_on=timezone.datetime.now(),
            #         updated_on=timezone.datetime.now(),
            #
            #     )

            #         except IntegrityError:
            #             return JsonResponse({'error': 'Assignment  not floated'})
            #
            # return Response(
            #     {
            #         'status': status.HTTP_201_CREATED,
            #         'message': 'Assignment Floated'
            #     },
            #     status=status_code.HTTP_201_CREATED
            # )

        return Response(assignment_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NewAssignmentListApi(APIView):
    """
    get:
    Returns the list of New assignments corresponding to logged in user.
    """
    permission = (Permission.objects.filter(codename='list_assignments'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'POST': group,

    }

    def get(self, request):
        queryset = Assignment.objects.filter(status=True,
                                             assignment_status=settings.ASSIGNMENT_STATUS.get('NEW_ASSIGNMENT'),
                                             is_archive=False)
        ordering = request.GET.get('ordering', None)
        search = request.GET.get('search', None)

        if search:
            queryset = queryset.filter(
                Q(assignment_number__icontains=search) | Q(student__name__icontains=search))

        if ordering:
            try:
                queryset = queryset.order_by(ordering)
            except Exception:
                return Response(
                    {
                        'status': status.HTTP_400_BAD_REQUEST,
                        'message': 'Invalid filter arguments'
                    }, status=status.HTTP_400_BAD_REQUEST
                )
        else:
            queryset = queryset.filter(status=True).order_by('-id')

        paginator = PageNumberPagination()
        result_page = paginator.paginate_queryset(queryset, request)

        serializer = AssignmentListSerializer(result_page, many=True)
        s_data = paginator.get_paginated_response(serializer.data)

        return Response(
            {
                'status': status.HTTP_200_OK,
                'message': 'new Assignment List fetched',
                'search_keys': ('assignment_number', 'user_name'),
                'data': s_data.data
            },
            status=status.HTTP_200_OK
        )


class UnpaidAssignmentListApi(APIView):
    """
    get:
    Returns the list of Unpaid assignments corresponding to logged in user.
    """

    permission = (Permission.objects.filter(codename='list_assignments'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'POST': group,

    }

    def get(self, request):

        queryset = Assignment.objects.filter(status=True,
                                             assignment_status=settings.ASSIGNMENT_STATUS.get('UNPAID_ASSIGNMENT'),
                                             is_archive=False)
        ordering = request.GET.get('ordering', None)
        search = request.GET.get('search', None)

        if search:
            queryset = queryset.filter(
                Q(assignment_number__icontains=search) | Q(student__name__icontains=search))

        if ordering:
            try:
                queryset = queryset.order_by(ordering)
            except Exception:
                return Response(
                    {
                        'status': status.HTTP_400_BAD_REQUEST,
                        'message': 'Invalid filter arguments'
                    }, status=status.HTTP_400_BAD_REQUEST
                )
        else:
            queryset = queryset.filter(status=True).order_by('-id')

        paginator = PageNumberPagination()
        result_page = paginator.paginate_queryset(queryset, request)

        serializer = AssignmentListSerializer(result_page, many=True)
        s_data = paginator.get_paginated_response(serializer.data)

        return Response(
            {
                'status': status.HTTP_200_OK,
                'message': 'Unpaid Assignment List fetched',
                'search_keys': ('assignment_number', 'user_name'),
                'data': s_data.data
            },
            status=status.HTTP_200_OK
        )


class PaidAssignmentListApi(APIView):
    """
    get:
    Returns the list of Paid assignments corresponding to logged in user.
    """

    permission = (Permission.objects.filter(codename='list_assignments'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'POST': group,

    }

    def get(self, request):
        queryset = Assignment.objects.filter(status=True,
                                             assignment_status=settings.ASSIGNMENT_STATUS.get('PAID_ASSIGNMENT'),
                                             is_archive=False)
        ordering = request.GET.get('ordering', None)
        search = request.GET.get('search', None)

        if search:
            queryset = queryset.filter(
                Q(assignment_number__icontains=search))

        if ordering:
            try:
                queryset = queryset.order_by(ordering)
            except Exception:
                return Response(
                    {
                        'status': status.HTTP_400_BAD_REQUEST,
                        'message': 'Invalid filter arguments'
                    }, status=status.HTTP_400_BAD_REQUEST
                )
        else:
            queryset = queryset.filter(status=True).order_by('-id')

        paginator = PageNumberPagination()
        result_page = paginator.paginate_queryset(queryset, request)

        serializer = AssignmentListSerializer(result_page, many=True)
        s_data = paginator.get_paginated_response(serializer.data)

        return Response(
            {
                'status': status.HTTP_200_OK,
                'message': 'paid Assignment List fetched',
                'search_keys': 'assignment_number',
                'data': s_data.data
            },
            status=status.HTTP_200_OK
        )


class ClarificationAssignmentListApi(APIView):
    """
    get:
    Returns the list of Clarification assignments corresponding to logged in user.
    """

    permission = (Permission.objects.filter(codename='list_AssignmentClarification'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'POST': group,

    }

    def get(self, request):
        queryset = Assignment.objects.filter(status=True,
                                             assignment_status=settings.ASSIGNMENT_STATUS.get(
                                                 'CLARIFICATION_ASSIGNMENT'), is_archive=False)
        ordering = request.GET.get('ordering', None)
        search = request.GET.get('search', None)

        if search:
            queryset = queryset.filter(
                Q(assignment_number__icontains=search) | Q(student__name__icontains=search))

        if ordering:
            try:
                queryset = queryset.order_by(ordering)
            except Exception:
                return Response(
                    {
                        'status': status.HTTP_400_BAD_REQUEST,
                        'message': 'Invalid filter arguments'
                    }, status=status.HTTP_400_BAD_REQUEST
                )
        else:
            queryset = queryset.filter(status=True).order_by('-id')

        paginator = PageNumberPagination()
        result_page = paginator.paginate_queryset(queryset, request)

        serializer = AssignmentListSerializer(result_page, many=True)
        s_data = paginator.get_paginated_response(serializer.data)

        return Response(
            {
                'status': status.HTTP_200_OK,
                'message': 'clarification Assignment List fetched',
                'search_keys': 'assignment_number',
                'data': s_data.data
            },
            status=status.HTTP_200_OK
        )


class ExpertClarificationAssignmentListApi(APIView):
    """
    get:
    Returns the list of Clarification assignments corresponding to logged in user.
    """
    permission = (Permission.objects.filter(codename='list_assignments'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'POST': group,

    }

    def get(self, request):
        queryset = Assignment.objects.filter(status=True,
                                             assignment_status=settings.ASSIGNMENT_STATUS.get(
                                                 'CLARIFICATION_ASSIGNMENT'), floated_assignment__expert=request.user)
        ordering = request.GET.get('ordering', None)
        search = request.GET.get('search', None)

        if search:
            queryset = queryset.filter(
                Q(assignment_number__icontains=search) | Q(student__name__icontains=search))

        if ordering:
            try:
                queryset = queryset.order_by(ordering)
            except Exception:
                return Response(
                    {
                        'status': status.HTTP_400_BAD_REQUEST,
                        'message': 'Invalid filter arguments'
                    }, status=status.HTTP_400_BAD_REQUEST
                )
        else:
            queryset = queryset.filter(status=True).order_by('-id')
        paginator = PageNumberPagination()
        result_page = paginator.paginate_queryset(queryset, request)

        serializer = AssignmentListSerializer(result_page, many=True)
        s_data = paginator.get_paginated_response(serializer.data)

        return Response(
            {
                'status': status.HTTP_200_OK,
                'message': 'clarification Assignment List fetched',
                'data': s_data.data
            },
            status=status.HTTP_200_OK
        )


class ExpertAssignedAssignmentListApi(APIView):
    """
    get:
    Returns the list of Clarification assignments corresponding to logged in user.
    """
    permission = (Permission.objects.filter(codename='list_assignments'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'POST': group,

    }

    def get(self, request):
        queryset = Assignment.objects.filter(
            status=True, is_assigned=True,
            floated_assignment__expert=request.user, floated_assignment__assigned_status=True).distinct()
        ordering = request.GET.get('ordering', None)
        search = request.GET.get('search', None)

        if search:
            queryset = queryset.filter(
                Q(assignment_number__icontains=search) | Q(student__name__icontains=search))

        if ordering:
            try:
                queryset = queryset.order_by(ordering)
            except Exception:
                return Response(
                    {
                        'status': status.HTTP_400_BAD_REQUEST,
                        'message': 'Invalid filter arguments'
                    }, status=status.HTTP_400_BAD_REQUEST
                )
        else:
            queryset = queryset.filter(status=True).order_by('-id')

        paginator = PageNumberPagination()
        result_page = paginator.paginate_queryset(queryset, request)

        serializer = AssignmentListSerializer(result_page, many=True)
        s_data = paginator.get_paginated_response(serializer.data)

        return Response(
            {
                'status': status.HTTP_200_OK,
                'message': 'assigned Assignment List fetched',
                'data': s_data.data
            },
            status=status.HTTP_200_OK
        )


class CompletedAssignmentListApi(APIView):
    """
    get:
    Returns the list of assignments corresponding to logged in user.
    """

    permission = (Permission.objects.filter(codename='list_assignments'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'POST': group,

    }

    def get(self, request):
        queryset = Assignment.objects.filter(status=True,
                                             assignment_status=settings.ASSIGNMENT_STATUS.get(
                                                 'COMPLETED_ASSIGNMENT'), is_archive=False)
        ordering = request.GET.get('ordering', None)
        search = request.GET.get('search', None)

        if search:
            queryset = queryset.filter(
                Q(assignment_number__icontains=search) | Q(student__name__icontains=search))

        if ordering:
            try:
                queryset = queryset.order_by(ordering)
            except Exception:
                return Response(
                    {
                        'status': status.HTTP_400_BAD_REQUEST,
                        'message': 'Invalid filter arguments'
                    }, status=status.HTTP_400_BAD_REQUEST
                )
        else:
            queryset = queryset.filter(status=True).order_by('-id')

        paginator = PageNumberPagination()
        result_page = paginator.paginate_queryset(queryset, request)

        serializer = AssignmentListSerializer(result_page, many=True)
        s_data = paginator.get_paginated_response(serializer.data)

        return Response(
            {
                'status': status.HTTP_200_OK,
                'message': 'completed Assignment List fetched',
                'search_keys': 'assignment_number',
                'data': s_data.data
            },
            status=status.HTTP_200_OK
        )


class ExpertCompletedAssignmentListApi(APIView):
    """
    get:
    Returns the list of assignments corresponding to logged in user.
    """

    permission = (Permission.objects.filter(codename='list_assignments'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'POST': group,

    }

    def get(self, request):
        queryset = Assignment.objects.filter(assignment_status=settings.ASSIGNMENT_STATUS.get(
            'COMPLETED_ASSIGNMENT'), floated_assignment__expert=request.user)

        ordering = request.GET.get('ordering', None)
        search = request.GET.get('search', None)

        if search:
            queryset = queryset.filter(
                Q(assignment_number__icontains=search) | Q(student__name__icontains=search))

        if ordering:
            try:
                queryset = queryset.order_by(ordering)
            except Exception:
                return Response(
                    {
                        'status': status.HTTP_400_BAD_REQUEST,
                        'message': 'Invalid filter arguments'
                    }, status=status.HTTP_400_BAD_REQUEST
                )
        else:
            queryset = queryset.order_by('-id')

        paginator = PageNumberPagination()
        result_page = paginator.paginate_queryset(queryset, request)

        serializer = AssignmentListSerializer(result_page, many=True)
        s_data = paginator.get_paginated_response(serializer.data)

        return Response(
            {
                'status': status.HTTP_200_OK,
                'message': 'completed Assignment List fetched',
                'search_keys': 'assignment_number',
                'data': s_data.data
            },
            status=status.HTTP_200_OK
        )


class FloatedAssignmentList(APIView):
    """
        get:
        Returns the list of floated assignments with experts.
        """

    permission = (Permission.objects.filter(codename='list_floated_assignments'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'POST': group,

    }

    def get(self, request):
        if request.user.is_superuser:
            queryset = FloatedAssignment.objects.all()
        else:
            queryset = FloatedAssignment.objects.filter(expert=request.user)
        ordering = request.GET.get('ordering', None)
        search = request.GET.get('search', None)

        if search:
            queryset = queryset.filter(
                Q(assignment_number__icontains=search))

        if ordering:
            try:
                queryset = queryset.order_by(ordering)
            except Exception:
                return Response(
                    {
                        'status': status.HTTP_400_BAD_REQUEST,
                        'message': 'Invalid filter arguments'
                    }, status=status.HTTP_400_BAD_REQUEST
                )
        else:
            queryset = queryset.filter().order_by('-id')

        paginator = PageNumberPagination()
        result_page = paginator.paginate_queryset(queryset, request)

        serializer = FloatedAssignmentListSerializer(result_page, many=True)
        s_data = paginator.get_paginated_response(serializer.data)

        return Response(
            {
                'status': status_code.HTTP_200_OK,
                'message': 'floated Assignment list fetched',
                'data': s_data.data
            },
            status=status_code.HTTP_200_OK
        )


class IsInterested(APIView):
    """
         put:
    Change to interested status of floated assignmnet corresponding to the user as True
        """

    # permission = (Permission.objects.filter(codename='add_country'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'POST': group,
    #
    # }

    def get_object(self, id):
        try:
            return FloatedAssignment.objects.get(assignment_id=id, expert=self.request.user)
        except ObjectDoesNotExist:
            raise NotFound(detail="Error 404 ,assignmnet corresponding to user not found", code=404)

    def put(self, request, id):
        assignment = self.get_object(id)
        assignment.interested = True
        assignment.save()

        return Response(
            {
                'status': status_code.HTTP_200_OK,
                'message': 'Marked as Interested',
                'data': {'interested': assignment.interested}
            },
            status=status_code.HTTP_200_OK
        )


class EditFloatedAssignment(APIView):
    """
    modifying the floated assignments

    """

    permission = (Permission.objects.filter(codename='edit_floated_assignments'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'POST': group,

    }

    schema = schemas.ManualSchema(fields=[
        coreapi.Field(
            "assignment",
            required=True,
            location="form",
            schema=coreschema.Integer(
                description="assignment id should be given here(i.e. 18)"
            )
        ),

        coreapi.Field(
            "amount",
            required=True,
            location="form",
            schema=coreschema.String(
                description=""
            )
        ),
        coreapi.Field(
            "deadline",
            required=True,
            location="form",
            schema=coreschema.String(
                description="in the date time format i.e '2019-04-02 09:14:52"
            )
        ),
        coreapi.Field(
            "existing_attachments",
            required=False,
            location="form",
            schema=coreschema.String(
                description="additional file concated with assignments file"
            )
        ),
        coreapi.Field(
            "additional_attachments",
            required=False,
            location="form",
            schema=coreschema.String(
                description="additional file concated with assignments file"
            )
        ),

    ])

    def post(self, request):
        assignment = FloatedAssignment.objects.filter(id=request.data['assignment'])
        serializer = FloatedAssignmentSerializer(assignment, request.data)
        print(request.data)
        if serializer.is_valid():
            """
            if there is no attachments in the data
            
            """
            if FloatedAttachments.objects.filter(assignment=assignment[0]).exists():
                FloatedAttachments.objects.filter(assignment=assignment[0]).delete()

            if 'existing_attachments' in request.data:
                existing_files = request.data['existing_attachments'].split(",")

                for file in existing_files:
                    FloatedAttachments.objects.create(
                        assignment=assignment[0],
                        attachment=file,
                        created_on=timezone.now(),
                        updated_on=timezone.now(),

                    )

                    # for file in self.request.data.getlist('existing_attachments'):
                    #     rndm = random.randint(100000, 9999999)
                    #     upload_dir = make_dir(
                    #         settings.MEDIA_ROOT + settings.CUSTOM_DIRS.get('FLOATED_DIR') + '/' + str(
                    #             rndm) + '/'
                    #     )
                    #     file_name = file_upload_handler(file, upload_dir)
                    #     attachment = settings.MEDIA_URL + '/' + settings.CUSTOM_DIRS.get(
                    #         'FLOATED_DIR') + '/' + str(rndm) + '/' + file_name
                    #
                    #     FloatedAttachments.objects.create(
                    #                 assignment=assignment[0],
                    #                 attachment=attachment,
                    #                 created_on=timezone.datetime.now(),
                    #                 updated_on=timezone.datetime.now(),
                    #     )

            if 'additional_attachments' in request.data:

                for file in self.request.data.getlist('additional_attachments'):
                    rndm = random.randint(100000, 9999999)
                    upload_dir = make_dir(
                        settings.MEDIA_ROOT + settings.CUSTOM_DIRS.get('FLOATED_DIR') + '/' + str(
                            rndm) + '/'
                    )
                    file_name = file_upload_handler(file, upload_dir)
                    attachment = settings.MEDIA_URL + settings.CUSTOM_DIRS.get(
                        'FLOATED_DIR') + '/' + str(rndm) + '/' + file_name

                    FloatedAttachments.objects.create(
                        assignment=assignment[0],
                        attachment=attachment,
                        created_on=timezone.now(),
                        updated_on=timezone.now(),
                    )

            serializer.validated_data.pop('attachments')
            assignment.update(**serializer.validated_data)

            return Response(
                {
                    'status': status_code.HTTP_200_OK,
                    'message': 'updated with attachments'
                },
                status=status_code.HTTP_200_OK
            )

            # if 'attachments' not in request.data:
            #     serializer.validated_data.pop('attachments')
            #     assignment.update(**serializer.validated_data)
            #
            #     return Response(
            #         {
            #             'status': status_code.HTTP_200_OK,
            #             'message': 'updated'
            #         },
            #         status=status_code.HTTP_200_OK
            #     )
            # else:
            #     """
            #     if there is attachments available in data
            #     """
            #     if FloatedAttachments.objects.filter(assignment=assignment[0]).exists():
            #         FloatedAttachments.objects.filter(assignment=assignment[0]).delete()
            #     for file in self.request.data.getlist('attachments'):
            #         rndm = random.randint(100000, 9999999)
            #         upload_dir = make_dir(
            #             settings.MEDIA_ROOT + settings.CUSTOM_DIRS.get('FLOATED_DIR') + '/' + str(
            #                 rndm) + '/'
            #         )
            #         file_name = file_upload_handler(file, upload_dir)
            #         attachment = settings.MEDIA_URL + '/' + settings.CUSTOM_DIRS.get(
            #             'FLOATED_DIR') + '/' + str(rndm) + '/' + file_name
            #         FloatedAttachments.objects.create(
            #             assignment=assignment[0],
            #             attachment=attachment,
            #             created_on=timezone.datetime.now(),
            #             updated_on=timezone.datetime.now(),
            #
            #         )
            #     serializer.validated_data.pop('attachments')
            #     serializer.validated_data.update({'updated_on': timezone.now()})
            #     assignment.update(**serializer.validated_data)
            #

        return Response(
            {
                'error': serializer.errors
            }
        )


class FloatedDetail(APIView):

    """
    API for the Detail of floated assignment
    """

    permission = (Permission.objects.filter(codename='view_floated_assignments'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'POST': group,

    }

    def get_object(self, id):
        try:
            return FloatedAssignment.objects.get(id=id)
        except ObjectDoesNotExist:
            raise NotFound(detail="Error 404 ,assignmnet corresponding to user not found", code=404)

    def get(self, request, id):
        floatedassignment = self.get_object(id)
        serializer = FloatedAssignmentDetailSerializer(floatedassignment)
        return Response(
            {
                'status': status.HTTP_200_OK,
                'message': 'assignment detail fetched',
                'data': serializer.data
            }
        )


class ExpertFloatedDetail(APIView):

    """
    API for thr Detail of floated assignment detail to the expert
    """
    permission = (Permission.objects.filter(codename='view_floated_assignments'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'POST': group,

    }

    def get_object(self, id):
        try:
            return FloatedAssignment.objects.get(assignment_id=id, expert=self.request.user)
        except ObjectDoesNotExist:
            raise NotFound(detail="Error 404 ,assignment corresponding to user not found", code=404)

    def get(self, request, id):
        floatedassignment = self.get_object(id)
        serializer = FloatedAssignmentDetailSerializer(floatedassignment)
        return Response(
            {
                'status': status.HTTP_200_OK,
                'message': 'assignment detail fetched',
                'data': serializer.data
            }
        )


class AssignAssignment(APIView):
    """
    api for assigning the floated assignment to the interested expert
    """

    # permission = (Permission.objects.filter(codename='add_country'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'POST': group,
    #
    # }

    def get_object(self, id):
        try:
            return FloatedAssignment.objects.get(id=id)
        except ObjectDoesNotExist:
            raise NotFound(detail="Error 404 ,assignmnet corresponding to user not found", code=404)

    def put(self, request, id):
        floatedassignment = self.get_object(id)
        if not floatedassignment.assigned_status:
            floatedassignment.assigned_status = True
            floatedassignment.save()
        else:
            floatedassignment.assigned_status = False
            floatedassignment.save()

        assignment = Assignment.objects.get(id=floatedassignment.assignment_id)
        assignment.is_assigned = True
        assignment.save()

        return Response(
            {
                'status': status_code.HTTP_200_OK,
                'message': 'Assigned'

            },
            status=status_code.HTTP_200_OK
        )


class ExpertSolutionApi(APIView):
    """
    post:
    api for solution given by experts.
    """

    permission = (Permission.objects.filter(codename='upload_expert_solution'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'POST': group,

    }

    schema = schemas.ManualSchema(fields=[
        coreapi.Field(
            "assignment",
            required=True,
            location="form",
            schema=coreschema.Integer(
                description="assignment id should be given here(i.e. 18)"
            )
        ),

        coreapi.Field(
            "description",
            required=True,
            location="form",
            schema=coreschema.String(
                description=""
            )
        ),
        coreapi.Field(
            "attachments",
            required=False,
            location="form",
            schema=coreschema.String(
                description="files here"
            )
        ),

    ])

    def post(self, request):

        serializer = ExpertSolutionSerializer(data=request.data)
        if serializer.is_valid():
            expert_solution = ExpertSolution.objects.create(
                assignment=serializer.validated_data['assignment'],
                description=serializer.validated_data['description'],
                created_on=timezone.now(),
                updated_on=timezone.now(),
                submitted_by=request.user

            )

            if 'attachments' in request.data:
                for file in self.request.data.getlist('attachments'):
                    rndm = random.randint(100000, 9999999)
                    upload_dir = make_dir(
                        settings.MEDIA_ROOT + settings.CUSTOM_DIRS.get('EXPERT_SOLUTION_DIR') + '/' + str(
                            rndm) + '/'
                    )
                    file_name = file_upload_handler(file, upload_dir)
                    attachment = settings.MEDIA_URL + '/' + settings.CUSTOM_DIRS.get(
                        'EXPERT_SOLUTION_DIR') + '/' + str(rndm) + '/' + file_name
                    ExpertSolutionAttachment.objects.create(
                        expert_solution=expert_solution,
                        attachment=attachment,
                        created_on=timezone.now(),
                        updated_on=timezone.now(),

                    )
            return Response(
                {
                    'status': status.HTTP_201_CREATED,
                    'message': 'solution successfully submitted'
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExpertSolutionList(APIView):

    permission = (Permission.objects.filter(codename='list_expert_solution'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'POST': group,

    }

    def get(self, request, id):
        queryset = ExpertSolution.objects.filter(status=True, assignment_id=id, submitted_by=self.request.user)
        serializer = ExpertSolutionListSerializer(queryset, many=True)
        return Response(
            {
                'status': status_code.HTTP_200_OK,
                'message': 'expert solution list fetched',
                'data': serializer.data
            },
            status=status_code.HTTP_200_OK
        )


class AssignmentSolutionList(APIView):

    permission = (Permission.objects.filter(codename='list_assignment_solution'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'POST': group,

    }

    def get(self, request, id):
        queryset = ExpertSolution.objects.filter(status=True, assignment_id=id)
        serializer = ExpertSolutionListSerializer(queryset, many=True)
        return Response(
            {
                'status': status_code.HTTP_200_OK,
                'message': 'solution list fetched',
                'data': serializer.data
            },
            status=status_code.HTTP_200_OK
        )


class ExpertsolutionDetailApi(APIView):
    """
    get:
        Return a list of all the details of a expert solution corresponding to id.
    """

    permission = (Permission.objects.filter(codename='view_expert_solution'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'POST': group,

    }

    def get_object(self, id):
        try:
            return ExpertSolution.objects.get(id=id)
        except ExpertSolution.DoesNotExist:
            return Response(
                {
                    'status': status_code.HTTP_404_NOT_FOUND,
                    'message': 'solution not found'
                },
                status=status_code.HTTP_404_NOT_FOUND
            )

    def get(self, request, id):
        solution = self.get_object(id)
        try:
            serializer = ExpertSolutionListSerializer(solution)
            return Response(
                {
                    'status': status_code.HTTP_200_OK,
                    'message': 'solution Details Fetched',
                    'data': {
                        'solution_detail': serializer.data,
                    }
                },
                status=status_code.HTTP_200_OK
            )
        except AttributeError:

            return Response(
                {
                    'status': status_code.HTTP_404_NOT_FOUND,
                    'message': 'solution not found'
                },
                status=status_code.HTTP_404_NOT_FOUND
            )


class AssignmentSolutionApi(APIView):
    """
    post:
    api for submitting the final soution of assignment
    """
    schema = schemas.ManualSchema(fields=[
        coreapi.Field(
            "assignment",
            required=True,
            location="form",
            schema=coreschema.Integer(
                description="assignment id should be given here(i.e. 18)"
            )
        ),

        coreapi.Field(
            "description",
            required=True,
            location="form",
            schema=coreschema.String(
                description=""
            )
        ),
        coreapi.Field(
            "attachments",
            required=False,
            location="form",
            schema=coreschema.String(
                description="files here"
            )
        ),

    ])

    permission = (Permission.objects.filter(codename='upload_assignment_solution'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'POST': group,

    }

    def post(self, request):

        serializer = AssignmentSolutionSerializer(data=request.data)
        if serializer.is_valid():
            expert_solution = AssignmentSolution.objects.create(
                assignment=serializer.validated_data['assignment'],
                description=serializer.validated_data['description'],
                created_on=timezone.now(),
                updated_on=timezone.now(),
                submitted_by=request.user

            )

            if 'attachments' in request.data:
                for file in self.request.data.getlist('attachments'):
                    rndm = random.randint(100000, 9999999)
                    upload_dir = make_dir(
                        settings.MEDIA_ROOT + settings.CUSTOM_DIRS.get('ASSIGNMENT_SOLUTION_DIR') + '/' + str(
                            rndm) + '/'
                    )
                    file_name = file_upload_handler(file, upload_dir)
                    attachment = settings.MEDIA_URL + '/' + settings.CUSTOM_DIRS.get(
                        'ASSIGNMENT_SOLUTION_DIR') + '/' + str(rndm) + '/' + file_name
                    AssignmentSolutionAttachment.objects.create(
                        assignment_solution=expert_solution,
                        attachment=attachment,
                        created_on=timezone.now(),
                        updated_on=timezone.now(),

                    )
            assignment = serializer.validated_data['assignment']
            assignment.assignment_status = settings.ASSIGNMENT_STATUS.get(
                'COMPLETED_ASSIGNMENT')
            assignment.save()

            return Response(
                {
                    'status': status.HTTP_201_CREATED,
                    'message': 'solution successfully submitted'
                },
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class AssignmentSolutionList(APIView):
#     """
#     get:
#         Return a list of assignment solutions
#     """
#
#     def get(self,request, id):
#         queryset = AssignmentSolution.objects.filter(status=True, assignment_id=id, submitted_by=self.request.user)
#         serializer = AssignmentSolutionListSerializer(queryset, many=True)
#         return Response(
#             {
#                 'status': status_code.HTTP_200_OK,
#                 'message': 'expert solution list fetched',
#                 'data': serializer.data
#             },
#             status=status_code.HTTP_200_OK
#         )


class AssignmentSolutionDetailApi(APIView):
    """
    get:
        Return a list of all the details of a solution corresponding to id.
    """

    permission = (Permission.objects.filter(codename='view_assignment_solution'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'POST': group,

    }

    def get_object(self, id):
        try:
            return AssignmentSolution.objects.get(id=id)
        except AssignmentSolution.DoesNotExist:
            return Response(
                {
                    'status': status_code.HTTP_404_NOT_FOUND,
                    'message': 'solution not found'
                },
                status=status_code.HTTP_404_NOT_FOUND
            )

    def get(self, request, id):
        solution = self.get_object(id)
        try:
            serializer = AssignmentSolutionListSerializer(solution)
            return Response(
                {
                    'status': status_code.HTTP_200_OK,
                    'message': 'solution Details Fetched',
                    'data': {
                        'solution_detail': serializer.data,
                    }
                },
                status=status_code.HTTP_200_OK
            )
        except AttributeError:

            return Response(
                {
                    'status': status_code.HTTP_404_NOT_FOUND,
                    'message': 'solution not found'
                },
                status=status_code.HTTP_404_NOT_FOUND
            )


class FloatedExpertList(APIView):

    # permission = (Permission.objects.filter(codename='add_country'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'POST': group,
    #
    # }

    def get(self, request, id):
        floatedassignment = FloatedAssignment.objects.filter(assignment_id=id)
        serializer = FloatedAssignmentExpertSerializer(floatedassignment, many=True)
        return Response(
            {
                'status': status.HTTP_200_OK,
                'data': serializer.data
            }
        )


class PriceQuoteHistory(APIView):
    """
    post:
    API for getting history of price quote
    """

    schema = schemas.ManualSchema(fields=[
        coreapi.Field(
            "assignment_id",
            required=True,
            location="form",
            schema=coreschema.Integer(
                description="assignment id should be given here(i.e. 18)"
            )
        )
    ])

    # permission = (Permission.objects.filter(codename='add_country'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'POST': group,
    #
    # }

    def post(self, request):
        requested_data = request.data
        try:
            assignment = Assignment.objects.get(id=requested_data['assignment_id'])
            quoted_logs_qs = assignment.price_quote_logs.filter(status=True)
            quoted_logs_ser = PriceQuoteLogSerializer(quoted_logs_qs, many=True)

            return Response(
                {
                    'status': status.HTTP_200_OK,
                    'message': 'History fetched',
                    'data': quoted_logs_ser.data
                }
            )
        except ObjectDoesNotExist:
            return Response(
                {
                    'status': status.HTTP_404_NOT_FOUND,
                    'message': 'requested assignment not found'
                }
            )


class NotifyStudentAPI(APIView):
    """
    post:
    REST API for notify user for his/her assignment
    """
    schema = schemas.ManualSchema(fields=[
        coreapi.Field(
            'assignment_id',
            required=True,
            schema=coreschema.Integer(
                description='Enter Assignment ID'
            )
        )
    ])

    # permission = (Permission.objects.filter(codename='add_country'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'POST': group,
    #
    # }

    def post(self, request):
        requested_data = request.data
        try:
            assignment = Assignment.objects.get(id=requested_data['assignment_id'])
        except ObjectDoesNotExist:
            return Response(
                {
                    'status': status.HTTP_404_NOT_FOUND,
                    'message': 'Assignment not found'
                }, status=status.HTTP_404_NOT_FOUND
            )
        # getting all device token of student
        devices = user_active_devices(assignment.student)

        title = 'Mentyor Notification for Assignment ' + assignment.assignment_number + '.'
        message = 'You have new message for assignment number ' + assignment.assignment_number + '. Please login for detail'

        # sending notification to user's device
        notification = send_notification(devices, title, message)
        # sending email to student email id
        email = send_user_notify_email.delay(title, message, assignment.student.email)  # have to activate in production
        # email = True # have remove in production

        if notification and email:
            return Response(
                {
                    'status': status.HTTP_200_OK,
                    'message': 'User Notification Sent.'
                }
            )
        else:
            return Response(
                {
                    'status': status.HTTP_500_INTERNAL_SERVER_ERROR,
                    'message': 'Something went wrong. Please try later'
                }
            )


class NotifyExpertAPI(APIView):
    """
    post:
    REST API for notify expert for his/her floated assignment
    """
    schema = schemas.ManualSchema(fields=[
        coreapi.Field(
            'assignment_id',
            required=True,
            schema=coreschema.Integer(
                description='Enter Assignment ID'
            )
        ),
        coreapi.Field(
            'expert_id',
            required=True,
            schema=coreschema.Integer(
                description='Enter Expert ID.'
            )
        )
    ])

    # permission = (Permission.objects.filter(codename='add_country'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'POST': group,
    #
    # }

    def post(self, request):
        requested_data = request.data
        try:
            assignment = Assignment.objects.get(id=requested_data['assignment_id'])
            expert = User.objects.get(id=requested_data['expert_id'])
        except ObjectDoesNotExist:
            return Response(
                {
                    'status': status.HTTP_404_NOT_FOUND,
                    'message': 'Assignment not found'
                }, status=status.HTTP_404_NOT_FOUND
            )
        # getting all device token of expert
        devices = user_active_devices(expert)

        title = 'Notification for Assignment ' + assignment.assignment_number + '.'
        message = 'You have new message for assignment number ' + assignment.assignment_number + '. Please login for detail'

        # sending notification to user's device
        notification = send_notification(devices, title, message)
        # sending email to student email id
        email = send_user_notify_email.delay(title, message, expert.email)  # have to activate in production
        # email = True  # have remove in production

        if notification and email:
            return Response(
                {
                    'status': status.HTTP_200_OK,
                    'message': 'Expert Notification Sent.'
                }
            )
        else:
            return Response(
                {
                    'status': status.HTTP_500_INTERNAL_SERVER_ERROR,
                    'message': 'Something went wrong. Please try later'
                }
            )


class ArchiveAssignment(APIView):

    # permission = (Permission.objects.filter(codename='add_country'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'POST': group,
    #
    # }

    def put(self, request, id):
        try:
            assignment = Assignment.objects.get(id=id)
        except ObjectDoesNotExist:
            return Response(
                {
                    'status': status.HTTP_404_NOT_FOUND,
                    'message': 'assignment not found'

                },
                status=status.HTTP_404_NOT_FOUND
            )
        if not assignment.is_archive:
            assignment.is_archive = True
        else:
            assignment.is_archive = False
        assignment.save()

        return Response(
            {
                'status': status.HTTP_200_OK,
                'message': 'Assignment Archived',
                'archive': assignment.is_archive
            },
            status=status.HTTP_200_OK
        )


class ArchiveAssignmentList(APIView):

    # permission = (Permission.objects.filter(codename='list_archive_assignment'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'POST': group,
    #
    # }

    def get(self, request):
        queryset = Assignment.objects.filter(is_archive=True)

        ordering = request.GET.get('ordering', None)
        search = request.GET.get('search', None)

        if search:
            queryset = queryset.filter(
                Q(assignment_number__icontains=search) | Q(student__name__icontains=search))

        if ordering:
            try:
                queryset = queryset.order_by(ordering)
            except Exception:
                return Response(
                    {
                        'status': status.HTTP_400_BAD_REQUEST,
                        'message': 'Invalid filter arguments'
                    }, status=status.HTTP_400_BAD_REQUEST
                )
        else:
            queryset = queryset.filter(status=True).order_by('-id')

        paginator = PageNumberPagination()
        result_page = paginator.paginate_queryset(queryset, request)

        serializer = AssignmentListSerializer(result_page, many=True)
        s_data = paginator.get_paginated_response(serializer.data)

        return Response(
            {
                'status': status.HTTP_200_OK,
                'message': 'Archive Assignment List fetched',
                'search_keys': 'assignment_number',
                'data': s_data.data
            },
            status=status.HTTP_200_OK
        )
        # serializer = AssignmentListSerializer(queryset, many=True)
        # return Response(
        #     {
        #         'status': status.HTTP_200_OK,
        #         'message': 'Archive assignment list fetched',
        #         'data': serializer.data
        #     },
        #     status=status.HTTP_200_OK
        # )


class ViewMobileEmail(APIView):
    """
    post:
    API for view mobile/email of student who posted particular assignment
    """
    schema = schemas.ManualSchema(fields=[
        coreapi.Field(
            "assignment_id",
            required=True,
            location="form",
            schema=coreschema.Integer(
                description="assignment id should be given here(i.e. 18)"
            )
        )

    ])

    # permission = (Permission.objects.filter(codename='add_country'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'POST': group,
    #
    # }

    def post(self, request):
        assignment_id = request.data['assignment_id']
        if not assignment_id:
            return Response(
                {
                    'status': status.HTTP_400_BAD_REQUEST,
                    'message': 'invalid assignment id'
                }, status=status.HTTP_400_BAD_REQUEST
            )
        assignment = get_object_or_404(Assignment, id=assignment_id)
        activity = save_user_activity(request, 'View Email/Mobile of student', assignment.assignment_number)
        # activity = UserActivityLog.objects.create(
        #                 user=request.user,
        #                 activity='View Email/Mobile of student',
        #                 activity_for=assignment.assignment_number
        #             )

        return Response(
            {
                'status': status.HTTP_200_OK,
                'message': 'detail fetched',
                'data': {
                            'student_email': assignment.student.get_email,
                            'student_mobile': assignment.student.get_mobile
                        }
            }, status=status.HTTP_200_OK
        )


class AssignmentPaymentHistory(APIView):
    """
    API for getting payment history of an assignment
    """
    # permission = (Permission.objects.filter(codename='add_country'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'POST': group,
    #
    # }

    schema = schemas.ManualSchema(fields=[
        coreapi.Field(
            "assignment_id",
            required=True,
            location="form",
            schema=coreschema.Integer(
                description="Send assignment id. Ex: 22"
            )
        ),

    ])

    def post(self, request):
        assignment_id = request.data['assignment_id']

        payment_history_qs = AssignmentTransaction.objects.filter(assignment_id=assignment_id)

        if payment_history_qs.count() > 0:
            serializer = AssignmentPaymentHistorySerializer(payment_history_qs, many=True)

            return Response(
                {
                    'status': status.HTTP_200_OK,
                    'message': 'Data fetched',
                    'data': serializer.data
                }
            )
        else:
            return Response(
                {
                    'status': status.HTTP_404_NOT_FOUND,
                    'message': 'Data not found'
                }, status=status.HTTP_404_NOT_FOUND
            )


class AssignmentMemoList(APIView):
    """
    get:
        API for getting list of memos of an assignment
    """
    # permission = (Permission.objects.filter(codename='list_memo'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'POST': group,
    #
    # }

    # TODO must have to remove comments for permissions before making it live

    def get_object(self, id):
        try:
            return get_object_or_404(Assignment, id=id)
        except AssignmentSolution.DoesNotExist:
            return Response(
                {
                    'status': status_code.HTTP_404_NOT_FOUND,
                    'message': 'Assignment not found'
                },
                status=status_code.HTTP_404_NOT_FOUND
            )

    def get(self, request, id):
        assignment_id = self.get_object(id)
        queryset = AssignmentMemos.objects.filter(status=True, assignment=assignment_id)
        if queryset.count() > 0:
            serializer = AssignmentMemoListSerializer(queryset, many=True)

            return Response(
                {
                    'status': status.HTTP_200_OK,
                    'message': 'Data fetched',
                    'data': serializer.data
                }
            )
        else:
            return Response(
                {
                    'status': status.HTTP_200_OK,
                    'message': 'No data found for this assignment',
                    'data': []
                }
            )


class AssignmentMemoCreate(APIView):
    """
    post:
        API for create a memo for an assignment
    """
    permission = (Permission.objects.filter(codename='add_memo'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'POST': group,

    }

    schema = schemas.ManualSchema(fields=[
        coreapi.Field(
            "assignment_id",
            required=True,
            location="form",
            schema=coreschema.Integer(
                description="Send assignment id. Ex: 22"
            )
        ),
        coreapi.Field(
            "message",
            required=True,
            location="form",
            schema=coreschema.String(
                description="Send message"
            )
        ),

    ])

    def post(self, request):
        assignment_id = request.data.get('assignment_id', None)
        message = request.data.get('message', None)
        if not message:
            return Response(
                {
                    'status': status.HTTP_400_BAD_REQUEST,
                    'message': 'Please put some message for memo'
                }, status=status.HTTP_400_BAD_REQUEST
            )

        assignment = get_object_or_404(Assignment, id=assignment_id)
        created_memo = AssignmentMemos.objects.create(
            assignment=assignment,
            assignment_number = assignment.assignment_number,
            message=message,
            created_by=request.user
        )
        if created_memo:
            return Response(
                {
                    'status': status.HTTP_201_CREATED,
                    'message': 'Memo created',
                    'data': {'memo_id': created_memo.id}
                }, status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {
                    'status': status.HTTP_500_INTERNAL_SERVER_ERROR,
                    'message': 'Something went wrong. Contact to admin.'
                }
            )

