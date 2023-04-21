from django.contrib.auth import authenticate
from rest_framework.request import Request
from trench.exceptions import UnauthenticatedError

# from django.contrib.auth.models import User
from users.models import CustomUser as User


class AuthenticateUserCommand:
    @staticmethod
    def execute(request: Request, email: str, password: str) -> User:
        user = authenticate(
            request=request,
            email=email,
            password=password,
        )
        if user is None:
            raise UnauthenticatedError()
        return user


authenticate_user_command = AuthenticateUserCommand.execute
