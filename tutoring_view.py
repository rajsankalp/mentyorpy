from rest_framework.response import Response
from apps.tutoring.models import Tutoring
from apps.users.models import User
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from api.v1.admin_serializers.tutoring_serializer import TutoringListSerializer
from libraries.permission import HasGroupPermission
from django.contrib.auth.models import Permission, Group
from rest_framework.exceptions import NotFound
from django.utils import timezone


class TutoringListApi(APIView):
    """
    get:
    API for list of online tutoring leads
    """
    def get(self, request):
        ordering = request.GET.get('ordering', None)
        search = request.GET.get('search', None)
        queryset = Tutoring.objects.filter(status=True)

        # if search value is available
        if search:
            queryset = queryset.filter(
                Q(user__username__icontains=search) |
                Q(user__name__icontains=search) |
                Q(country__icontains=search) |
                Q(subject__icontains=search) |
                Q(grade__icontains=search)
            )

        # if ordering is available
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
            queryset.order_by('-id')

        paginator = PageNumberPagination()
        result_page = paginator.paginate_queryset(queryset, request)

        serializer = TutoringListSerializer(result_page, many=True)
        s_data = paginator.get_paginated_response(serializer.data)

        return Response(
            {
                'status': status.HTTP_200_OK,
                'message': 'data fetched',
                'search_keys': 'username, name, country, subject, grade',
                'data': s_data.data
            }, status=status.HTTP_200_OK
        )


class TutoringDeleteApi(APIView):
    """
    put:
        Delete a Tutoring Lead set status=False where status=True
    """
    permission = (Permission.objects.filter(codename='delete_tutoring'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'GET': group,
        'PUT': group,
        'POST': group

    }

    def get_object(self, id):
        try:
            return Tutoring.objects.get(id=id, status=True)
        except Tutoring.DoesNotExist:
            raise NotFound(detail="Error 404 ,user id not found", code=404)

    def put(self, request, id):
        try:
            tutoring_obj = self.get_object(id)
            tutoring_obj.status = False
            tutoring_obj.updated_on = timezone.now()

            tutoring_obj.save()

            return Response({
                'status': status.HTTP_200_OK,
                'message': 'Tutoring lead deleted successfully',
            }, status=status.HTTP_200_OK)
        except AttributeError:

            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Tutoring lead not found',
            })


class ApproveTutoringApi(APIView):
    """
    put:
        Delete a Tutoring Lead set is_approved=True where is_approved=False
    """
    permission = (Permission.objects.filter(codename='edit_tutoring'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'GET': group,
        'PUT': group,
        'POST': group

    }

    def get_object(self, id):
        try:
            return Tutoring.objects.get(id=id, status=True, is_approved=False)
        except Tutoring.DoesNotExist:
            raise NotFound(detail="Error 404 ,user id not found", code=404)

    def put(self, request, id):
        try:
            tutoring_obj = self.get_object(id)
            tutoring_obj.is_approved = True
            tutoring_obj.updated_on = timezone.now()

            tutoring_obj.save()
            # TODO have to send email and notification

            return Response({
                'status': status.HTTP_200_OK,
                'message': 'Tutoring lead approved successfully',
            }, status=status.HTTP_200_OK)
        except AttributeError:

            return Response({
                'status': status.HTTP_404_NOT_FOUND,
                'message': 'Tutoring lead not found',
            })
