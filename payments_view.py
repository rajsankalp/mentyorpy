from api.v1.admin_serializers.payments_serializers import OrderHistoryListSerializer, OrderHistoryDetailSerializer
from rest_framework.views import APIView
from apps.payment.models import AssignmentTransaction
from rest_framework.response import Response
from rest_framework import status


class OrderHistoryListAPI(APIView):

    def get(self, request):
        queryset = AssignmentTransaction.objects.all().distinct('assignment')
        serializer = OrderHistoryListSerializer(queryset, many=True)
        return Response(
            {
                'status': status.HTTP_200_OK,
                'message': 'orders history list fetched',
                'data': serializer.data,
            },
            status=status.HTTP_200_OK
        )


class OrderHistoryDetailAPI(APIView):

    def get(self, request, id):

        payment_history_qs = AssignmentTransaction.objects.filter(assignment_id=id)

        if payment_history_qs.count() > 0:
            serializer = OrderHistoryDetailSerializer(payment_history_qs, many=True)

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
                },
                status=status.HTTP_404_NOT_FOUND
            )
