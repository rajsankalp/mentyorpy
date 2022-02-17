from rest_framework.response import Response
from rest_framework.views import APIView
from apps.common import models as common_models
from apps.users import models as user_models
from apps.assignment import models as assignment_models
from apps.payment import models as payment_models
from apps.country import models as country_models
from apps.topic import models as topic_models
from apps.tutoring import models as tutoring_models
from api.v1.admin_serializers import dashboard_chart_serializer as chart_serializers
from config import settings
from django.db.models import Count
from rest_framework import status


class AssignmentPieChartData(APIView):
    """
    get:
        API for getting assignment count with assignment_status for making a pie chard on admin dashboard
    """

    def get(self, request):
        data = assignment_models.Assignment.objects.all().values('assignment_status').annotate(
            total_count=Count('assignment_status'))

        total_count = assignment_models.Assignment.objects.all().count()
        # print('************TOTAL******************')
        # print(total_count)

        return Response(
            {
                'status': status.HTTP_200_OK,
                'message': 'data fetched.',
                'data': {'total_count': total_count, 'seperate_data': data}
            }
        )
