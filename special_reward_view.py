from rest_framework.response import Response
from apps.users.models import SpecialReward, User, UserWalletLog, MentyorWallet
from rest_framework.views import APIView
from api.v1.admin_serializers.special_reward_serializer import SpecialRewardListSerializer
from rest_framework import status, schemas, permissions
import coreschema, coreapi
from django.contrib.auth.models import Permission, Group
from libraries.permission import HasGroupPermission
from django.utils import timezone
from django.db import transaction


class SpecialRewardList(APIView):
    """
    get:
    API for listing of special rewards
    """
    def get(self, request):
        queryset = SpecialReward.objects.filter(status=True)
        serializer = SpecialRewardListSerializer(queryset, many=True)

        return Response(
            {
                'status': status.HTTP_200_OK,
                'message': 'List fetched',
                'data': serializer.data
            }, status=status.HTTP_200_OK
        )


class SpecialRewardCreate(APIView):
    """
    post:
    API for create special reward
    """
    permission_classes = (permissions.IsAuthenticated,)
    permission = (Permission.objects.filter(codename='add_special_reward'))
    group = Group.objects.filter(permissions__in=permission)
    permission_classes = [HasGroupPermission]
    required_groups = {
        'POST': group,

    }

    schema = schemas.ManualSchema(fields=[
        coreapi.Field(
            'email',
            required=True,
            location="form",
            schema=coreschema.String(
                description="Enter Email"
            )
        ),
        coreapi.Field(
            'purpose',
            required=True,
            location="form",
            schema=coreschema.String(
                description="Enter purpose"
            )
        ),
        coreapi.Field(
            'amount',
            required=True,
            location="form",
            schema=coreschema.Number(
                description="enter amount"
            )
        )
    ])

    def post(self, request, format=None):
        requested_data = request.data
        email = requested_data.get('email', None)
        purpose = requested_data.get('purpose', None)
        amount = requested_data.get('amount', None)
        if email and purpose and amount:
            try:
                user = User.objects.get(email=email)
                user_wallet = MentyorWallet.objects.get(user=user)
            except Exception as e:
                return Response(
                    {
                        'status': status.HTTP_400_BAD_REQUEST,
                        'message': 'email not found with any user'
                    }
                )
            with transaction.atomic():
                # creating special reward
                special_reward = SpecialReward.objects.create(
                    user=user,
                    email=email,
                    purpose=purpose,
                    amount=amount,
                    given_by=request.user,
                    created_on=timezone.now(),
                    updated_on=timezone.now()
                )

                # update user wallet
                user_wallet.wallet_amount = float(user_wallet.wallet_amount) + float(amount)
                user_wallet.updated_on = timezone.now()
                user_wallet.save()
                # creating user wallet log
                UserWalletLog.objects.create(
                    user=user,
                    amount=amount,
                    is_credited=True,
                    wallet_log_type='Special Reward',
                    wallet_log_for=purpose,
                    created_by=request.user,
                    created_on=timezone.now(),
                    updated_by=request.user,
                    updated_on=timezone.now()
                )
            # TODO Have to send notification and email
            return Response(
                {
                    'status': status.HTTP_201_CREATED,
                    'message': 'Special reward created',
                    'data': {'special_reward_id': special_reward.id}
                }
            )
        else:
            return Response(
                {
                    'status': status.HTTP_400_BAD_REQUEST,
                    'message': 'All fields are required.'
                }
            )
