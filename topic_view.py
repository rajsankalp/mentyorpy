from rest_framework.exceptions import NotFound
from rest_framework.views import APIView
from api.v1.admin_serializers.topic_serializers import SubjectCreateSerializer, SubjectListSerializer, \
    SubjectDetailSerializer, \
    SubSubjectCreateSerializer, SubSubjectListSerializer, SubSubjectDetailSerializer, TopicCreateSerializer, \
    TopicListSerializer, TopicDetailSerializer
from apps.topic.models import Subject, Subsubject, Topic
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
import random
from libraries.Functions import file_upload_handler, make_dir
from django.conf import settings
from apps.users.models import User
from libraries.permission import HasGroupPermission
from django.contrib.auth.models import Permission, Group
import coreapi
import coreschema
from rest_framework import schemas
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist


class SubjectCreateApi(APIView):
    """
    Post:
         Create Subjects in topic of admin panel
    """
    # permission = (Permission.objects.filter(codename='add_subject'))
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
            'title',
            required=True,
            location="form",
            schema=coreschema.String(
                description="title name should be given here"
            )
        ),
        coreapi.Field(
            'main_title',
            required=False,
            location="form",
            schema=coreschema.String(
                description="For SEO"
            )
        ),
        coreapi.Field(
            'short_name',
            required=False,
            location="form",
            schema=coreschema.String(
                description="short name will "
            )
        ),
        coreapi.Field(
            'contents',
            required=False,
            location="form",
            schema=coreschema.String(
                description="in the date time format i.e '2019-04-02 09:14:52"
            )
        ),
        coreapi.Field(
            'slug',
            required=True,
            location="form",
            schema=coreschema.String(
                description="additional files concated with assignments file"
            )
        ),
        coreapi.Field(
            'meta_description',
            required=False,
            location="form",
            schema=coreschema.String(
                description="Enter description. For SEO"
            )
        ),
        coreapi.Field(
            'meta_keywords',
            required=False,
            location="form",
            schema=coreschema.String(
                description="For SEO"
            )
        ),
        coreapi.Field(
            'head_script',
            required=False,
            location="form",
            schema=coreschema.String(
                description="For SEO"
            )
        ),

        coreapi.Field(
            'image',
            required=False,
            location="form",
            schema=coreschema.String(
                description="attach the image here"
            )
        ),
    ])

    def post(self, request, format=None):

        serializer = SubjectCreateSerializer(data=request.data)
        subject_data = request.data
        subject_image = ''

        if serializer.is_valid():

            serializer.validated_data['slug'] = serializer.validated_data['slug'].lower()
            if 'image' in subject_data:
                rndm = random.randint(100000, 9999999)

                file_name = subject_data['image']
                upload_dir = make_dir(
                    settings.MEDIA_ROOT + settings.CUSTOM_DIRS.get('SUBJECT_DIR') + '/' + str(rndm) + '/'
                )

                file_name = file_upload_handler(file_name, upload_dir)

                subject_image = settings.MEDIA_URL + '/' + settings.CUSTOM_DIRS.get('SUBJECT_DIR') + '/' + str(
                    rndm) + '/' + file_name

                serializer.validated_data['image'] = subject_image
            serializer.validated_data['created_on'] = timezone.datetime.now()
            serializer.validated_data['updated_on'] = timezone.datetime.now()

            user_obj = User.objects.get(is_superuser=True)
            # Get user instance for subject Foreignkey

            serializer.validated_data['created_by'] = user_obj
            serializer.validated_data['updated_by'] = user_obj
            serializer.validated_data['status'] = True

            # serializer.save()
            subject_create = Subject.objects.create(**serializer.validated_data)
            return Response({
                'status': status.HTTP_201_CREATED,
                'message': 'Subject data saved successfully',
                'data': {'subject_id': subject_create.id}
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubjectUpdateView(APIView):
    schema = schemas.ManualSchema(fields=[
        coreapi.Field(
            'title',
            required=True,
            location="form",
            schema=coreschema.String(
                description="title name should be given here"
            )
        ),
        coreapi.Field(
            'main_title',
            required=False,
            location="form",
            schema=coreschema.String(
                description="For SEO"
            )
        ),
        coreapi.Field(
            'short_name',
            required=False,
            location="form",
            schema=coreschema.String(
                description="short name will "
            )
        ),
        coreapi.Field(
            'contents',
            required=False,
            location="form",
            schema=coreschema.String(
                description="in the date time format i.e '2019-04-02 09:14:52"
            )
        ),
        coreapi.Field(
            'slug',
            required=True,
            location="form",
            schema=coreschema.String(
                description="additional files concated with assignments file"
            )
        ),
        coreapi.Field(
            'meta_description',
            required=False,
            location="form",
            schema=coreschema.String(
                description="Enter description. For SEO"
            )
        ),
        coreapi.Field(
            'meta_keywords',
            required=False,
            location="form",
            schema=coreschema.String(
                description="For SEO"
            )
        ),
        coreapi.Field(
            'head_script',
            required=False,
            location="form",
            schema=coreschema.String(
                description="For SEO"
            )
        ),

        coreapi.Field(
            'image',
            required=False,
            location="form",
            schema=coreschema.String(
                description="attach the image here"
            )
        ),

    ])

    def get_object(self, id):
        try:
            return Subject.objects.get(id=id)
        except Subject.DoesNotExist:
            return Response(
                {
                    'status': status.HTTP_404_NOT_FOUND,
                    'message': 'subject not found'
                }
            )

    def put(self, request, id, format=None):
        subject = self.get_object(id)
        serializer = SubjectCreateSerializer(subject, data=request.data)
        if serializer.is_valid():
            if 'image' in request.data:
                rndm = random.randint(100000, 9999999)

                file_name = request.data['image']
                upload_dir = make_dir(
                    settings.MEDIA_ROOT + settings.CUSTOM_DIRS.get('SUBJECT_DIR') + '/' + str(rndm) + '/'
                )

                file_name = file_upload_handler(file_name, upload_dir)

                country_image = settings.MEDIA_URL + settings.CUSTOM_DIRS.get('SUBJECT_DIR') + '/' + str(
                    rndm) + '/' + file_name

                serializer.validated_data['image'] = country_image

            serializer.validated_data['slug'] = serializer.validated_data['slug'].lower()
            serializer.validated_data['status'] = True

            serializer.save()
            return Response(
                {
                    'status': status.HTTP_200_OK,
                    'message': 'subject updated'
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubjectListApi(APIView):
    """
    Get:
        API for listing of all  Subjects.

    """
    # permission = (Permission.objects.filter(codename='list_subject'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'GET': group,
    #     'PUT': group,
    #     'POST': group
    #
    # }

    def get(self, request):
        ordering = request.GET.get('ordering', None)
        search = request.GET.get('search', None)

        queryset = Subject.objects.filter(status=True)

        serializer = SubjectListSerializer(queryset, many=True)

        return Response({
            'status': status.HTTP_200_OK,
            'message': 'subject List fetched',
            'data': serializer.data
        })


class SubjectDetailApi(APIView):
    """
    Get :
         API for Detail of a Subject.
    """
    # permission = (Permission.objects.filter(codename='view_subject'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'GET': group,
    #     'PUT': group,
    #     'POST': group
    #
    # }

    def get_object(self, slug):
        try:
            return Subject.objects.get(slug=slug)
        except Subject.DoesNotExist:
            raise NotFound(detail="Error 404 ,subject slug not found", code=404)

    def get(self, request, slug):
        try:
            subject_obj = self.get_object(slug)
            serializer = SubjectDetailSerializer(subject_obj)

            return Response({
                'status': status.HTTP_200_OK,
                'message': 'subject Details Fetched',
                'data': serializer.data,
            }, status=status.HTTP_200_OK)
        except AttributeError:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Error 404 ,subject slug no found',
            }, status=status.HTTP_404_NOT_FOUND)


class SubjectIsBlockApi(APIView):
    """
    Put:
        API for Update Subject set is_block=True where status=True
    """
    # permission = (Permission.objects.filter(codename='add_subject'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'GET': group,
    #     'PUT': group,
    #     'POST': group
    #
    # }

    def get_object(self, id):
        try:
            return Subject.objects.get(id=id, status=True)
        except Subject.DoesNotExist:
            raise NotFound(detail="Error 404 ,subject slug not found", code=404)

    def put(self, request, id):
        try:
            subject_obj = self.get_object(id)
            if subject_obj.is_block:
                subject_obj.is_block = False
            else:
                subject_obj.is_block = True

            subject_obj.updated_on = timezone.now()

            subject_obj.save()

            return Response({
                'status': status.HTTP_201_CREATED,
                'message': 'Subject updated successfully',
                'is_blocked': subject_obj.is_block
            }, status=status.HTTP_201_CREATED)
        except AttributeError:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Error 404 ,subject slug no found',

            }, status=status.HTTP_404_NOT_FOUND)


