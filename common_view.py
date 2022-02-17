from api.v1.admin_serializers.common_serializers import FaqDetailSerializer, TestimonialPostSerializer, \
    FaqListSerializer, TestimonialListSerializer, TestimonialDetailSerializer, EnquiryListSerializer, \
    EnquiryDetailSerializer, CareerListSerializer, CareerDetailSerializer, ReportAdminLisSerializer, \
    ReviewListSerializer, ReviewDetailSerializer, NotificationSerializer
from apps.common.models import Faq, Testimonial, Enquiry, Career, ReportAdmin, Review, PushNotification
from apps.common.models import Review
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
import coreapi
import coreschema
from rest_framework import schemas
from django.utils import timezone
import random
from libraries.Functions import file_upload_handler, make_dir
from django.conf import settings
from rest_framework.exceptions import NotFound
from libraries.helper import permission_to_user
from libraries.permission import HasGroupPermission
from django.contrib.auth.models import Permission, Group
from apps.users.models import LoginLog
import json
from libraries.PushNotification import send_notification
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from rest_framework.pagination import PageNumberPagination


class FaqCreateApi(APIView):
    """
    post:
        post List of All FAQs.
    """

    # Parameter description for API documentation starts here
    schema = schemas.ManualSchema(fields=[
        coreapi.Field(
            "question",
            required=False,
            location="form",
            schema=coreschema.String(
                description="Enter question here"
            )
        ),

        coreapi.Field(
            "brief_answer",
            required=True,
            location="form",
            schema=coreschema.String(
                description="Brief answer here"
            )
        ),
        coreapi.Field(
            "answer",
            required=True,
            location="form",
            schema=coreschema.String(
                description="Answer"
            )
        ),
        coreapi.Field(
            "id",
            required=False,
            location="form",
            schema=coreschema.String(
                description="Enter id to update the faq else leave blank to create"
            )
        ),
    ])

    # Parameter description for API documentation ends here

    """
    permission:
    permission is being handled according to group permission of logged in user
    # """

    # permission_name = 'add_faq'

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.permission_name = 'add_faq'
    # permission = (Permission.objects.filter(codename='add_faq'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'POST': group,
    # }

    # permission_classes = permission_to_user('add_faq')

    def post(self, request, format=None):
        serializer = FaqDetailSerializer(data=request.data)

        if serializer.is_valid():
            serializer.validated_data['updated_on'] = timezone.now()
            if 'id' not in request.data:
                serializer.validated_data['created_on'] = timezone.now()
                serializer.validated_data['created_by'] = request.user
                serializer.validated_data['updated_by'] = request.user
                if request.data['question']:
                    faq = Faq.objects.create(**serializer.validated_data)
                else:
                    return Response(
                        {
                            'status': status.HTTP_400_BAD_REQUEST,
                            'message': 'please fill the require fields',

                        }, status=status.HTTP_400_BAD_REQUEST
                    )

                return Response(
                    {
                        'status': status.HTTP_201_CREATED,
                        'message': 'Faq data saved successfully.',
                        'data': {'faq_id': faq.id}
                    }, status=status.HTTP_201_CREATED)
            else:
                try:
                    faq = Faq.objects.filter(id=request.data['id'])
                except ObjectDoesNotExist:
                    return Response(
                        {
                            'status': status.HTTP_404_NOT_FOUND,
                            'message': 'faq not found'
                        },
                        status=status.HTTP_404_NOT_FOUND
                    )
                serializer.validated_data['updated_by'] = request.user
                faq.update(**serializer.validated_data)
                return Response(
                    {
                        'status': status.HTTP_200_OK,
                        'message': 'Faq data updated.',
                        'data': {'id': request.data['id']}
                    }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreateTestimonialApi(APIView):
    # permission = (Permission.objects.filter(codename='add_testimonial'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'POST': group,
    # }
    schema = schemas.ManualSchema(fields=[
        coreapi.Field(
            "name",
            required=True,
            location="form",
            schema=coreschema.String(
                description="Enter question here"
            )
        ),
        coreapi.Field(
            "image",
            required=False,
            location="form",
            schema=coreschema.String(
                description="Enter question here"
            )
        ),
        coreapi.Field(
            "message",
            required=True,
            location="form",
            schema=coreschema.String(
                description=""
            )
        ),
        coreapi.Field(
            "id",
            required=False,
            location="form",
            schema=coreschema.Integer(
                description="enter id to update else leave blank to create new testimonials "
            )
        )
    ])

    schema = schemas.ManualSchema(fields=[
        coreapi.Field(

            'name',
            required=True,
            location="form",
            schema=coreschema.String(
                description=""
            )
        ),
        coreapi.Field(

            'message',
            required=True,
            location="form",
            schema=coreschema.String(
                description=""
            )
        ),
    ])

    def post(self, request, formate=None):
        testimonial_serializer = TestimonialPostSerializer(data=request.data)

        testimonial_data = request.data
        testimonial_image = ''

        if testimonial_serializer.is_valid():
            if 'image' in testimonial_data:
                rndm = random.randint(100000, 9999999)

                file_name = testimonial_data['image']
                upload_dir = make_dir(
                    settings.MEDIA_ROOT + settings.CUSTOM_DIRS.get('TESTIMONIAL_DIR') + '/' + str(rndm) + '/'
                )
                try:
                    file_name = file_upload_handler(file_name, upload_dir)
                except ValueError:
                    print('*******EXCEPTION**********')
                    print(ValueError)
                    return Response(
                        {
                            'status':status.HTTP_400_BAD_REQUEST,
                            'message': str(ValueError)
                        }, status=status.HTTP_400_BAD_REQUEST
                    )

                testimonial_image = settings.MEDIA_URL + settings.CUSTOM_DIRS.get('TESTIMONIAL_DIR') + '/' + str(
                    rndm) + '/' + file_name

                testimonial_serializer.validated_data['image'] = testimonial_image

            testimonial_serializer.validated_data['updated_on'] = timezone.now()
            testimonial_serializer.validated_data['updated_by'] = request.user
            testimonial_serializer.validated_data['status'] = True

            if 'id' not in request.data:
                testimonial_serializer.validated_data['created_on'] = timezone.now()
                testimonial_serializer.validated_data['created_by'] = request.user
                testimonial = Testimonial.objects.create(**testimonial_serializer.validated_data)
                return Response({
                    'status': status.HTTP_201_CREATED,
                    'message': 'your testimonial has been submitted successfully',
                    'data': {'testimonial_id': testimonial.id}
                }, status=status.HTTP_201_CREATED)
            else:
                try:
                    testimonial = Testimonial.objects.filter(id=request.data['id'])
                except ObjectDoesNotExist:
                    return Response(
                        {
                            'status': status.HTTP_404_NOT_FOUND,
                            'message': 'testimonial not found',

                        },
                        status=status.HTTP_404_NOT_FOUND
                    )
                testimonial.update(**testimonial_serializer.validated_data)

                return Response({
                    'status': status.HTTP_201_CREATED,
                    'message': 'your testimonial has been updated successfully',
                    'data': {'testimonial_id': request.data['id']}
                }, status=status.HTTP_201_CREATED)

        return Response(testimonial_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FaqsListApi(APIView):
    """
    get
    Return a list of all faq

    http://192.168.1.14:8002/api/v1/admin/faq/list?page=1&ordering=-id&search=question

    """

    # permission = (Permission.objects.filter(codename='list_faq'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'GET': group,
    # }

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.permission_name = 'add_faq'

    def get(self, request):
        queryset = Faq.objects.filter(status=True).order_by('id')

        ordering = request.GET.get('ordering', None)
        search = request.GET.get('search', None)

        if search:
            queryset = queryset.filter(
                Q(question__icontains=search) | Q(answer__icontains=search))

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

        serializer = FaqListSerializer(result_page, many=True)
        s_data = paginator.get_paginated_response(serializer.data)

        return Response(
            {
                'status': status.HTTP_200_OK,
                'message': 'faq List fetched',
                'data': s_data.data,
                'search_on': {'question', 'answer'}
            },
            status=status.HTTP_200_OK
        )


class FaqDetailApi(APIView):
    """
     Get a detail of Faq detail
     """

    # permission = (Permission.objects.filter(codename='view_enquiry'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'GET': group,
    #
    # }

    def get_object(self, id):

        try:
            return Faq.objects.get(id=id, status=True)
        except Faq.DoesNotExist:
            raise NotFound(detail="Error 404 ,faq id not found", code=404)

    def get(self, request, id):

        try:

            faq_obj = self.get_object(id)
            serializer = FaqDetailSerializer(faq_obj)

            return Response({

                'status': status.HTTP_200_OK,
                'message': 'Faq Detail fetched',
                'data': serializer.data,
            })
        except AttributeError:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Faq not found ',
            }, status=status.HTTP_404_NOT_FOUND)


