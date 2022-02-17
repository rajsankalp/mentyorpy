from apps.users.models import User, UserProfile, ExpertBankAccount, MentyorWallet, UserWalletLog, LoginLog
from apps.common.models import PushNotification
from apps.assignment.models import Assignment
from api.v1.admin_serializers.users_serializers import UserListSerializer, UserDetailsSerializer, \
    ExpertBankAccountSerializer, ExpertBankAccountDetailSerializer
from api.v1.admin_serializers.assignment import AssignmentListSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound
from django.utils import timezone
from libraries.permission import HasGroupPermission
from django.contrib.auth.models import Permission, Group
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
import coreschema, coreapi
from rest_framework import schemas
from django.core.exceptions import ObjectDoesNotExist
from cryptography.fernet import Fernet
import base64
from libraries.Functions import encrypt_data
from apps.users.helper import user_active_devices
from libraries.PushNotification import send_notification
from libraries.Email_model import offer_reward_email
import json
from django.db import transaction


class UserListApi(APIView):
    """
    get:
        http://192.168.1.14:8002/api/v1/admin/user/list?page=1&ordering=-name&search=sonu
    """

    # permission = (Permission.objects.filter(codename='list_user'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'GET': group,
    #     'PUT': group,
    #     'POST': group
    #
    # }

    def get(self, request, format=None):
        ordering = request.GET.get('ordering', None)
        search = request.GET.get('search', None)

        queryset = User.objects.filter(is_superuser=False, groups__name='user')
        model = ((apps.get_models()[25].__name__))
        all_perms_on_this_modal = Permission.objects.filter(codename__contains=model.lower())
        # print(all_perms_on_this_modal)
        all_permissions = Permission.objects.filter(content_type__model=model)
        # print(model.lower())
        c=(ContentType.objects.all())
        print(c[0])

        # if search value is available
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) | Q(mobile__icontains=search) | Q(name__icontains=search))

        # if need ordering
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

        serializer = UserListSerializer(result_page, many=True)
        s_data = paginator.get_paginated_response(serializer.data)

        return Response(
            {
                'status': status.HTTP_200_OK,
                'message': 'data fetched',
                'search_keys': 'email, mobile, name',
                'data': s_data.data
            }, status=status.HTTP_200_OK
        )


class UserDetailApi(APIView):
    """
       get:
           Return a Detail of User
       """

    permission = (Permission.objects.filter(codename='view_user'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'GET': group,
        'PUT': group,
        'POST': group

    }

    def get_object(self, id):
        try:
            return User.objects.get(id=id, groups__name='user')
        except User.DoesNotExist:

            raise NotFound(detail="Error 404 ,user id not found", code=404)

    def get(self, request, id):
        try:
            user_obj = self.get_object(id)

            serializer = UserDetailsSerializer(user_obj)

            return Response({
                'status': status.HTTP_200_OK,
                'message': 'user detail fetched',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except AttributeError:

            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'user detail not found',
            }, status=status.HTTP_404_NOT_FOUND)


class UserIsDeleteApi(APIView):
    """
    put:
        Delete a user set is_active=False where is_active=True
    """
    permission = (Permission.objects.filter(codename='delete_user'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'GET': group,
        'PUT': group,
        'POST': group

    }

    def get_object(self, id):
        try:
            return User.objects.get(id=id)
        except User.DoesNotExist:

            raise NotFound(detail="Error 404 ,user not found", code=404)

    def put(self, request, id):
        try:
            user_obj = self.get_object(id)
            if user_obj.is_active:
                user_obj.is_active = False
            else:
                user_obj.is_active = True
            user_obj.updated_on = timezone.now()

            user_obj.save()

            return Response({
                'status': status.HTTP_200_OK,
                'message': 'user detail Deleted successfully',
                'is_active': user_obj.is_active
            }, status=status.HTTP_200_OK)
        except AttributeError:

            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'user detail not found',
            })


class UserAssignmentView(APIView):

    """ API For assignmnet list corresponding to the user
    """

    def get(self, request, id):
        queryset = Assignment.objects.filter(student_id=id)
        serializer = AssignmentListSerializer(queryset, many=True)
        return Response(
            {
                'message': 'Assignment list corresponding user fetched',
                'status': status.HTTP_200_OK,
                'data': serializer.data
            },
            status=status.HTTP_200_OK
        )