class SubjectDeleteApi(APIView):
    """
    Put:
        API for Delete Subject set status=False where status=True
    """
    # permission = (Permission.objects.filter(codename='delete_subject'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'GET': group,
    #     'PUT': group,
    #     'POST': group
    #
    # }

    def get_object(self, id):
        try:
            return Subject.objects.get(id=id)
        except Subject.DoesNotExist:
            raise NotFound(detail="Error 404 ,subject not found", code=404)

    def put(self, request, id):
        try:
            subject_obj = self.get_object(id)
            subject_obj.status = False

            subject_obj.save()

            return Response({
                'status': status.HTTP_201_CREATED,
                'message': 'Subject Delete successfully',
            }, status=status.HTTP_201_CREATED)
        except AttributeError:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Error 404 ,subject not found',
            }, status=status.HTTP_404_NOT_FOUND)


class SubSubjectCreateApi(APIView):
    """
        Post:
             Create SubSubjects in topic of admin panel
        """
    # permission = (Permission.objects.filter(codename='add_sub_subject'))
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
            'subject',
            required=True,
            location="form",
            schema=coreschema.Integer(
                description="subject id should be given here(i.e. 1)"
            )
        ),
        coreapi.Field(
            'title',
            required=True,
            location="form",
            schema=coreschema.String(
                description="title name should be given here"
            )
        ),
        coreapi.Field(
            'main_title',
            required=False,
            location="form",
            schema=coreschema.String(
                description="For SEO"
            )
        ),
        coreapi.Field(
            'short_name',
            required=True,
            location="form",
            schema=coreschema.String(
                description="short name will "
            )
        ),
        coreapi.Field(
            'contents',
            required=False,
            location="form",
            schema=coreschema.String(
                description="in the date time format i.e '2019-04-02 09:14:52"
            )
        ),
        coreapi.Field(
            'slug',
            required=True,
            location="form",
            schema=coreschema.String(
                description="additional files concated with assignments file"
            )
        ),
        coreapi.Field(
            'is_block',
            required=False,
            location="form",
            schema=coreschema.String(
                description="additional files concated with assignments file"
            )
        ),
        coreapi.Field(
            'meta_description',
            required=False,
            location="form",
            schema=coreschema.String(
                description="Enter description. For SEO"
            )
        ),
        coreapi.Field(
            'meta_keywords',
            required=False,
            location="form",
            schema=coreschema.String(
                description="For SEO"
            )
        ),
        coreapi.Field(
            'head_script',
            required=False,
            location="form",
            schema=coreschema.String(
                description="For SEO"
            )
        ),
        coreapi.Field(
            'image',
            required=False,
            location="form",
            schema=coreschema.String(
                description="attach the image here"
            )
        ),

    ])

    def post(self, request, format=None):

        serializer = SubSubjectCreateSerializer(data=request.data)
        sub_subject_data = request.data
        sub_subject_image = ''

        if serializer.is_valid():
            serializer.validated_data['slug'] = serializer.validated_data['slug'].lower()
            if 'image' in sub_subject_data:
                rndm = random.randint(100000, 9999999)

                file_name = sub_subject_data['image']
                upload_dir = make_dir(
                    settings.MEDIA_ROOT + settings.CUSTOM_DIRS.get('SUB_SUBJECT_DIR') + '/' + str(rndm) + '/'
                )

                file_name = file_upload_handler(file_name, upload_dir)

                sub_subject_image = settings.MEDIA_URL + '/' + settings.CUSTOM_DIRS.get('SUB_SUBJECT_DIR') + '/' + str(
                    rndm) + '/' + file_name

                serializer.validated_data['image'] = sub_subject_image

            serializer.validated_data['created_on'] = timezone.datetime.now()
            serializer.validated_data['updated_on'] = timezone.datetime.now()

            user_obj = User.objects.get(is_superuser=True)
            # Get user instance for subject Foreignkey

            serializer.validated_data['created_by'] = user_obj
            serializer.validated_data['updated_by'] = user_obj
            serializer.validated_data['status'] = True
            # serializer.save()
            sub_subject_create = Subsubject.objects.create(**serializer.validated_data)
            return Response({
                'status': status.HTTP_201_CREATED,
                'message': 'SubSubject data saved successfully',
                'data': {'sub_subject_id': sub_subject_create.id}
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubSubjectUpdateView(APIView):
    schema = schemas.ManualSchema(fields=[
        coreapi.Field(
            'subject',
            required=True,
            location="form",
            schema=coreschema.Integer(
                description="subject id should be given here(i.e. 1)"
            )
        ),
        coreapi.Field(
            'title',
            required=True,
            location="form",
            schema=coreschema.String(
                description="title name should be given here"
            )
        ),
        coreapi.Field(
            'main_title',
            required=False,
            location="form",
            schema=coreschema.String(
                description="For SEO"
            )
        ),
        coreapi.Field(
            'short_name',
            required=True,
            location="form",
            schema=coreschema.String(
                description="short name will "
            )
        ),
        coreapi.Field(
            'contents',
            required=False,
            location="form",
            schema=coreschema.String(
                description="in the date time format i.e '2019-04-02 09:14:52"
            )
        ),
        coreapi.Field(
            'slug',
            required=False,
            location="form",
            schema=coreschema.String(
                description="additional files concated with assignments file"
            )
        ),
        coreapi.Field(
            'meta_description',
            required=False,
            location="form",
            schema=coreschema.String(
                description="Enter description. For SEO"
            )
        ),
        coreapi.Field(
            'meta_keywords',
            required=False,
            location="form",
            schema=coreschema.String(
                description="For SEO"
            )
        ),
        coreapi.Field(
            'head_script',
            required=False,
            location="form",
            schema=coreschema.String(
                description="For SEO"
            )
        ),
        coreapi.Field(
            'image',
            required=False,
            location="form",
            schema=coreschema.String(
                description="attach the image here"
            )
        ),

    ])

    def get_object(self, pk):
        try:
            return Subsubject.objects.get(pk=pk)
        except Subsubject.DoesNotExist:
            return Response(
                {
                    'status': status.HTTP_404_NOT_FOUND,
                    'message': 'subject not found'
                }
            )

    def put(self, request, pk, format=None):
        subsubject = self.get_object(pk)
        serializer = SubSubjectCreateSerializer(subsubject, data=request.data)
        if serializer.is_valid():
            if 'image' in request.data:
                rndm = random.randint(100000, 9999999)

                file_name = request.data['image']
                upload_dir = make_dir(
                    settings.MEDIA_ROOT + settings.CUSTOM_DIRS.get('SUB_SUBJECT_DIR') + '/' + str(rndm) + '/'
                )

                file_name = file_upload_handler(file_name, upload_dir)

                country_image = settings.MEDIA_URL + settings.CUSTOM_DIRS.get('SUB_SUBJECT_DIR') + '/' + str(
                    rndm) + '/' + file_name

                serializer.validated_data['image'] = country_image

            serializer.validated_data['slug'] = serializer.validated_data['slug'].lower()
            serializer.validated_data['status'] = True

            serializer.save()
            return Response(
                {
                    'status': status.HTTP_200_OK,
                    'message': 'sub subject updated'
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubSubjectListApi(APIView):
    """
    Get :
         API for List of a SubSubject.
    """
    permission = (Permission.objects.filter(codename='list_sub_subject'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'GET': group,
        'PUT': group,
        'POST': group

    }

    def get_object(self, slug):
        try:
            # print(Subject.objects.get(slug=slug))
            return Subject.objects.get(slug=slug)
        except Subject.DoesNotExist:
            raise NotFound(detail="Error 404 ,subject not found", code=404)

    def get(self, request, slug):
        try:
            sub = self.get_object(slug)
            queryset = Subsubject.objects.filter(subject=sub)
            serializer = SubSubjectListSerializer(queryset, many=True)
            return Response({
                'status': status.HTTP_200_OK,
                'message': 'Sub-Subjects List fetched',
                'subject': 'test',
                'data': serializer.data
            }, status=status.HTTP_200_OK)

        except AttributeError:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Error 404 ,sub_subject  no found1',
            }, status=status.HTTP_404_NOT_FOUND)


class SubSubjectDetailApi(APIView):
    """
    Get:
        API for Detail of a SubSubject.
    """
    permission = (Permission.objects.filter(codename='view_sub_subject'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'GET': group,
        'PUT': group,
        'POST': group

    }

    def get_object(self, slug):
        try:
            return Subsubject.objects.get(slug=slug)
        except Subsubject.DoesNotExist:
            raise NotFound(detail="Error 404 ,sub_subject_slug not found", code=404)

    def get(self, request, slug):
        try:
            queryset = self.get_object(slug)
            serializer = SubSubjectDetailSerializer(queryset)
            return Response({
                'status': status.HTTP_200_OK,
                'message': 'Sub-Subject Detail fetched',
                'data': serializer.data,
            }, status=status.HTTP_200_OK)

        except AttributeError:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Error 404 ,sub_subject  no found',
            }, status=status.HTTP_404_NOT_FOUND)


class SubSubjectIsBlockApi(APIView):
    """
    Put:
        API for Update SubSubject set is_block=True where status=True
    """
    permission = (Permission.objects.filter(codename='delete_sub_subject'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'GET': group,
        'PUT': group,
        'POST': group

    }

    def get_object(self, id):
        try:
            return Subsubject.objects.get(id=id, status=True)
        except Subsubject.DoesNotExist:
            raise NotFound(detail="Error 404 ,sub_subject not found", code=404)

    def put(self, request, id):
        try:
            sub_subject_obj = self.get_object(id)
            if sub_subject_obj.is_block:
                sub_subject_obj.is_block = False
            else:
                sub_subject_obj.is_block = True
            sub_subject_obj.updated_on = timezone.now()

            sub_subject_obj.save()

            return Response({
                'status': status.HTTP_201_CREATED,
                'message': 'Sub-Subject updated successfully',
                'is_block': sub_subject_obj.is_block
            }, status=status.HTTP_201_CREATED)
        except AttributeError:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Error 404 ,sub-subject not found',
            }, status=status.HTTP_404_NOT_FOUND)


class SubSubjectDeleteApi(APIView):
    """
    Put:
        API for Delete SubSubject set status=False where status=True
    """
    permission = (Permission.objects.filter(codename='delete_sub_subject'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'GET': group,
        'PUT': group,
        'POST': group

    }

    def get_object(self, id):
        try:
            return Subsubject.objects.get(id=id)
        except Subsubject.DoesNotExist:
            raise NotFound(detail="Error 404 ,sub-subject not found", code=404)

    def put(self, request, id):
        try:
            sub_subject_obj = self.get_object(id)
            sub_subject_obj.status = False

            sub_subject_obj.save()

            return Response({
                'status': status.HTTP_201_CREATED,
                'message': 'Sub-Subject Delete successfully',
            }, status=status.HTTP_201_CREATED)
        except AttributeError:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Error 404 ,sub-subject slug no found',
            }, status=status.HTTP_404_NOT_FOUND)