class FaqIsBlockApi(APIView):
    """
      Put:
    Update faq set is_blocked=True where status=True

    # """

    # permission = (Permission.objects.filter(codename='delete_faq'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'GET': group,
    #     'PUT':group
    # }

    def get_object(self, id):

        try:
            return Faq.objects.get(id=id, status=True)
        except Faq.DoesNotExist:
            raise NotFound(detail="Error 404 ,faq id not found", code=404)

    def put(self, request, id):

        try:
            faq_obj = self.get_object(id)
            if faq_obj.is_block:
                faq_obj.is_block = False
            else:
                faq_obj.is_block = True
            faq_obj.updated_on = timezone.now()

            faq_obj.save()

            return Response({
                'status': status.HTTP_201_CREATED,
                'message': 'Faq updated successfully',
                'is_block': faq_obj.is_block
            })
        except AttributeError:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Faq not found ',
            }, status=status.HTTP_404_NOT_FOUND)


class FaqDeleteApi(APIView):
    """
     Put:
         Delete faq set status=False where status=True

    """

    # permission = (Permission.objects.filter(codename='delete_faq'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'GET': group,
    #     'PUT': group
    # }

    def get_object(self, id):

        try:
            return Faq.objects.get(id=id, status=True)
        except Faq.DoesNotExist:
            raise NotFound(detail="Error 404 ,faq id not found", code=404)

    def put(self, request, id):

        try:
            faq_obj = self.get_object(id)
            faq_obj.status = False
            faq_obj.updated_on = timezone.now()

            faq_obj.save()

            return Response({
                'status': status.HTTP_201_CREATED,
                'message': 'Faq Delete successfully',
            })
        except AttributeError:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Faq not found ',
            }, status=status.HTTP_404_NOT_FOUND)


