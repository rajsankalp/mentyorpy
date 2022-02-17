from rest_framework.response import Response
from rest_framework.views import APIView
from apps.common.models import PageMedia
from apps.users.models import User
from libraries.Functions import make_dir, upload_page_media_handler
from libraries.permission import HasGroupPermission
from django.contrib.auth.models import Permission, Group
from django.conf import settings
from rest_framework import status
import random
from django.utils import timezone
from api.v1.admin_serializers.page_media_serializer import PageMediaListSerializer
from rest_framework.exceptions import NotFound
from django.db.models import Q
from rest_framework.pagination import PageNumberPagination


class UploadPageMediaAPI(APIView):
    """
    post:
    API for upload media in page-media directory
    """
    permission = (Permission.objects.filter(codename='add_page_media'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'GET': group,
        'PUT': group,
        'POST': group

    }

    def post(self, request):
        requested_data = request.data
        if 'media' not in requested_data:
            return Response(
                {
                    'status': status.HTTP_400_BAD_REQUEST,
                    'message': 'File not found'
                }, status=status.HTTP_400_BAD_REQUEST
            )
        else:
            for file in self.request.data.getlist('media'):
                # rndm = random.randint(100000, 9999999)
                upload_dir = make_dir(
                    settings.MEDIA_ROOT + settings.CUSTOM_DIRS.get('PAGE_MEDIA_DIR') + '/'
                )
                file_name = upload_page_media_handler(file, upload_dir)
                file_url = settings.MEDIA_URL + settings.CUSTOM_DIRS.get(
                    'PAGE_MEDIA_DIR') + '/' + file_name

                # saving file data in database
                save_media = PageMedia.objects.create(
                    file_url=file_url,
                    file_name=file_name,
                    uploaded_on=timezone.now(),
                    uploaded_by=request.user
                )
            return Response(
                {
                    'status': status.HTTP_201_CREATED,
                    'message': 'Media uploaded.'
                }, status=status.HTTP_201_CREATED
            )
        return Response(
            {
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'message': 'Something went wrong. Please try later.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class PageMediaListAPI(APIView):
    """
        get:
        API for get media list from page-media directory
        """
    permission = (Permission.objects.filter(codename='list_page_media'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'GET': group,
        'PUT': group,
        'POST': group

    }

    def get(self, request):
        ordering = request.GET.get('ordering', None)
        search = request.GET.get('search', None)
        print('*****************: ',search)

        queryset = PageMedia.objects.filter(status=True)

        # if search value is available
        if search:
            queryset = queryset.filter(
                Q(file_url__icontains=search) | Q(file_name__icontains=search)
            )

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

        serializer = PageMediaListSerializer(result_page, many=True)
        s_data = paginator.get_paginated_response(serializer.data)

        return Response(
            {
                'status': status.HTTP_200_OK,
                'message': 'Data fetched',
                'data': s_data.data
            }, status=status.HTTP_200_OK
        )


class PageMediaDeleteAPI(APIView):
    """
    put:
        Delete a user set is_active=False where is_active=True
    """
    permission = (Permission.objects.filter(codename='delete_page_media'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'GET': group,
        'PUT': group,
        'POST': group

    }

    def get_object(self, id):
        try:
            return PageMedia.objects.get(id=id, status=True)
        except PageMedia.DoesNotExist:

            raise NotFound(detail="Error 404 ,Media not found", code=404)

    def put(self, request, id):
        try:
            media_obj = self.get_object(id)
            media_obj.status = False

            media_obj.save()

            return Response({
                'status': status.HTTP_200_OK,
                'message': 'Media Deleted successfully'
            }, status=status.HTTP_200_OK)
        except AttributeError:

            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Media not found',
            })

