from rest_framework import status
from rest_framework.response import Response
from api.v1.admin_serializers.auth_group_serializers import GroupCreateSerializer, PermissionAssignSerializer, \
    PermissionListSerializer, ModelPermissionSerializer
from rest_framework.views import APIView
from django.contrib.auth.models import Permission, Group
from rest_framework.exceptions import NotFound
from django.core.exceptions import ObjectDoesNotExist
import coreapi
import coreschema
from rest_framework import schemas
from libraries.permission import HasGroupPermission
from django.contrib.contenttypes.models import ContentType


class GroupCreateApi(APIView):
    """
        Create a Group for user.
        """
    permission = (Permission.objects.filter(codename='add_group'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'GET': group,
        'PUT': group,
        'POST': group

    }

    schema = schemas.ManualSchema(fields=[
        coreapi.Field(
            "name",
            required=True,
            location="form",
            schema=coreschema.String(
                description="Enter Group name  here"
            )
        ),
    ])

    def post(self, request):
        serializer = GroupCreateSerializer(data=request.data)

        if serializer.is_valid():
            group=Group.objects.create(**serializer.validated_data)
            return Response(
                {
                    'status': status.HTTP_201_CREATED,
                    'message': 'New Group Created.',
                    'group_id':group.id
                }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GroupDetailApi(APIView):
    """
    Retrieve, update or delete a group instance.
    """

    # permission = (Permission.objects.filter(codename='view_group'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'GET': group,
    #     'PUT': group,
    #     'POST': group
    #
    # }

    def get_object(self, pk):
        try:
            return Group.objects.get(pk=pk)
        except Group.DoesNotExist:
            raise NotFound(detail="Error 404 ,faq id not found", code=404)

    def get(self, request, pk, format=None):
        group = self.get_object(pk)
        serializer = GroupCreateSerializer(group)
        return Response(serializer.data)

    def put(self, request, pk, format=None):
        snippet = self.get_object(pk)
        serializer = GroupCreateSerializer(snippet, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, format=None):
        group = self.get_object(pk)
        group.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GroupListApi(APIView):
    """
        list of all group for the user.
        """

    permission = (Permission.objects.filter(codename='list_group'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'GET': group,
        'PUT': group,
        'POST': group

    }

    def get(self, request):
        queryset = Group.objects.all()
        group = Group.objects.get(id=1)
        # permission = (Permission.objects.filter(codename__in=['delete_user', 'view_user', 'add_role', 'change_role']))
        # for permission in permission:
        #     group.permissions.add(permission)
        # print('group', permission)
        serializer = GroupCreateSerializer(queryset, many=True)
        return Response({
            'status': status.HTTP_200_OK,
            'message': 'Group list fetched',
            'data': serializer.data,
        })


class GroupPermissionAssign(APIView):
    """
        Assigning the permissions to different group
        """
    schema = schemas.ManualSchema(fields=[
        coreapi.Field(
            "group_id",
            required=True,
            location="form",
            schema=coreschema.Integer(
                description="Enter Group name  here"
            )
        ),
        coreapi.Field(
            "permissions",
            required=True,
            location="form",
            schema=coreschema.String(
                description="Enter permissions codename here(i.e. view_xyz, edit_xyz"
            )

        )
    ])

    def post(self, request):
        serializers = PermissionAssignSerializer(data=request.data)

        data = request.data
        if serializers.is_valid():
            try:
                perm_list = data['permissions']
                permission = Permission.objects.filter(codename__in=perm_list)
                group = Group.objects.get(id=data['group_id'])
                group.permissions.clear()
                for permission in permission:
                    group.permissions.add(permission)
                return Response(
                    {
                        'status': status.HTTP_200_OK,
                        'message': 'permission assigned'

                    },
                    status=status.HTTP_200_OK
                )

            except ObjectDoesNotExist:
                return Response(
                    {
                        'status': status.HTTP_404_NOT_FOUND,
                        'message': 'permission not found'

                    },
                    status=status.HTTP_404_NOT_FOUND
                )
        print('*******', serializers.errors)
        return Response({
            'status': status.HTTP_400_BAD_REQUEST,
            'message': 'NOT ASSIGNED',

        })


class PermissionListApi(APIView):
    """
        list of all group for the user.
        """

    # permission = (Permission.objects.filter(codename='list_permission'))
    # group = Group.objects.filter(permissions__in=permission)
    # permission_classes = [HasGroupPermission]
    # required_groups = {
    #     'GET': group,
    #     'PUT': group,
    #     'POST': group
    #
    # }

    def get(self, request):
        queryset = Permission.objects.all()
        # print(queryset)
        serializer = PermissionListSerializer(queryset, many=True)
        print(serializer)
        return Response({
            'status': status.HTTP_200_OK,
            'message': 'Group list fetched',
            'data': serializer.data,
        })


class ModelPermission(APIView):
    def get(self, request):
        qs = ContentType.objects.all().exclude(model__in=['contenttype', 'session', 'loginsessionmanager'])
        serializer = ModelPermissionSerializer(qs, many=True)
        return Response(
            {
                'status': status.HTTP_200_OK,
                'data': serializer.data
            },
            status=status.HTTP_200_OK
        )