class TestimonialListApi(APIView):
    """
    Get a list of all testimonial

    http://192.168.1.14:8002/api/v1/admin/testimonial/list?page=1&ordering=-name&search=name

    # """

    # permission = (Permission.objects.filter(codename='list_testimonial'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'GET': group,
    # }

    def get(self, request):
        queryset = Testimonial.objects.filter(status=True).order_by('-id')

        serializer = TestimonialListSerializer(queryset, many=True)

        return Response(
            {
                'status': status.HTTP_200_OK,
                'message': 'testimonial List fetched',
                'data': serializer.data
            },
            status=status.HTTP_200_OK
        )


class TestimonialDetailApi(APIView):
    """
    Get a detail of testimonial
    """

    # permission = (Permission.objects.filter(codename='view_testimonial'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'GET': group,
    # }

    def get_object(self, id):

        try:
            return Testimonial.objects.get(id=id)
        except Testimonial.DoesNotExist:
            raise NotFound(detail="Error 404 ,testimonial id not found", code=404)

    def get(self, request, id):

        try:

            testimonial_obj = self.get_object(id)
            serializer = TestimonialDetailSerializer(testimonial_obj)

            return Response({
                'status': status.HTTP_200_OK,
                'message': 'Testimonial Detail fetched',
                'data': serializer.data,
            })
        except AttributeError:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Testimonial not found ',
            }, status=status.HTTP_404_NOT_FOUND)


class TestimonialIsBlockApi(APIView):
    """
      Put:
    Update testimonial set is_blocked=True where status=True

    """

    # permission = (Permission.objects.filter(codename='edit_testimonial'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'GET': group,
    #     'PUT': group
    # }

    def get_object(self, id):

        try:
            return Testimonial.objects.get(id=id)
        except Testimonial.DoesNotExist:
            raise NotFound(detail="Error 404 ,testimonial id not found", code=404)

    def put(self, request, id):

        try:

            testimonial_obj = self.get_object(id)
            if testimonial_obj.is_blocked:
                testimonial_obj.is_blocked = False
            else:
                testimonial_obj.is_blocked = True
            testimonial_obj.updated_on = timezone.now()
            testimonial_obj.save()

            return Response({
                'status': status.HTTP_201_CREATED,
                'message': 'Testimonial updated successfully',
                'is_block': testimonial_obj.is_blocked,
            })
        except AttributeError:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Testimonial not found ',
            }, status=status.HTTP_404_NOT_FOUND)


