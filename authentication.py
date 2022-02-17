from django.db.models import Q
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from apps.users.models import User, LoginLog, ExpertProfile, ExpertSubject, Address, ModeratorProfile, UserActivityLog
from rest_framework import status as http_status_codes
from libraries import jwt_helper
from django.utils import timezone
import coreapi
import coreschema
from rest_framework.exceptions import NotFound
from rest_framework import schemas, permissions, status
from rest_framework.exceptions import ValidationError
from libraries.Email_model import send_auth_email
from libraries.Email_templates import welcome_email
from api.v1.admin_serializers.authentication import UserCreateSerializer, ExpertListSerializer, \
    ExpertProfileSerializer, ModeratorListSerializer, ExpertSubjectSerializer, ExpertDetailsSerializer, \
    ModeratorUpdateSerilaizer, UserActivitySerializer
from django.contrib.auth.models import Group
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status as status_code, status
import json
from libraries.Functions import get_unique_id
from libraries.Email_templates import adminusr_resetpwd_emailcontent
from django.contrib.auth.hashers import make_password
from rest_framework.generics import get_object_or_404


class UserCreateApiView(APIView):
    """
        post:
            API for Sign Up / Registration
        """

    # Parameter description for API documentation starts here
    schema = schemas.ManualSchema(fields=[
        coreapi.Field(
            "name",
            required=True,
            location="form",
            schema=coreschema.String(
                description="User's full name must be in valid alphabet with 3-40 characters long"
            )
        ),
        coreapi.Field(
            "email",
            required=True,
            location="form",
            schema=coreschema.String(
                description="Enter a valid email id"
            )
        ),
        coreapi.Field(
            "mobile",
            required=True,
            location="form",
            schema=coreschema.String(
                description="must with country code separated with space. Ex: +12 1234567890"
            )
        ),
        coreapi.Field(
            "group",
            required=True,
            location="form",
            schema=coreschema.String(
                description="Group name i.e expert or moderator"
            )

        ),
        coreapi.Field(
            "gender",
            required=True,
            location="form",
            schema=coreschema.String(
                description="gende i.e male or female"
            )
        ),
        coreapi.Field(
            "dob",
            required=True,
            location="form",
            schema=coreschema.String(
                description="date i.e 2018-02-02/yyyy-mm-dd"
            )
        ),
        coreapi.Field(
            "address",
            required=True,
            location="form",
            schema=coreschema.String(
                description=""
            )
        ),
        coreapi.Field(
            "pincode",
            required=True,
            location="form",
            schema=coreschema.Integer(
                description=""
            )
        ),
        coreapi.Field(
            "is_active",
            required=True,
            location="form",
            schema=coreschema.Integer(
                description="1/0"
            )
        ),
    ])

    def post(self, request):
        context = request.data
        new_user = UserCreateSerializer(data=request.data, context=context)
        if new_user.is_valid():
            print(request.data)
            if request.user.is_superuser:

                try:
                    new_user.save()

                    created_user = new_user.data
                    created_user = User.objects.get(email=created_user['email'])

                    return Response(
                        {
                            'message': 'User Succesfully created and detail has been mailed to his/her mail id',
                            # getting token for authenticated user
                            'status': http_status_codes.HTTP_201_CREATED,
                            'role': context['group'],
                            'user_id': created_user.id,
                            'email': created_user.email

                        },
                        status=http_status_codes.HTTP_201_CREATED)

                except Exception as e:
                    print('******ERROR************')
                    print(e)
                    print(str(e))
                    return Response(
                        {
                            'message': 'Server error.',
                            'data': {}
                        },
                        status=http_status_codes.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response(
                    {
                        'message': 'permission error',
                        'status': http_status_codes.HTTP_403_FORBIDDEN
                    },
                    status=http_status_codes.HTTP_403_FORBIDDEN
                )

        tmp_errors = {key: new_user.errors[key][0] for key in new_user.errors}

        return Response(
            {
                'message': 'error',
                'error': tmp_errors,
                'data': {}
            },
            status=http_status_codes.HTTP_400_BAD_REQUEST)


class LoginApiView(APIView):
    """
    post:
        API for Login/Sin In
    """

    # Parameter description for API documentation starts here
    schema = schemas.ManualSchema(fields=[
        coreapi.Field(
            "email",
            required=True,
            location="form",
            schema=coreschema.String(
                description=""
            )
        ),
        coreapi.Field(
            "password",
            required=True,
            location="form",
            schema=coreschema.String(
                description=""
            )
        )
    ])

    # Parameter description for API documentation ends here

    def post(self, request):
        username = request.data.get('email', None)
        password = request.data.get('password', None)
        if username and password:
            try:
                user = authenticate(username=username, password=password)
                if user and user.is_staff and user.is_active:
                    user.last_login = timezone.now()
                    user.save()

                    auth_user_log = LoginLog()
                    auth_user_log.login_time = timezone.now()
                    auth_user_log.user = user
                    auth_user_log.save()
                    user_detail = {'username': user.username, 'password': password}
                    permission_list = []
                    permissions = (user.groups.all()[0].permissions.all())
                    for permission in permissions:
                        permission_list.append(permission.codename)

                    return Response(
                        {
                            'status': http_status_codes.HTTP_200_OK,
                            'message': 'You have been successfully logged in',
                            'data': {
                                'username': user.username,
                                'email': user.email,
                                'name': user.name,
                                'role': user.groups.all()[0].name,
                                'permission': json.dumps(permission_list)

                            },
                            'token': jwt_helper.get_my_token(user_detail)
                        },
                        status=http_status_codes.HTTP_200_OK)
                elif user and user.is_active:
                    return Response(
                        {
                            'message': 'you dont have permission',
                            'status': http_status_codes.HTTP_403_FORBIDDEN
                        },
                        status=http_status_codes.HTTP_401_UNAUTHORIZED)
                else:
                    return Response(
                        {
                            'message': 'unauthorised',
                            'status': http_status_codes.HTTP_401_UNAUTHORIZED
                        },
                        status=http_status_codes.HTTP_401_UNAUTHORIZED
                    )
            except Exception as e:

                return Response(
                    {
                        'message': 'Server error.',
                        'data': {}
                    },
                    status=http_status_codes.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(
                {
                    'message': 'email and password are required fields',
                    'data': {}
                },
                status=http_status_codes.HTTP_400_BAD_REQUEST)


class ExpertListApi(APIView):
    """
    Returns the list of all experts
    """

    def get(self, request):
        queryset = User.objects.filter(groups__name='expert')
        serializer = ExpertListSerializer(queryset, many=True)
        return Response(
            {
                'status': status.HTTP_200_OK,
                'message': 'expert List fetched',
                'data': serializer.data
            },
            status=status.HTTP_200_OK
        )


class ExpertProfileApi(APIView):
    schema = schemas.ManualSchema(fields=[
        coreapi.Field(
            "id",
            required=True,
            location="form",
            schema=coreschema.String(
                description="User ID for expert"
            )
        ),

        coreapi.Field(
            "highest_qualification",
            required=True,
            location="form",
            schema=coreschema.String(
                description="i.e M.tech"
            )
        ),
        coreapi.Field(
            "passing_year",
            required=True,
            location="form",
            schema=coreschema.Integer(
                description="passing year"
            )
        ),
        coreapi.Field(
            "college",
            required=True,
            location="form",
            schema=coreschema.String(
                description="college name"
            )
        ),
        coreapi.Field(
            "per_page_cost",
            required=True,
            location="form",
            schema=coreschema.String(
                description="i.e. 150"
            )

        ),

        coreapi.Field(
            "subject",
            required=True,
            location="form",
            schema=coreschema.String(
                description="subject id seperated by comma"
            )
        ),
        coreapi.Field(
            "experience",
            required=True,
            location="form",
            schema=coreschema.String(
                description="experience in years"
            )
        ),
        coreapi.Field(
            "working",
            required=True,
            location="form",
            schema=coreschema.String(
                description="True or False"
            )
        ),
    ]
    )

    def post(self, request, format=None):
        """
            Post Api for profile upadate of expert by admin
            """
        user = User.objects.get(id=request.data['id'])

        subject = ','.join(map(str, request.data['subject']))
        subject = subject.split(",")
        serializer = ExpertProfileSerializer(user, data=request.data)
        if serializer.is_valid():
            """
           checking if the user is expert or not
             """
            try:
                expert = ExpertProfile.objects.filter(user=user)
            except ObjectDoesNotExist:
                raise NotFound(detail='expert profile not available', code=404)
            try:
                """
                  updating the subject of expert
                  """
                expert_subject = ExpertSubject.objects.filter(expert=expert[0])
                expert_subject.delete()
                for subject in subject:
                    ExpertSubject.objects.create(expert=expert[0], subject_id=int(subject))

            except ObjectDoesNotExist:
                for subject in subject:
                    ExpertSubject.objects.create(expert=expert[0], subject_id=int(subject))
            """
            updating the expert profile
            """
            serializer.validated_data.update({"updated_on": timezone.now()})
            expert.update(**serializer.validated_data)
            return Response(
                {
                    'status': status.HTTP_202_ACCEPTED,
                    'message': 'Expert Profile successfully updated'

                },
                status=status.HTTP_202_ACCEPTED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExpertEditApi(APIView):
    schema = schemas.ManualSchema(fields=[
        coreapi.Field(
            "id",
            required=True,
            location="form",
            schema=coreschema.String(
                description="User ID for expert"
            )
        ),
        coreapi.Field(
            "name",
            required=True,
            location="form",
            schema=coreschema.String(
                description="User ID for expert"
            )
        ),
        coreapi.Field(
            "gender",
            required=True,
            location="form",
            schema=coreschema.String(
                description="User ID for expert"
            )
        ),
        coreapi.Field(
            "dob",
            required=True,
            location="form",
            schema=coreschema.String(
                description="User ID for expert"
            )
        ),

        coreapi.Field(
            "highest_qualification",
            required=True,
            location="form",
            schema=coreschema.String(
                description="i.e M.tech"
            )
        ),
        coreapi.Field(
            "passing_year",
            required=True,
            location="form",
            schema=coreschema.Integer(
                description="passing year"
            )
        ),
        coreapi.Field(
            "college",
            required=True,
            location="form",
            schema=coreschema.String(
                description="college name"
            )
        ),
        coreapi.Field(
            "per_page_cost",
            required=True,
            location="form",
            schema=coreschema.String(
                description="i.e. 150"
            )

        ),

        coreapi.Field(
            "subject",
            required=True,
            location="form",
            schema=coreschema.String(
                description="subject id seperated by comma"
            )
        ),
        coreapi.Field(
            "experience",
            required=True,
            location="form",
            schema=coreschema.String(
                description="experience in years"
            )
        ),
        coreapi.Field(
            "working",
            required=True,
            location="form",
            schema=coreschema.String(
                description="True or False"
            )
        ),
        coreapi.Field(
            "address",
            required=True,
            location="form",
            schema=coreschema.String(
                description="True or False"
            )
        ),
        coreapi.Field(
            "pincode",
            required=True,
            location="form",
            schema=coreschema.String(
                description="True or False"
            )
        ),
    ]
    )

    def post(self, request, format=None):
        """
            Post Api for profile upadate of expert by admin
            """
        user = User.objects.get(id=request.data['id'])
        user.name = request.data['name']
        user.gender = request.data['gender']
        user.dob = request.data['dob']
        user.save()

        address = Address.objects.get(user=user)
        address.address_line1 = request.data['address']
        address.pincode = request.data['pincode']
        address.save()

        subject = request.data['subject']
        subject = json.loads(str(subject))
        serializer = ExpertProfileSerializer(user, data=request.data)
        if serializer.is_valid():
            """
           checking if the user is expert or not
             """
            try:
                expert = ExpertProfile.objects.filter(user=user)
            except ObjectDoesNotExist:
                raise NotFound(detail='expert profile not available', code=404)
            try:
                """
                  updating the subject of expert
                  """
                expert_subject = ExpertSubject.objects.filter(expert=expert[0])
                expert_subject.delete()
                for subject in subject:
                    ExpertSubject.objects.create(expert=expert[0], subject_id=int(subject))

            except ObjectDoesNotExist:
                for subject in subject:
                    ExpertSubject.objects.create(expert=expert[0], subject_id=int(subject))
            """
            updating the expert profile
            """
            # for e in ['name', 'gender', 'dob']:
            #     serializer.validated_data.pop(e)
            serializer.validated_data.update({"updated_on": timezone.now()})
            expert.update(**serializer.validated_data)
            return Response(
                {
                    'status': status.HTTP_202_ACCEPTED,
                    'message': 'Expert Profile successfully updated'

                },
                status=status.HTTP_202_ACCEPTED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ModeratorListApi(APIView):
    """
    Returns a List of all available expert.
    """

    def get(self, request):
        queryset = User.objects.filter(groups__name='moderator')
        serializer = ModeratorListSerializer(queryset, many=True)

        return Response(
            {
                'status': status.HTTP_200_OK,
                'message': 'Moderator List fetched',
                'data': serializer.data
            },
            status=status.HTTP_200_OK
        )


class SubjectExpertListApi(APIView):
    """
    post: fetch the list of distinct expert relative to their subjects in case id is given for subject ==0
    return all the active distinct experts.
    """
    schema = schemas.ManualSchema(fields=[
        coreapi.Field(
            "subject",
            required=True,
            location="form",
            schema=coreschema.Integer(
                description="User ID for expert"
            )
        ),

        coreapi.Field(
            "assignment",
            required=True,
            location="form",
            schema=coreschema.String(
                description="id of assignmnet"
            )
        ),
    ]
    )

    def post(self, request):
        context = request.data

        if int(context['subject']) == 0:
            obj = ExpertSubject.objects.all().distinct('expert')

        else:
            obj = ExpertSubject.objects.filter(subject_id=request.data['subject'], expert__user__is_active=True)

        serializer = ExpertSubjectSerializer(obj, many=True, context=context)
        return Response(
            {
                'status': status.HTTP_200_OK,
                'message': 'expert list fetched',
                'data': serializer.data
            },
            status=status.HTTP_200_OK
        )


class ExpertDetail(APIView):

    def get_object(self, id):
        try:
            return User.objects.get(id=id)
        except User.DoesNotExist:
            raise ObjectDoesNotExist

    def get(self, request, id):
        user = self.get_object(id)
        try:
            userserializer = ExpertDetailsSerializer(user)

            return Response(
                {
                    'status': status_code.HTTP_200_OK,
                    'message': 'expert Details Fetched',
                    'data': {
                        'user': userserializer.data
                    }
                },
                status=status_code.HTTP_200_OK
            )
        except AttributeError:
            return Response(
                {
                    'status': status.HTTP_404_NOT_FOUND,
                    'message': 'not found',
                },
                status=status.HTTP_404_NOT_FOUND
            )


class ModeratorEditApi(APIView):
    schema = schemas.ManualSchema(fields=[
        coreapi.Field(
            "id",
            required=True,
            location="form",
            schema=coreschema.String(
                description="User ID for expert"
            )
        ),
        coreapi.Field(
            "name",
            required=True,
            location="form",
            schema=coreschema.String(
                description="User ID for expert"
            )
        ),
        coreapi.Field(
            "gender",
            required=True,
            location="form",
            schema=coreschema.String(
                description="User ID for expert"
            )
        ),
        coreapi.Field(
            "mobile",
            required=True,
            location="form",
            schema=coreschema.String(
                description="User ID for expert"
            )
        ),
        coreapi.Field(
            "dob",
            required=True,
            location="form",
            schema=coreschema.String(
                description="User ID for expert"
            )
        ),

        coreapi.Field(
            "address",
            required=True,
            location="form",
            schema=coreschema.String(
                description="True or False"
            )
        ),
        coreapi.Field(
            "pincode",
            required=True,
            location="form",
            schema=coreschema.String(
                description="True or False"
            )
        ),
        coreapi.Field(
            "employee_code",
            required=True,
            location="form",
            schema=coreschema.String(
                description="True or False"
            )
        ),

    ]
    )

    def post(self, request, format=None):
        """
            Post Api for profile upadate of expert by admin
            """
        user = User.objects.filter(id=request.data['id'])

        address = Address.objects.get(user=user[0])
        address.address_line1 = request.data['address']
        address.pincode = request.data['pincode']
        address.save()
        moderator = ModeratorProfile.objects.get(user=user[0])
        moderator.employee_code = request.data['employee_code']
        moderator.save()

        serializer = ModeratorUpdateSerilaizer(user[0], data=request.data)
        if serializer.is_valid():
            """
           checking if the user is expert or not
             """
            serializer.validated_data.update({"updated_on": timezone.now()})
            user.update(**serializer.validated_data)
            return Response(
                {
                    'status': status.HTTP_202_ACCEPTED,
                    'message': 'moderator Profile successfully updated'

                },
                status=status.HTTP_202_ACCEPTED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ModeratorDelete(APIView):

    def post(self, request, id):
        user = User.objects.get(id=id, groups__name='moderator')
        if user.is_active:
            user.is_active = False
        else:
            user.is_active = True
        user.updated_on = timezone.now()
        user.save()
        return Response(
            {
                'status': status.HTTP_200_OK,
                'message': 'moderator status updated',
                'is_active': user.is_active
            },
            status=status.HTTP_200_OK
        )


class ModeratorDetailApi(APIView):
    """
    Returns a List of all available expert.
    """

    def get(self, request, id):
        moderator = User.objects.get(groups__name='moderator', id=id)
        serializer = ModeratorListSerializer(moderator)

        return Response(
            {
                'status': status.HTTP_200_OK,
                'message': 'Moderator detail fetched',
                'data': serializer.data
            },
            status=status.HTTP_200_OK
        )


class AdminForgotPasswordApi(APIView):
    """
    post:
        API for send email for forgot password for admin users.
    """

    schema = schemas.ManualSchema(
        fields=[
            coreapi.Field(
                'email',
                required=True,
                location="form",
                schema=coreschema.String(
                    description="Enter registered email here"
                )
            )
        ]
    )

    def post(self, request):
        data = request.data
        email = data.get("email", None)
        if not email:
            return Response(
                {
                    "statu":http_status_codes.HTTP_400_BAD_REQUEST,
                    "message": "Email parameter is required"
                }, status=http_status_codes.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=email)

        if len(user) == 0:
            return Response(
                {
                    'status': http_status_codes.HTTP_400_BAD_REQUEST,
                    "message": "User not found with this email id"
                }, status=http_status_codes.HTTP_400_BAD_REQUEST)

        user = user[0]
        pwd_reset_token = str(get_unique_id(user.id)).replace("-","")
        user.password_reset_token = pwd_reset_token

        user.save()

        # Send Email
        subject = 'Mentyor: Forgot password link'
        body = adminusr_resetpwd_emailcontent(user, pwd_reset_token, 'localhost')
        received_user = user.email

        if send_auth_email(subject, body, received_user):
            return Response(
                {
                    "status": http_status_codes.HTTP_200_OK,
                    "message": "Password reset link sent on your registered email id"
                }, status=http_status_codes.HTTP_200_OK)

        return Response(
            {
                "status": http_status_codes.HTTP_400_BAD_REQUEST,
                "message": "Can not send the password reset link on your registered email. Please contact the administrator"
            }, status=http_status_codes.HTTP_400_BAD_REQUEST)


class AdminResetPasswordApi(APIView):
    """
    post:
        API for Reset password for admin users.
    """
    # Parameter Schema start here
    schema = schemas.ManualSchema(
        fields=[
            coreapi.Field(
                'reset_token',
                required=True,
                location="form",
                schema=coreschema.String(
                    description="Enter password reset token here"
                )
            ),
            coreapi.Field(
                'password',
                required=True,
                location="form",
                schema=coreschema.String(
                    description="Enter new password here"
                )
            ),
            coreapi.Field(
                'confirm_password',
                required=True,
                location="form",
                schema=coreschema.String(
                    description="Enter confirm here"
                )
            )
        ]
    )
    # Parameter Schema ends here
    def post(self, request):
        data = request.data
        password_reset_token = data.get("reset_token", None)
        print('***Reset token')
        print(password_reset_token)
        new_password = data.get("password", None)
        print('***new password')
        print(new_password)
        confirm_password = data.get("confirm_password", None)
        print('***confirm password')
        print(confirm_password)

        if not password_reset_token or not new_password or not confirm_password:
            return Response(
                {
                    "status": http_status_codes.HTTP_400_BAD_REQUEST,
                    "message":"Password, confirm password and reset token are required fields"
                }, status=http_status_codes.HTTP_400_BAD_REQUEST)

        if new_password != confirm_password:
            return Response(
                {
                    "status": http_status_codes.HTTP_400_BAD_REQUEST,
                    "message": "new password, confirm password must be same"
                }, status=http_status_codes.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(password_reset_token=password_reset_token)

        if len(user)==0:
            return Response(
                {
                    "status": http_status_codes.HTTP_400_BAD_REQUEST,
                    "message": "Invalid password reset token"
                }, status=http_status_codes.HTTP_400_BAD_REQUEST)

        user = user[0]

        user.password = make_password(new_password)
        user.password_reset_token = None

        user.save()

        return Response(
            {
                "status": http_status_codes.HTTP_200_OK,
                "message": "Password has been reset successfully. Please login to continue"
            }, status=http_status_codes.HTTP_200_OK)


class AdminChangePasswordApi(APIView):
    """
    post:
        API for change password for admin users. Token is required for this API.
    """

    schema = schemas.ManualSchema(
        fields=[
            coreapi.Field(
                'old_password',
                required=True,
                location="form",
                schema=coreschema.String(
                    description="Enter Old Password. Auth token is required for this API"
                )
            ),
            coreapi.Field(
                'new_password',
                required=True,
                location="form",
                schema=coreschema.String(
                    description="Enter New Password"
                )
            ),
            coreapi.Field(
                'confirm_password',
                required=True,
                location="form",
                schema=coreschema.String(
                    description="Enter Confirm Password"
                )
            )
        ]
    )

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        email = request.user.email

        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        if old_password and new_password and confirm_password:
            user = User.objects.get(email=email)
            if user.check_password(old_password):
                if len(new_password) >= 8 and len(new_password) <=45:
                    if new_password == confirm_password:
                        user.password = make_password(new_password)
                        user.save()
                        return Response(
                            {
                                'status': http_status_codes.HTTP_200_OK,
                                'message': 'Password has been changed. Go for logout and login again.'
                            },
                            status=http_status_codes.HTTP_200_OK)
                    else:
                        return Response(
                            {
                                'status': http_status_codes.HTTP_400_BAD_REQUEST,
                                'message': 'New password and confirm password does not match'
                            }, status=http_status_codes.HTTP_400_BAD_REQUEST)
                else:
                    return Response(
                        {
                            'status': http_status_codes.HTTP_400_BAD_REQUEST,
                            'message': 'New password must be between 8 to 45 characters long'
                        }, status=http_status_codes.HTTP_400_BAD_REQUEST)
            else:
                return Response(
                    {
                        'status': http_status_codes.HTTP_400_BAD_REQUEST,
                        'message': 'Invalid old password'
                    }, status=http_status_codes.HTTP_400_BAD_REQUEST)
        else:
            return Response(
                {
                    'status': http_status_codes.HTTP_400_BAD_REQUEST,
                    'message': 'old password, new password and confirm password are required fields'
                }, status=http_status_codes.HTTP_400_BAD_REQUEST)


class UserActivityLogAPI(APIView):
    """
        post:
            API for get activity log of a user.
        """

    schema = schemas.ManualSchema(
        fields=[
            coreapi.Field(
                'user_id',
                required=True,
                location="form",
                schema=coreschema.String(
                    description="Enter user ID"
                )
            )
        ]
    )

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        user = get_object_or_404(User, id=request.data['user_id'])
        queryset = user.activity_logs.all()
        serializer = UserActivitySerializer(queryset, many=True)

        return Response(
            {
                'status': status.HTTP_200_OK,
                'message': 'Data fetched',
                'data': serializer.data
            }
        )
