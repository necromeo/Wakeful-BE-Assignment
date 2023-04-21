from django.http import JsonResponse
from django.urls import reverse
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny, IsAuthenticated
from users.models import CustomUser
from users.permissions import IsSameUserOrSuperUser
from users.serializers import UpdateUserInfoSerializer

from .serializers import RegisterSerializer


@api_view(["GET"])
def landing(request):
    login = reverse("generate-code-jwt")
    if not request.user.is_authenticated:
        return JsonResponse(
            {"message": f"You are not authenticated. Head over to {login} to log in"},
        )
    return JsonResponse(
        {"message": "You are authenticated"},
    )


class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer


class UserView(generics.RetrieveAPIView, generics.UpdateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = (IsAuthenticated, IsSameUserOrSuperUser)
    serializer_class = UpdateUserInfoSerializer
    lookup_url_kwarg = "pk"