class TestimonialDeleteApi(APIView):
    """
          Put:
         Delete testimonial set status=False where status=True

        """

    # permission = (Permission.objects.filter(codename='delete_testimonial'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'GET': group,
    #     'PUT':group
    # }

    def get_object(self, id):

        try:
            return Testimonial.objects.get(id=id, status=True)
        except Testimonial.DoesNotExist:
            raise NotFound(detail="Error 404 ,testimonial id not found", code=404)

    def put(self, request, id):

        try:

            testimonial_obj = self.get_object(id)
            testimonial_obj.status = False

            testimonial_obj.save()

            return Response({
                'status': status.HTTP_201_CREATED,
                'message': 'Testimonial Delete successfully',
            })
        except AttributeError:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Testimonial not found ',
            }, status=status.HTTP_404_NOT_FOUND)


class EnquiryListApi(APIView):
    """
    Get
    a list of all Enquiry

    http://192.168.1.14:8002/api/v1/admin/enquiry/list?page=1&ordering=-name&search=sonu
    """

    # permission = (Permission.objects.filter(codename='list_enquiry'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'GET': group,
    #
    # }

    def get(self, request):
        queryset = Enquiry.objects.filter(status=True)
        # ordering = request.GET.get('ordering', None)
        # search = request.GET.get('search', None)
        #
        # if search:
        #     queryset = queryset.filter(
        #         Q(mobile__icontains=search) | Q(email__icontains=search) | Q(name__icontains=search))
        #
        # if ordering:
        #     try:
        #         queryset = queryset.order_by(ordering)
        #     except Exception:
        #         return Response(
        #             {
        #                 'status': status.HTTP_400_BAD_REQUEST,
        #                 'message': 'Invalid filter arguments'
        #             }, status=status.HTTP_400_BAD_REQUEST
        #         )
        # else:
        #     queryset = queryset.filter(status=True).order_by('-id')
        #
        # paginator = PageNumberPagination()
        # result_page = paginator.paginate_queryset(queryset, request)

        serializer = EnquiryListSerializer(queryset, many=True)
        # s_data = paginator.get_paginated_response(serializer.data)

        return Response(
            {
                'status': status.HTTP_200_OK,
                'message': 'enquiry List fetched',
                'data': serializer.data
            },
            status=status.HTTP_200_OK
        )


class EnquiryDetailApi(APIView):
    """
     Get a detail of Enquiry
     """

    # permission = (Permission.objects.filter(codename='view_enquiry'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'GET': group,
    #
    # }

    def get_object(self, id):

        try:
            return Enquiry.objects.get(id=id)
        except Enquiry.DoesNotExist:
            raise NotFound(detail="Error 404 ,enquiry id not found", code=404)

    def get(self, request, id):

        try:

            enquiry_obj = self.get_object(id)
            serializer = EnquiryDetailSerializer(enquiry_obj)

            return Response({

                'status': status.HTTP_200_OK,
                'message': 'Enquiry Detail fetched',
                'data': serializer.data,
            })
        except AttributeError:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Enquiry not found ',
            }, status=status.HTTP_404_NOT_FOUND)


class EnquiryIsBlockApi(APIView):
    """
      Put:
        Update Enquiry set is_blocked=True where status=True

    """

    # permission = (Permission.objects.filter(codename='edit_enquiry'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'GET': group,
    #     'PUT':group
    #
    # }

    def get_object(self, id):

        try:
            return Enquiry.objects.get(id=id, status=True)
        except Enquiry.DoesNotExist:
            raise NotFound(detail="Error 404, Enquiry id not found", code=404)

    def put(self, request, id):

        try:
            enquiry_obj = self.get_object(id)
            if not enquiry_obj.is_blocked:
                enquiry_obj.is_blocked = True
            else:
                enquiry_obj.is_blocked = False
            enquiry_obj.updated_on = timezone.now()
            enquiry_obj.save()

            return Response({

                'status': status.HTTP_201_CREATED,
                'message': 'Enquiry updated successfully',
                'is_blocked': enquiry_obj.is_blocked,
            })
        except AttributeError:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Enquiry not found ',
            }, status=status.HTTP_404_NOT_FOUND)


class EnquiryDeleteApi(APIView):
    """
          Put:
         Delete Enquiry set status=False where status=True

        """

    # permission = (Permission.objects.filter(codename='delete_enquiry'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'GET': group,
    #     'PUT': group
    #
    # }

    def get_object(self, id):

        try:
            return Enquiry.objects.get(id=id, status=True)
        except Enquiry.DoesNotExist:
            raise NotFound(detail="Error 404, enquiry id not found", code=404)

    def put(self, request, id):

        try:
            enquiry_obj = self.get_object(id)

            enquiry_obj.status = False
            enquiry_obj.updated_on = timezone.now()

            enquiry_obj.save()

            return Response({
                'status': status.HTTP_201_CREATED,
                'message': 'Enquiry delete successfully',
            })
        except AttributeError:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Enquiry not found ',
            }, status=status.HTTP_404_NOT_FOUND)