class ExpertBankAccountCreate(APIView):
    """
    post:
    API for add bank account of expert
    """
    permission = (Permission.objects.filter(codename='add_expert_bank_account'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'GET': group,
        'PUT': group,
        'POST': group

    }

    schema = schemas.ManualSchema(fields=[
        coreapi.Field(
            "expert_id",
            required=True,
            location="form",
            schema=coreschema.Integer(
                description="User ID for expert"
            )
        ),

        coreapi.Field(
            "full_name",
            required=True,
            location="form",
            schema=coreschema.String(
                description="Enter full name for bank acount"
            )
        ),
        coreapi.Field(
            "bank_name",
            required=True,
            location="form",
            schema=coreschema.String(
                description="Enter bank name"
            )
        ),
        coreapi.Field(
            "account_number",
            required=True,
            location="form",
            schema=coreschema.Integer(
                description="Enter account number"
            )
        ),
        coreapi.Field(
            "ifsc_code",
            required=True,
            location="form",
            schema=coreschema.String(
                description="Enter IFSC code"
            )
        ),
        coreapi.Field(
            "bank_location",
            required=True,
            location="form",
            schema=coreschema.String(
                description="Enter bank location"
            )

        ),

        coreapi.Field(
            "account_type",
            required=True,
            location="form",
            schema=coreschema.String(
                description="Bank Location. Ex: saving/current"
            )
        ),
        coreapi.Field(
            "country",
            required=False,
            location="form",
            schema=coreschema.String(
                description="Enter country of bank"
            )
        )
    ]
    )

    def post(self, request, format=None):
        """
            Post Api for profile upadate of expert by admin
            """
        try:
            expert = User.objects.get(id=request.data['expert_id'], is_staff=True, groups__name='expert')
        except ObjectDoesNotExist:
            return Response(
                {
                    'status': status.HTTP_400_BAD_REQUEST,
                    'message': 'Expert not found with this expert id'
                }
            )
        serializer = ExpertBankAccountSerializer(data=request.data)
        if serializer.is_valid():
            serializer.validated_data['account_number'] = encrypt_data(serializer.validated_data['account_number'])
            serializer.validated_data['user'] = expert
            serializer.validated_data['created_by'] = request.user
            serializer.validated_data['updated_by'] = request.user
            serializer.validated_data['created_on'] = timezone.now()
            serializer.validated_data['updated_on'] = timezone.now()

            obj, created = ExpertBankAccount.objects.update_or_create(
                user=expert,
                defaults=serializer.validated_data,
            )

            if created:
                return Response(
                    {
                        'status': status.HTTP_201_CREATED,
                        'message': 'Expert bank account added successfully.'

                    },
                    status=status.HTTP_201_CREATED
                )
            else:
                return Response(
                    {
                        'status': status.HTTP_201_CREATED,
                        'message': 'Expert bank account updated successfully.'

                    },
                    status=status.HTTP_201_CREATED
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExpertBankAccountDetail(APIView):
    """
    post:
    API for detail of bank account of expert
    """
    # permission = (Permission.objects.filter(codename='view_expert_bank_account'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'GET': group,
    #     'PUT': group,
    #     'POST': group
    #
    # }

    schema = schemas.ManualSchema(fields=[
        coreapi.Field(
            "expert_id",
            required=True,
            location="form",
            schema=coreschema.Integer(
                description="User ID for expert"
            )
        )
    ]
    )

    def post(self, request, format=None):
        """
            Post Api for get detail of expert's bank account
            """
        try:
            expert = User.objects.get(id=request.data['expert_id'], is_staff=True, groups__name='expert')
        except ObjectDoesNotExist:
            return Response(
                {
                    'status': status.HTTP_400_BAD_REQUEST,
                    'message': 'Expert not found with this expert id'
                }
            )
        queryset = ExpertBankAccount.objects.filter(user=expert)

        if queryset.exists():
            serializer = ExpertBankAccountDetailSerializer(queryset[0])
            return Response(
                {
                    'status': status.HTTP_200_OK,
                    'message': 'Detail fetched.',
                    'data': serializer.data

                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {
                    'status': status.HTTP_404_NOT_FOUND,
                    'message': 'Expert bank account detail not found.'

                },
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OfferRewardAPI(APIView):
    """
        post:
        API for add offer reward to users
        """
    permission = (Permission.objects.filter(codename='add_mentyor_wallet'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'GET': group,
        'PUT': group,
        'POST': group

    }

    schema = schemas.ManualSchema(fields=[
        coreapi.Field(
            "user_ids",
            required=True,
            location="form",
            schema=coreschema.String(
                description="Enter multiple or single user_id here. Ex: [10,15,18]"
            )
        ),
        coreapi.Field(
            "amount",
            required=True,
            location="form",
            schema=coreschema.Number(
                description="Enter amount"
            )
        ),
        coreapi.Field(
            "currency",
            required=True,
            location="form",
            schema=coreschema.Number(
                description="Enter currency"
            )
        ),
        coreapi.Field(
            "reward_for",
            required=True,
            location="form",
            schema=coreschema.String(
                description="Enter occasion of reward"
            )
        )
    ]
    )

    def post(self, request):
        requested_data = request.data
        user_ids = requested_data.get('user_ids', None)
        amount = requested_data.get('amount', None)
        currency = requested_data.get('currency', None)
        reward_for = requested_data.get('reward_for', None)

        if user_ids and amount and currency and reward_for:
            user_ids = json.loads(user_ids)
            for user_id in user_ids:
                print(user_id)
                # getting user instance
                user = User.objects.get(id=user_id)
                # getting user wallet instance
                user_wallet = MentyorWallet.objects.get(user=user, wallet_currency=currency)
                user_wallet.wallet_amount = float(user_wallet.wallet_amount) + float(amount)
                user_wallet.updated_on = timezone.now()
                user_wallet.save()

                # creating user wallet log
                user_wallet_log = UserWalletLog()
                user_wallet_log.user = user
                user_wallet_log.amount = amount
                user_wallet_log.currency = currency
                user_wallet_log.is_credited = True
                user_wallet_log.created_by = request.user
                user_wallet_log.updated_by = request.user
                user_wallet_log.created_on = timezone.now()
                user_wallet_log.wallet_log_type = 'Offer Reward'
                user_wallet_log.wallet_log_for = reward_for
                with transaction.atomic():
                    user_wallet.save()
                    user_wallet_log.save()

                # getting user login logs
                active_devices = user_active_devices(user)
                title = 'Mentoyr Offer Reward'
                message = 'Congratulations..! You have rewarded with '+currency+''+amount+' for '+reward_for+'.'
                # sending notification
                send_notification(active_devices, title, message)
                # sending email
                offer_reward_email.delay(title, message, user.email)

            return Response(
                {
                    'status': status.HTTP_201_CREATED,
                    'message': 'Reward updated to all selected users.'
                }, status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {
                    'status': status.HTTP_400_BAD_REQUEST,
                    'message': 'All fields are required'
                }, status=status.HTTP_400_BAD_REQUEST
            )


class CurrencyWiseUserList(APIView):
    """
    get:
        http://192.168.1.14:8002/api/v1/admin/currencyWiseUsers/?currency=INR&page=1&ordering=-name&search=sonu
    """

    # permission = (Permission.objects.filter(codename='list_user'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'GET': group,
    #     'PUT': group,
    #     'POST': group
    #
    # }

    def get(self, request, format=None):
        currency = request.GET.get('currency', None)
        ordering = request.GET.get('ordering', None)
        search = request.GET.get('search', None)

        if not currency:
            return Response(
                {
                    'status': status.HTTP_400_BAD_REQUEST,
                    'message': 'Please mention currency of users.'
                }
            )

        queryset = User.objects.filter(is_superuser=False, groups__name='user', mentyorwallet__wallet_currency=currency)

        # if search value is available
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search) | Q(mobile__icontains=search) | Q(name__icontains=search))

        # if need ordering
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

        serializer = UserListSerializer(result_page, many=True)
        s_data = paginator.get_paginated_response(serializer.data)

        return Response(
            {
                'status': status.HTTP_200_OK,
                'message': 'data fetched',
                'search_keys': 'email, mobile, name',
                'data': s_data.data
            }, status=status.HTTP_200_OK
        )


