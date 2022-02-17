from rest_framework.response import Response
from rest_framework import status, schemas, generics
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from apps.common.models import RewardSetting
from api.v1.admin_serializers import reward_setting_serializer as reward_ser
from apps.users.models import User, UserActivityLog
from django.utils import timezone
import coreschema, coreapi


class RewardSettingCreateAPI(APIView):
    """
    post:
    API for create a reward
    """
    def post(self, request):
        serializer = reward_ser.RewardSettingSerializer(data=request.data, partial=True)

        if serializer.is_valid(raise_exception=True):
            serializer.validated_data['created_by_id'] = 1
            saved_data = serializer.save()
            response_data = {'status': status.HTTP_201_CREATED, 'message': 'data created'}
            return Response(response_data, status=status.HTTP_201_CREATED)
        else:
            response_data = {'status': status.HTTP_400_BAD_REQUEST, 'error': serializer.errors}
            return Response(response_data, status=status.HTTP_201_CREATED)


class RewardSettingListAPI(generics.ListAPIView):
    """
    get:
    API for getting list of reward setting
    """
    queryset = RewardSetting.objects.filter(status=True)
    serializer_class = reward_ser.RewardSettingSerializer


class RewardSettingDetailAPI(generics.RetrieveAPIView):
    """
    get:
    API for getting list of reward setting
    """
    queryset = RewardSetting.objects.filter(status=True)
    serializer_class = reward_ser.RewardSettingSerializer


class RewardSettingUpdateAPI(APIView):
    """
    post:
    API for create a reward
    """
    def put(self, request, pk):
        instance = get_object_or_404(RewardSetting, pk=pk)
        serializer = reward_ser.RewardSettingSerializer(instance=instance, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):

            serializer.validated_data['updated_by_id'] = 1
            saved_data = serializer.save()
            saved_data.updated_by_id = 1
            saved_data.save()
            response_data = {'status': status.HTTP_201_CREATED, 'message': 'data updated'}
            return Response(response_data, status=status.HTTP_201_CREATED)
        else:
            response_data = {'status': status.HTTP_400_BAD_REQUEST, 'error': serializer.errors}
            return Response(response_data, status=status.HTTP_201_CREATED)


class RewardSettingDeleteAPI(APIView):
    """
    post:
    API for create a reward
    """
    def delete(self, request, pk):
        instance = get_object_or_404(RewardSetting, pk=pk)
        instance.delete()
        return Response(
            {
                'status': status.HTTP_200_OK,
                'message': 'Row deleted'
            }, status=status.HTTP_200_OK
        )