class CareerListApi(APIView):
    """
    Get:
        a list of all Career

        http://192.168.1.14:8002/api/v1/admin/career/list?page=1&ordering=-name&search=sonu

    """

    # permission = (Permission.objects.filter(codename='list_career'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'GET': group,
    #     'PUT': group
    #
    # }

    def get(self, request):
        queryset = Career.objects.filter(status=True)
        ordering = request.GET.get('ordering', None)
        search = request.GET.get('search', None)

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(subject__icontains=search) | Q(topic__icontains=search))

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

        serializer = CareerListSerializer(result_page, many=True)
        s_data = paginator.get_paginated_response(serializer.data)

        return Response(
            {
                'status': status.HTTP_200_OK,
                'message': 'career List fetched',
                'search_keys': 'name, subject, topic',
                'data': s_data.data
            },
            status=status.HTTP_200_OK
        )


class CareerDetailApi(APIView):
    """
     Get a detail of Career
     """

    # permission = (Permission.objects.filter(codename='view_career'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'GET': group,
    #     'PUT': group
    #
    # }

    def get_object(self, id):

        try:
            return Career.objects.get(id=id)
        except Career.DoesNotExist:
            raise NotFound(detail="Error 404, career id not found", code=404)

    def get(self, request, id):

        try:
            career_obj = self.get_object(id)
            serializer = CareerDetailSerializer(career_obj)

            return Response({
                'status': status.HTTP_200_OK,
                'message': 'Career Detail fetched',
                'data': serializer.data,

            })

        except AttributeError:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Career not found ',
            }, status=status.HTTP_404_NOT_FOUND)


class CareerIsBlockApi(APIView):
    """
      Put:
        Update Career set is_blocked=True where status=True

    """

    # permission = (Permission.objects.filter(codename='edit_career'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'GET': group,
    #     'PUT': group
    #
    # }

    def get_object(self, id):

        try:
            return Career.objects.get(id=id, status=True)
        except Career.DoesNotExist:
            raise NotFound(detail="Error 404, career id not found", code=404)

    def put(self, request, id):

        try:

            career_obj = self.get_object(id)
            if not career_obj:
                career_obj.is_block = True
            else:
                career_obj.is_block = False
            career_obj.updated_on = timezone.now()
            career_obj.save()

            return Response({
                'status': status.HTTP_201_CREATED,
                'message': 'Career updated successfully',
                'is_block': career_obj.is_block,
            })
        except AttributeError:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Career not found ',
            }, status=status.HTTP_404_NOT_FOUND)


class CareerDeleteApi(APIView):
    """
          Put:
         Delete Career set status=False where status=True

        """

    # permission = (Permission.objects.filter(codename='delete_career'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'GET': group,
    #     'PUT': group
    #
    # }

    def get_object(self, id):

        try:
            return Career.objects.get(id=id, status=True)
        except Career.DoesNotExist:
            raise NotFound(detail="Error 404, career id not found", code=404)

    def put(self, request, id):

        try:
            career_obj = self.get_object(id)

            career_obj.status = False
            career_obj.updated_on = timezone.now()

            career_obj.save()

            return Response({
                'status': status.HTTP_201_CREATED,
                'message': 'Career delete successfully',
            })
        except AttributeError:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Career not found ',
            }, status=status.HTTP_404_NOT_FOUND)


