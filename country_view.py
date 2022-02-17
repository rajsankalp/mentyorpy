from django.db.models import Q
from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from apps.country.models import Country, State
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from apps.users.models import User
import random
from libraries.Functions import file_upload_handler, make_dir
from django.conf import settings
from api.v1.admin_serializers.country_serializers import CountryCreateSerializer, CountryListSerializer, \
    CountryDetailSerializer, \
    StateCreateSerializer, StateListSerializer, StateDetailSerializer
from libraries.permission import HasGroupPermission
from django.contrib.auth.models import Permission, Group
import coreapi
import coreschema
from rest_framework import schemas
from django.core.exceptions import ObjectDoesNotExist


class CountryCreateApi(APIView):
    """
    Post:
         Create Country Api for admin panel
    """
    permission = (Permission.objects.filter(codename='add_country'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'POST': group,

    }

    schema = schemas.ManualSchema(fields=[
        coreapi.Field(
            'name',
            required=True,
            location="form",
            schema=coreschema.String(
                description="NAME OF COUNTRY"
            )
        ),
        coreapi.Field(
            'title',
            required=True,
            location="form",
            schema=coreschema.String(
                description="title of country"
            )
        ),
        coreapi.Field(
            'main_title',
            required=False,
            location="form",
            schema=coreschema.String(
                description="enter the main_title. For SEO purpose"
            )
        ),
        coreapi.Field(
            'slug',
            required=True,
            location="form",
            schema=coreschema.String(
                description="slug for the country "
            )
        ),
        coreapi.Field(
            'image',
            required=False,
            location="form",
            schema=coreschema.String(
                description="image if required"
            )
        ),
        coreapi.Field(
            'content',
            required=False,
            location="form",
            schema=coreschema.String(
                description="enter the content"
            )
        ),
        coreapi.Field(
            'meta_description',
            required=False,
            location="form",
            schema=coreschema.String(
                description="meta description for the country. For SEO purpose"
            )
        ),
        coreapi.Field(
            'meta_keywords',
            required=False,
            location="form",
            schema=coreschema.String(
                description="meta keyword for the country. For SEO purpose"
            )
        ),
        coreapi.Field(
            'head_script',
            required=False,
            location="form",
            schema=coreschema.String(
                description="head script for the country. For SEO purpose"
            )
        )

    ])

    def post(self, request, format=None):
        serializer = CountryCreateSerializer(data=request.data)
        country_data = request.data
        subject_image = ''
        if serializer.is_valid():
            serializer.validated_data['updated_on'] = timezone.now()
            serializer.validated_data['updated_by'] = request.user
            serializer.validated_data['slug'] = serializer.validated_data['slug'].lower()
            serializer.validated_data['status'] = True

            if 'image' in country_data:
                rndm = random.randint(100000, 9999999)

                file_name = country_data['image']
                upload_dir = make_dir(
                    settings.MEDIA_ROOT + settings.CUSTOM_DIRS.get('COUNTRY_DIR') + '/' + str(rndm) + '/'
                )

                file_name = file_upload_handler(file_name, upload_dir)

                country_image = settings.MEDIA_URL + '/' + settings.CUSTOM_DIRS.get('COUNTRY_DIR') + '/' + str(
                    rndm) + '/' + file_name

                serializer.validated_data['image'] = country_image

            serializer.validated_data['created_by'] = request.user
            serializer.validated_data['created_on'] = timezone.now()
            serializer.validated_data['status'] = True

            serializer.save()
            return Response({
                'status': status.HTTP_201_CREATED,
                'message': 'Country Create successfully ',
            }, status=status.HTTP_201_CREATED)
            # Get User instance for foreignkey in Created_by ,Updated_by

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CountryUpdateView(APIView):
    schema = schemas.ManualSchema(fields=[
        coreapi.Field(
            'name',
            required=True,
            location="form",
            schema=coreschema.String(
                description="NAME OF COUNTRY"
            )
        ),
        coreapi.Field(
            'title',
            required=True,
            location="form",
            schema=coreschema.String(
                description="title of country"
            )
        ),
        coreapi.Field(
            'title',
            required=False,
            location="form",
            schema=coreschema.String(
                description="main-title of country. For SEO"
            )
        ),
        coreapi.Field(
            'slug',
            required=True,
            location="form",
            schema=coreschema.String(
                description="slug for the country "
            )
        ),
        coreapi.Field(
            'image',
            required=False,
            location="form",
            schema=coreschema.String(
                description="image if required"
            )
        ),
        coreapi.Field(
            'content',
            required=False,
            location="form",
            schema=coreschema.String(
                description="content"
            )
        ),
        coreapi.Field(
            'meta_description',
            required=False,
            location="form",
            schema=coreschema.String(
                description="meta description for the country. For SEO purpose"
            )
        ),
        coreapi.Field(
            'meta_keywords',
            required=False,
            location="form",
            schema=coreschema.String(
                description="meta keyword for the country. For SEO purpose"
            )
        ),
        coreapi.Field(
            'head_script',
            required=False,
            location="form",
            schema=coreschema.String(
                description="head script for the country. For SEO purpose"
            )
        )

    ])

    def get_object(self, pk):
        try:
            return Country.objects.get(pk=pk)
        except Country.DoesNotExist:
            return Response(
                {
                    'status': status.HTTP_404_NOT_FOUND,
                    'message': 'country not found'
                }
            )

    def put(self, request, pk, format=None):
        country = self.get_object(pk)
        serializer = CountryCreateSerializer(country, data=request.data)
        if serializer.is_valid():
            if 'image' in request.data:
                rndm = random.randint(100000, 9999999)

                file_name = request.data['image']
                upload_dir = make_dir(
                    settings.MEDIA_ROOT + settings.CUSTOM_DIRS.get('COUNTRY_DIR') + '/' + str(rndm) + '/'
                )

                file_name = file_upload_handler(file_name, upload_dir)

                country_image = settings.MEDIA_URL + '/' + settings.CUSTOM_DIRS.get('COUNTRY_DIR') + '/' + str(
                    rndm) + '/' + file_name

                serializer.validated_data['image'] = country_image
                serializer.validated_data['slug'] = serializer.validated_data['slug'].lower()
            serializer.validated_data['status'] = True

            serializer.save()
            return Response(
                {
                    'status': status.HTTP_200_OK,
                    'message': 'country updated'
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CountryListApi(APIView):
    """
    Get:
        A list of all Country Api
        http://192.168.1.14:8002/api/v1/admin/user/list?page=1&ordering=-name&search=country name
    """
    permission = (Permission.objects.filter(codename='list_country'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'GET': group,

    }

    def get(self, request):

        try:
            queryset = Country.objects.filter(status=True).order_by('id')

            serializer = CountryListSerializer(queryset, many=True)

            return Response(
                {
                    'status': status.HTTP_200_OK,
                    'message': 'Country List fetched',
                    'data': serializer.data
                },
                status=status.HTTP_200_OK
            )

        except AttributeError:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Error 404 ,country  not found',
            }, status=status.HTTP_404_NOT_FOUND)


class CountryDetailApi(APIView):
    """
    Get
        A Detail of Country Api
    """
    permission = (Permission.objects.filter(codename='view_country'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'GET': group,

    }

    def get_object(self, pk):
        try:
            return Country.objects.get(id=pk)
        except Country.DoesNotExist:
            raise NotFound(detail="Error 404 ,country slug not found", code=404)

    def get(self, request, pk):
        try:
            queryset = self.get_object(pk)

            serializer = CountryDetailSerializer(queryset)

            return Response({
                'status': status.HTTP_200_OK,
                'message': 'Country Detail fetched',
                'data': serializer.data
            }, status=status.HTTP_200_OK)

        except AttributeError:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Error 404 Not found',
            }, status=status.HTTP_404_NOT_FOUND)


class CountryIsBlockApi(APIView):
    """
    Put:
        API for Update Country set is_block=True where status=True
    """
    permission = (Permission.objects.filter(codename='delete_country'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'GET': group,
        'PUT': group

    }

    def get_object(self, slug):
        try:
            return Country.objects.get(slug=slug, status=True)
        except Country.DoesNotExist:
            raise NotFound(detail="Error 404 ,country slug not found", code=404)

    def put(self, request, slug):
        try:
            country_obj = self.get_object(slug)
            country_obj.is_block = True
            country_obj.updated_on = timezone.now()

            country_obj.save()

            return Response({
                'status': status.HTTP_201_CREATED,
                'message': 'Country updated successfully',
            }, status=status.HTTP_201_CREATED)
        except AttributeError:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Error 404 ,country slug no found',
            }, status=status.HTTP_404_NOT_FOUND)