class TopicCreateApi(APIView):
    """
        Post:
             Create Topic in topic of admin panel
        """
    permission = (Permission.objects.filter(codename='add_topic'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'GET': group,
        'PUT': group,
        'POST': group

    }

    schema = schemas.ManualSchema(fields=[
        coreapi.Field(
            'subject',
            required=True,
            location="form",
            schema=coreschema.Integer(
                description="subject id should be given here(i.e. 1)"
            )
        ),
        coreapi.Field(
            'sub_subject',
            required=True,
            location="form",
            schema=coreschema.Integer(
                description="sub_subject id should be given here(i.e. 1)"
            )
        ),
        coreapi.Field(
            'title',
            required=True,
            location="form",
            schema=coreschema.String(
                description="title name should be given here"
            )
        ),
        coreapi.Field(
            'main_title',
            required=False,
            location="form",
            schema=coreschema.String(
                description="For SEO"
            )
        ),
        coreapi.Field(
            'contents',
            required=False,
            location="form",
            schema=coreschema.String(
                description="in the date time format i.e '2019-04-02 09:14:52"
            )
        ),
        coreapi.Field(
            'slug',
            required=True,
            location="form",
            schema=coreschema.String(
                description="additional files concated with assignments file"
            )
        ),
        # coreapi.Field(
        #     'is_block',
        #     required=False,
        #     location="form",
        #     schema=coreschema.String(
        #         description="additional files concated with assignments file"
        #     )
        # ),
        coreapi.Field(
            'meta_description',
            required=False,
            location="form",
            schema=coreschema.String(
                description="Enter description. For SEO"
            )
        ),
        coreapi.Field(
            'meta_keywords',
            required=False,
            location="form",
            schema=coreschema.String(
                description="For SEO"
            )
        ),
        coreapi.Field(
            'head_script',
            required=False,
            location="form",
            schema=coreschema.String(
                description="For SEO"
            )
        ),

        coreapi.Field(
            'image',
            required=False,
            location="form",
            schema=coreschema.String(
                description="attach the image here"
            )
        ),

    ])

    def post(self, request, format=None):

        serializer = TopicCreateSerializer(data=request.data)
        topic_data = request.data
        topic_image = ''

        if serializer.is_valid():

            serializer.validated_data['slug'] = serializer.validated_data['slug'].lower()
            if 'image' in topic_data:
                rndm = random.randint(100000, 9999999)

                file_name = topic_data['image']
                upload_dir = make_dir(
                    settings.MEDIA_ROOT + settings.CUSTOM_DIRS.get('TOPIC_DIR') + '/' + str(rndm) + '/'
                )

                file_name = file_upload_handler(file_name, upload_dir)

                topic_image = settings.MEDIA_URL + settings.CUSTOM_DIRS.get('TOPIC_DIR') + '/' + str(
                    rndm) + '/' + file_name

                serializer.validated_data['image'] = topic_image

            serializer.validated_data['created_on'] = timezone.datetime.now()
            serializer.validated_data['updated_on'] = timezone.datetime.now()

            user_obj = User.objects.get(is_superuser=True)
            # Get user instance for subject Foreignkey
            serializer.validated_data['created_by'] = user_obj
            serializer.validated_data['updated_by'] = user_obj
            create_topic = Topic.objects.create(**serializer.validated_data)#serializer.save()
            return Response({
                'status': status.HTTP_201_CREATED,
                'message': 'topic data saved successfully',
                'data': {'topic_id': create_topic.id}
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TopicUpdateView(APIView):
    schema = schemas.ManualSchema(fields=[
        coreapi.Field(
            'subject',
            required=True,
            location="form",
            schema=coreschema.Integer(
                description="subject id should be given here(i.e. 1)"
            )
        ),
        coreapi.Field(
            'sub_subject',
            required=True,
            location="form",
            schema=coreschema.Integer(
                description="sub_subject id should be given here(i.e. 1)"
            )
        ),
        coreapi.Field(
            'title',
            required=True,
            location="form",
            schema=coreschema.String(
                description="title name should be given here"
            )
        ),
        coreapi.Field(
            'main_title',
            required=False,
            location="form",
            schema=coreschema.String(
                description="For SEO"
            )
        ),
        coreapi.Field(
            'contents',
            required=False,
            location="form",
            schema=coreschema.String(
                description="in the date time format i.e '2019-04-02 09:14:52"
            )
        ),
        coreapi.Field(
            'slug',
            required=False,
            location="form",
            schema=coreschema.String(
                description="additional files concated with assignments file"
            )
        ),
        coreapi.Field(
            'meta_description',
            required=False,
            location="form",
            schema=coreschema.String(
                description="Enter description. For SEO"
            )
        ),
        coreapi.Field(
            'meta_keywords',
            required=False,
            location="form",
            schema=coreschema.String(
                description="For SEO"
            )
        ),
        coreapi.Field(
            'head_script',
            required=False,
            location="form",
            schema=coreschema.String(
                description="For SEO"
            )
        ),
        coreapi.Field(
            'image',
            required=False,
            location="form",
            schema=coreschema.String(
                description="attach the image here"
            )
        ),

    ])

    def get_object(self, id):
        try:
            return Topic.objects.get(id=id)
        except Topic.DoesNotExist:
            return Response(
                {
                    'status': status.HTTP_404_NOT_FOUND,
                    'message': 'Topic not found'
                }
            )

    def put(self, request, id, format=None):
        topic = self.get_object(id)
        serializer = TopicCreateSerializer(topic, data=request.data)
        if serializer.is_valid():
            if 'image' in request.data:
                rndm = random.randint(100000, 9999999)

                file_name = request.data['image']
                upload_dir = make_dir(
                    settings.MEDIA_ROOT + settings.CUSTOM_DIRS.get('TOPIC_DIR') + '/' + str(rndm) + '/'
                )

                file_name = file_upload_handler(file_name, upload_dir)

                country_image = settings.MEDIA_URL + settings.CUSTOM_DIRS.get('TOPIC_DIR') + '/' + str(
                    rndm) + '/' + file_name

                serializer.validated_data['image'] = country_image

            serializer.validated_data['slug'] = serializer.validated_data['slug'].lower()
            serializer.validated_data['status'] = True

            serializer.save()
            return Response(
                {
                    'status': status.HTTP_200_OK,
                    'message': 'Topic detail updated'
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TopicListApi(APIView):
    """
    Get :
         API for List of a Topic.
    """
    permission = (Permission.objects.filter(codename='list_topic'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'GET': group,
        'PUT': group,
        'POST': group

    }

    def get_object(self, slug):
        try:
            return Subsubject.objects.get(slug=slug)
        except Subsubject.DoesNotExist:
            raise NotFound(detail="Error 404 ,topic_slug  not found", code=404)

    def get(self, request, slug):
        try:

            qs = self.get_object(slug)
            queryset = Topic.objects.filter(sub_subject=qs)

            # queryset = self.get_object(slug)
            serializer = TopicListSerializer(queryset, many=True)
            return Response({
                'status': status.HTTP_200_OK,
                'message': 'Topic List fetched',
                'data': serializer.data
            }, status=status.HTTP_200_OK)

        except AttributeError:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Error 404 ,topic  not found',
            }, status=status.HTTP_404_NOT_FOUND)


class TopicDetailApi(APIView):
    """
    Get:
        API for Detail of a Topic.
    """
    permission = (Permission.objects.filter(codename='view_topic'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'GET': group,
        'PUT': group,
        'POST': group

    }

    def get_object(self, id):
        try:
            return Topic.objects.get(id=id)
        except Topic.DoesNotExist:
            raise NotFound(detail="Error 404 ,topic_slug not found", code=404)

    def get(self, request, id):
        try:
            queryset = self.get_object(id)

            serializer = TopicDetailSerializer(queryset)
            return Response({
                'status': status.HTTP_200_OK,
                'message': 'Topic Detail fetched',
                'data': serializer.data,
            }, status=status.HTTP_200_OK)

        except AttributeError:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Error 404 ,topic  no found',
            }, status=status.HTTP_404_NOT_FOUND)


class TopicIsBlockApi(APIView):
    """
    Put:
        API for Update Topic set is_block=True where status=True
    """
    permission = (Permission.objects.filter(codename='delete_topic'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'GET': group,
        'PUT': group,
        'POST': group

    }

    def get_object(self, id):
        try:
            return Topic.objects.get(id=id, status=True)
        except Topic.DoesNotExist:
            raise NotFound(detail="Error 404 ,topic not found", code=404)

    def put(self, request, id):
        try:
            topic_obj = self.get_object(id)
            if topic_obj.is_block:
                topic_obj.is_block = False
            else:
                topic_obj.is_block = True
            topic_obj.updated_on = timezone.now()

            topic_obj.save()

            return Response({
                'status': status.HTTP_201_CREATED,
                'message': 'Topic updated successfully',
                'is_block': topic_obj.is_block
            }, status=status.HTTP_201_CREATED)
        except AttributeError:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Error 404 ,topic not found',
            }, status=status.HTTP_404_NOT_FOUND)


class TopicDeleteApi(APIView):
    """
    Put:
        API for Delete topic set status=False where status=True
    """
    permission = (Permission.objects.filter(codename='delete_topic'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'GET': group,
        'PUT': group,
        'POST': group

    }

    def get_object(self, id):
        try:
            return Topic.objects.get(id=id)
        except Topic.DoesNotExist:
            raise NotFound(detail="Error 404 ,topic not found", code=404)

    def put(self, request, id):
        try:
            topic_obj = self.get_object(id)
            topic_obj.status = False

            topic_obj.save()

            return Response({
                'status': status.HTTP_201_CREATED,
                'message': ' Topic Delete successfully',
            }, status=status.HTTP_201_CREATED)
        except AttributeError:
            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Error 404 ,topic not found',
            }, status=status.HTTP_404_NOT_FOUND)