class ReportAdminListApi(APIView):
    """
    Get:
        a list of all Report_Admin

        http://192.168.1.14:8002/api/v1/admin/reportAdmin/list?page=1&ordering=-name&search=sonu

    """
    permission = (Permission.objects.filter(codename='add_report_admin'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'GET': group,
        'PUT': group

    }

    def get(self, request):
        queryset = ReportAdmin.objects.filter(status=True)
        ordering = request.GET.get('ordering', None)
        search = request.GET.get('search', None)

        if search:
            queryset = queryset.filter(
                Q(assignment_no__icontains=search) | Q(title__icontains=search))

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

        serializer = ReportAdminLisSerializer(result_page, many=True)
        s_data = paginator.get_paginated_response(serializer.data)

        return Response(
            {
                'status': status.HTTP_200_OK,
                'message': 'career List fetched',
                'data': s_data.data
            },
            status=status.HTTP_200_OK
        )


class ReportAdminIsBlockApi(APIView):
    permission = (Permission.objects.filter(codename='delete_report_admin'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'GET': group,
        'PUT': group

    }

    """
      Put:
        Update ReportAdmin set is_blocked=True where status=True

    """

    def get_object(self, id):

        try:
            return ReportAdmin.objects.get(id=id, status=True)
        except ReportAdmin.DoesNotExist:
            raise NotFound(detail="Error 404, ReportAdmin id not found", code=404)

    def put(self, request, id):

        try:
            report_obj = self.get_object(id)
            if not report_obj.is_block:
                report_obj.is_block = True
            else:
                report_obj.is_block = False
            report_obj.updated_on = timezone.now()
            report_obj.save()

            return Response({

                'status': status.HTTP_201_CREATED,
                'message': 'ReportAdmin updated successfully',
            })
        except AttributeError:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'ReportAdmin not found ',
            }, status=status.HTTP_404_NOT_FOUND)


class ReportAdminDeleteApi(APIView):
    """
          Put:
         Delete ReportAdmin set status=False where status=True

        """
    permission = (Permission.objects.filter(codename='delete_report_admin'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'GET': group,
        'PUT': group

    }

    def get_object(self, id):

        try:
            return ReportAdmin.objects.get(id=id, status=True)
        except ReportAdmin.DoesNotExist:
            raise NotFound(detail="Error 404, ReportAdmin id not found", code=404)

    def put(self, request, id):

        try:
            report_obj = self.get_object(id)

            report_obj.status = False
            report_obj.updated_on = timezone.now()

            report_obj.save()

            return Response({
                'status': status.HTTP_201_CREATED,
                'message': 'ReportAdmin delete successfully',
            })
        except AttributeError:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'ReportAdmin not found ',
            }, status=status.HTTP_404_NOT_FOUND)


class ReviewListApi(APIView):
    """
    get
    Return a list of all Reviews

    http://192.168.1.14:8002/api/v1/admin/review/list?page=1&ordering=-name&search=sonu

    """

    # permission = (Permission.objects.filter(codename='list_review'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'GET': group,
    # }

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.permission_name = 'add_faq'

    def get(self, request):
        queryset = Review.objects.filter(status=True)
        ordering = request.GET.get('ordering', None)
        search = request.GET.get('search', None)

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(rating__icontains=search) | Q(name__icontains=search))

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

        serializer = ReviewListSerializer(result_page, many=True)
        s_data = paginator.get_paginated_response(serializer.data)

        return Response(
            {
                'status': status.HTTP_200_OK,
                'message': 'Review List fetched',
                'data': s_data.data
            },
            status=status.HTTP_200_OK
        )


class ReviewIsBlockApi(APIView):
    """
      Put:
    Update Review set is_blocked=True where status=True

    # """

    # permission = (Permission.objects.filter(codename='delete_review'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'GET': group,
    #     'PUT':group
    # }

    def get_object(self, id):

        try:
            return Review.objects.get(id=id, status=True)
        except Review.DoesNotExist:
            raise NotFound(detail="Error 404 ,Review id not found", code=404)

    def put(self, request, id):

        try:
            review_obj = self.get_object(id)
            if not review_obj.is_block:
                review_obj.is_block = True
            else:
                review_obj.is_block = False

            review_obj.updated_on = timezone.now()
            review_obj.save()

            return Response({
                'status': status.HTTP_201_CREATED,
                'message': 'Review blocked successfully',
            })
        except AttributeError:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Review not found ',
            }, status=status.HTTP_404_NOT_FOUND)


class ReviewDeleteApi(APIView):
    """
     Put:
         Delete faq set status=False where status=True

    """

    # permission = (Permission.objects.filter(codename='delete_review'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'GET': group,
    #     'PUT': group
    # }

    def get_object(self, id):

        try:
            return Review.objects.get(id=id, status=True)
        except Review.DoesNotExist:
            raise NotFound(detail="Error 404 ,review id not found", code=404)

    def put(self, request, id):

        try:
            review_obj = self.get_object(id)
            review_obj.status = False
            review_obj.updated_on = timezone.now()

            review_obj.save()

            return Response({
                'status': status.HTTP_201_CREATED,
                'message': 'Review Deleted successfully',
            })
        except AttributeError:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Review not found ',
            }, status=status.HTTP_404_NOT_FOUND)