class CountryDeleteApi(APIView):
    """
    Put:
        API for Delete Country set status=False where status=True
    """
    permission = (Permission.objects.filter(codename='delete_country'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'GET': group,
        'PUT': group

    }

    def get_object(self, slug):
        try:
            return Country.objects.get(slug=slug)
        except Country.DoesNotExist:
            raise NotFound(detail="Error 404 ,Country slug not found", code=404)

    def put(self, request, slug):
        try:
            country_obj = self.get_object(slug)
            country_obj.status = False

            country_obj.save()

            return Response({
                'status': status.HTTP_201_CREATED,
                'message': 'Country Delete successfully',
            }, status=status.HTTP_201_CREATED)
        except AttributeError:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Error 404 ,Country slug no found',
            }, status=status.HTTP_404_NOT_FOUND)


class StateCreateApi(APIView):
    """
    Post:
         Create State Api for admin panel
    """

    permission = (Permission.objects.filter(codename='add_state'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'POST': group,

    }

    schema = schemas.ManualSchema(fields=[

        coreapi.Field(
            'country',
            required=False,
            location="form",
            schema=coreschema.String(
                description="id of country"
            )
        ),

        coreapi.Field(
            'name',
            required=True,
            location="form",
            schema=coreschema.String(
                description="NAME OF state"
            )
        ),
        coreapi.Field(
            'title',
            required=True,
            location="form",
            schema=coreschema.String(
                description="title of state"
            )
        ),
        coreapi.Field(
            'main_title',
            required=False,
            location="form",
            schema=coreschema.String(
                description="enter the main_title. For SEO purpose"
            )
        ),
        coreapi.Field(
            'slug',
            required=True,
            location="form",
            schema=coreschema.String(
                description="slug for the state('unique') "
            )
        ),
        coreapi.Field(
            'image',
            required=False,
            location="form",
            schema=coreschema.String(
                description="image if required"
            )
        ),

        coreapi.Field(
            'content',
            required=False,
            location="form",
            schema=coreschema.String(
                description="write the content here"
            )
        ),
        coreapi.Field(
            'meta_description',
            required=False,
            location="form",
            schema=coreschema.String(
                description="meta description for the state. For SEO purpose"
            )
        ),
        coreapi.Field(
            'meta_keywords',
            required=False,
            location="form",
            schema=coreschema.String(
                description="meta keyword for the state. For SEO purpose"
            )
        ),
        coreapi.Field(
            'head_script',
            required=False,
            location="form",
            schema=coreschema.String(
                description="head script for the state. For SEO purpose"
            )
        )
    ]
    )

    def post(self, request, format=None):
        serializer = StateCreateSerializer(data=request.data)
        state_data = request.data
        subject_image = ''
        if serializer.is_valid():

            rndm = random.randint(100000, 9999999)

            if 'image' in state_data:
                file_name = state_data['image']
                upload_dir = make_dir(
                    settings.MEDIA_ROOT + settings.CUSTOM_DIRS.get('STATE_DIR') + '/' + str(rndm) + '/'
                )

                file_name = file_upload_handler(file_name, upload_dir)

                state_image = settings.MEDIA_URL + '/' + settings.CUSTOM_DIRS.get('STATE_DIR') + '/' + str(
                    rndm) + '/' + file_name

                serializer.validated_data['image'] = state_image

            user_obj = User.objects.get(is_superuser=True)
            # Get User instance for foreignkey in Created_by ,Updated_by
            serializer.validated_data['created_by'] = user_obj
            serializer.validated_data['updated_by'] = user_obj
            serializer.validated_data['status'] = True
            serializer.validated_data['slug'] = serializer.validated_data['slug'].lower()

            """
            checking if the credentials provided for country is right or not
            
            """

            if 'country' in state_data:
                if state_data['country'].isdigit():
                    pass
                else:
                    print(type(state_data['country']))
                    return Response(
                        {
                            'status': status.HTTP_400_BAD_REQUEST,
                            'message': 'wrong country credentials'
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                return Response(
                    {
                        'status': status.HTTP_400_BAD_REQUEST,
                        'message': 'country not selected'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                country_obj = Country.objects.get(id=state_data['country'])
                serializer.validated_data['country'] = country_obj
            except ObjectDoesNotExist:
                raise NotFound(detail="Error 404 ,Country not found", code=404)

            serializer.validated_data['created_on'] = timezone.now()
            serializer.validated_data['updated_on'] = timezone.now()

            serializer.save()

            return Response({
                'status': status.HTTP_201_CREATED,
                'message': 'State Created',
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StateUpdateView(APIView):
    schema = schemas.ManualSchema(fields=[
        coreapi.Field(
            'name',
            required=True,
            location="form",
            schema=coreschema.String(
                description="NAME OF COUNTRY"
            )
        ),
        coreapi.Field(
            'title',
            required=True,
            location="form",
            schema=coreschema.String(
                description="title of country"
            )
        ),
        coreapi.Field(
            'main_title',
            required=False,
            location="form",
            schema=coreschema.String(
                description="main_title for the state. For SEO purpose"
            )
        ),
        coreapi.Field(
            'slug',
            required=False,
            location="form",
            schema=coreschema.String(
                description="slug for the country "
            )
        ),
        coreapi.Field(
            'image',
            required=False,
            location="form",
            schema=coreschema.String(
                description="image if required"
            )
        ),
        coreapi.Field(
            'meta_description',
            required=False,
            location="form",
            schema=coreschema.String(
                description="meta description for the state. For SEO purpose"
            )
        ),
        coreapi.Field(
            'meta_keywords',
            required=False,
            location="form",
            schema=coreschema.String(
                description="meta keyword for the state. For SEO purpose"
            )
        ),
        coreapi.Field(
            'head_script',
            required=False,
            location="form",
            schema=coreschema.String(
                description="head script for the state. For SEO purpose"
            )
        )

    ])

    def get_object(self, pk):
        try:
            return State.objects.get(pk=pk)
        except State.DoesNotExist:
            return Response(
                {
                    'status': status.HTTP_404_NOT_FOUND,
                    'message': 'country not found'
                }
            )

    def put(self, request, pk, format=None):
        state = self.get_object(pk)
        serializer = StateCreateSerializer(state, data=request.data)
        if serializer.is_valid():
            rndm = random.randint(100000, 9999999)

            if 'image' in request.data:
                file_name = request.data['image']
                upload_dir = make_dir(
                    settings.MEDIA_ROOT + settings.CUSTOM_DIRS.get('STATE_DIR') + '/' + str(rndm) + '/'
                )

                file_name = file_upload_handler(file_name, upload_dir)

                state_image = settings.MEDIA_URL + settings.CUSTOM_DIRS.get('STATE_DIR') + '/' + str(
                    rndm) + '/' + file_name

                serializer.validated_data['image'] = state_image
            serializer.validated_data['slug'] = serializer.validated_data['slug'].lower()
            serializer.save()
            return Response(
                {
                    'status': status.HTTP_200_OK,
                    'message': 'state updated'
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StateListApi(APIView):
    """
        Get:
            A list of all State Api

            http://192.168.1.14:8002/api/v1/admin/user/list?page=1&ordering=-name&search=state name
        """
    permission = (Permission.objects.filter(codename='list_state'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'GET': group,

    }

    def get_object(self, slug):
        try:
            return Country.objects.get(slug=slug)
        except Country.DoesNotExist:
            raise NotFound(detail="Error 404 ,state slug not found", code=404)

    def get(self, request, slug):

        try:
            qs = self.get_object(slug)
            queryset = State.objects.filter(country=qs)

            serializer = StateListSerializer(queryset, many=True)

            return Response(
                {
                    'status': status.HTTP_200_OK,
                    'message': 'state List fetched',
                    'data': serializer.data
                },
                status=status.HTTP_200_OK
            )

        except AttributeError:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Error 404 ,state  not found',
            }, status=status.HTTP_404_NOT_FOUND)


class StateDetailApi(APIView):
    """
    Get:
        API for Detail of a State.
    """
    permission = (Permission.objects.filter(codename='view_state'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'GET': group,

    }

    def get_object(self, slug):
        try:
            return State.objects.get(slug=slug)
        except State.DoesNotExist:
            raise NotFound(detail="Error 404 ,state slug not found", code=404)

    def get(self, request, slug):
        try:
            queryset = self.get_object(slug)

            serializer = StateDetailSerializer(queryset)
            return Response({
                'status': status.HTTP_200_OK,
                'message': 'state Detail fetched',
                'data': serializer.data,
            }, status=status.HTTP_200_OK)

        except AttributeError:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Error 404 ,state  no found',
            }, status=status.HTTP_404_NOT_FOUND)


class StateIsBlockApi(APIView):
    """
    Put:
        API for Update State set is_block=True where status=True
    """
    permission = (Permission.objects.filter(codename='delete_state'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'GET': group,
        'PUT': group,

    }

    def get_object(self, slug):
        try:
            return State.objects.get(slug=slug, status=True)
        except State.DoesNotExist:
            raise NotFound(detail="Error 404 ,state slug not found", code=404)

    def put(self, request, slug):
        try:
            state_obj = self.get_object(slug)
            state_obj.is_block = True
            state_obj.updated_on = timezone.now()

            state_obj.save()

            return Response({
                'status': status.HTTP_201_CREATED,
                'message': 'State updated successfully',
            }, status=status.HTTP_201_CREATED)
        except AttributeError:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Error 404 ,state slug no found',
            }, status=status.HTTP_404_NOT_FOUND)


class StateDeleteApi(APIView):
    """
    Put:
        API for Delete State set status=False where status=True
    """
    permission = (Permission.objects.filter(codename='delete_state'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'GET': group,
        'PUT': group,

    }

    def get_object(self, slug):
        try:
            return State.objects.get(slug=slug)
        except State.DoesNotExist:
            raise NotFound(detail="Error 404 ,State slug not found", code=404)

    def put(self, request, slug):
        try:
            state_obj = self.get_object(slug)
            state_obj.status = False

            state_obj.save()

            return Response({
                'status': status.HTTP_201_CREATED,
                'message': 'State Delete successfully',
            }, status=status.HTTP_201_CREATED)
        except AttributeError:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Error 404 ,State slug no found',
            }, status=status.HTTP_404_NOT_FOUND)