class ReviewCreateApi(APIView):
    """
    post:
        API for Create review.
    """

    # Parameter description for API documentation starts here
    schema = schemas.ManualSchema(fields=[
        coreapi.Field(
            "assignment_no",
            required=True,
            location="form",
            schema=coreschema.String(
                description="Enter assignment_no here"
            )
        ),
        coreapi.Field(
            "name",
            required=True,
            location="form",
            schema=coreschema.String(
                description="Enter name"
            )
        ),
        coreapi.Field(
            "title",
            required=True,
            location="form",
            schema=coreschema.String(
                description="Enter title"
            )
        ),
        coreapi.Field(
            "rating",
            required=True,
            location="form",
            schema=coreschema.Integer(
                description="Enter rating"
            )
        ),
        coreapi.Field(
            "message",
            required=True,
            location="form",
            schema=coreschema.String(
                description="Enter message"
            )
        ),
        coreapi.Field(
            "user_id",
            required=True,
            location="form",
            schema=coreschema.String(
                description="Enter user_id"
            )
        ),
        coreapi.Field(
            "review_id",
            required=False,
            location="form",
            schema=coreschema.String(
                description="Enter review_id while update review"
            )
        )
    ])

    # Parameter description for API documentation ends here

    """
    permission:
    permission is being handled according to group permission of logged in user
    # """

    # permission_name = 'add_faq'

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.permission_name = 'add_faq'
    # permission = (Permission.objects.filter(codename='add_faq'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'POST': group,
    # }

    # permission_classes = permission_to_user('add_faq')

    def post(self, request, format=None):
        review_id = request.data.get('review_id', None)

        if not review_id:
            serializer = ReviewDetailSerializer(data=request.data)
        else:
            try:
                review_instance = Review.objects.get(id=review_id)
            except Exception:
                return Response(
                    {
                        'status': 404,
                        'message': 'Review not found',
                        'data': []
                    }, status=status.HTTP_400_BAD_REQUEST
                )
            serializer = ReviewDetailSerializer(review_instance, data=request.data)

        if serializer.is_valid():
            if not review_id:
                serializer.validated_data['created_on'] = timezone.now()
            serializer.validated_data['updated_on'] = timezone.now()

            serializer.save()

            return Response(
                {
                    'status': status.HTTP_201_CREATED,
                    'message': 'Review data saved successfully.'
                }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReviewIsBlockApi(APIView):
    """
      Put:
    Update review set is_blocked=True where status=True

    # """

    # permission = (Permission.objects.filter(codename='delete_faq'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'GET': group,
    #     'PUT':group
    # }

    def get_object(self, id):

        try:
            return Review.objects.get(id=id, status=True)
        except Review.DoesNotExist:
            raise NotFound(detail="Error 404 ,review id not found", code=404)

    def put(self, request, id):

        try:
            review_obj = self.get_object(id)
            if review_obj.is_block:
                review_obj.is_block = False
            else:
                review_obj.is_block = True
            review_obj.updated_on = timezone.now()

            review_obj.save()

            return Response({
                'status': status.HTTP_201_CREATED,
                'message': 'Review update successfully',
                'is_block': review_obj.is_block
            })
        except AttributeError:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Review not found ',
            }, status=status.HTTP_404_NOT_FOUND)


class ReviewDeleteApi(APIView):
    """
     Put:
         Delete Review set status=False where status=True

    """

    # permission = (Permission.objects.filter(codename='delete_faq'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'GET': group,
    #     'PUT': group
    # }

    def get_object(self, id):

        try:
            return Review.objects.get(id=id, status=True)
        except Review.DoesNotExist:
            raise NotFound(detail="Error 404 ,review id not found", code=404)

    def put(self, request, id):

        try:
            review_obj = self.get_object(id)
            review_obj.status = False
            review_obj.updated_on = timezone.now()

            review_obj.save()

            return Response({
                'status': status.HTTP_201_CREATED,
                'message': 'Review Deleted successfully',
            })
        except AttributeError:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Review not found ',
            }, status=status.HTTP_404_NOT_FOUND)


class ReviewDetailApi(APIView):
    """
     Get a detail of Review
     """

    # permission = (Permission.objects.filter(codename='view_enquiry'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'GET': group,
    #
    # }

    def get_object(self, id):

        try:
            return Review.objects.get(id=id, status=True)
        except Review.DoesNotExist:
            raise NotFound(detail="Error 404 ,review id not found", code=404)

    def get(self, request, id):

        try:

            review_obj = self.get_object(id)
            serializer = ReviewDetailSerializer(review_obj)

            return Response({

                'status': status.HTTP_200_OK,
                'message': 'Review Detail fetched',
                'data': serializer.data,
            })
        except AttributeError:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Review not found ',
            }, status=status.HTTP_404_NOT_FOUND)


class NotificationListApi(APIView):
    """
    get:
    API for get list of all notification in admin panel. Ex: http://192.168.1.14:8002/api/v1/admin/notification/notificationList/?page=1&ordering=id&search=134
    """

    # permission = (Permission.objects.filter(codename='list_notification'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'GET': group,
    # }

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.permission_name = 'list_notification'

    def get(self, request):
        ordering = request.GET.get('ordering', None)
        search = request.GET.get('search', None)

        queryset = PushNotification.objects.filter(status=True)

        # if search value is available
        if search:
            queryset = queryset.filter(
                Q(user__username__icontains=search) | Q(title__icontains=search) | Q(message__icontains=search))

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

        notification_ser = NotificationSerializer(result_page, many=True)

        s_data = paginator.get_paginated_response(notification_ser.data)

        if notification_ser:
            return Response(
                {
                    'status': status.HTTP_200_OK,
                    'message': 'data fetched',
                    'search_keys': 'user_id, title, message',
                    'data': s_data.data
                }, status=status.HTTP_200_OK
            )
        else:
            return Response(
                {
                    'status': status.HTTP_500_INTERNAL_SERVER_ERROR,
                    'message': 'Something went wrong. Please try later.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SendNotificationApi(APIView):
    """
    get:
    API for get list of all notification in admin panel
    """

    # Parameter description for API documentation starts here
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
            "title",
            required=True,
            location="form",
            schema=coreschema.String(
                description="Enter title of notification"
            )
        ),
        coreapi.Field(
            "message",
            required=True,
            location="form",
            schema=coreschema.String(
                description="Enter message for notification"
            )
        )
    ])

    # Parameter description for API documentation ends here

    # permission = (Permission.objects.filter(codename='send_notification'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'GET': group,
    # }

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.permission_name = 'send_notification'

    def post(self, request):
        user_ids = request.data.get('user_ids', None)
        title = request.data.get('title', None)
        message = request.data.get('message', None)
        print('*********REQUESTED DATA**********')
        print(request.data)

        if user_ids and title and message:
            user_ids = json.loads(user_ids)
            device_tokens = []

            for user_id in user_ids:
                device_qs = LoginLog.objects.filter(
                    Q(user_id=user_id) &
                    Q(is_logged_out=False) &
                    ~Q(device_token=None)
                )

                # save notification for each user in push_notifications table
                PushNotification.objects.create(
                    user_id=user_id,
                    title=title,
                    message=message,
                    device_count=len(device_qs),
                    # created_by=request.user,
                    created_on=timezone.now(),
                    updated_on=timezone.now()
                )

                # getting all active device tokens of user from user_login_logs table
                for device_q in device_qs:
                    if device_q.device_token:
                        device_tokens.append(device_q.device_token)

                # sending notification
                result = send_notification(device_tokens, title=title, message=message)
                print(result)

            return Response(
                {
                    'status': status.HTTP_201_CREATED,
                    'message': 'Notification send.',
                    'data': ''
                }, status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {
                    'status': status.HTTP_400_BAD_REQUEST,
                    'message': 'User Ids, title and message are required.'
                }, status=status.HTTP_400_BAD_REQUEST
            )


class NotificationDeleteApi(APIView):
    """
     Put:
         Delete Notification set status=False where status=True

    """

    # permission = (Permission.objects.filter(codename='delete_notification'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'GET': group,
    #     'PUT': group
    # }

    def get_object(self, id):

        try:
            return PushNotification.objects.get(id=id, status=True)
        except PushNotification.DoesNotExist:
            raise NotFound(detail="Error 404, Notification id not found", code=404)

    def put(self, request, id):

        try:
            notification_obj = self.get_object(id)
            notification_obj.status = False
            notification_obj.updated_on = timezone.now()

            notification_obj.save()

            return Response({
                'status': status.HTTP_201_CREATED,
                'message': 'Notification Deleted successfully',
            })
        except AttributeError:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Notification not found ',
            }, status=status.HTTP_404_NOT_FOUND)
