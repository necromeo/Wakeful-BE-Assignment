from django.urls import path
from users.views import RegisterView, UserView

urlpatterns = [
    path("<int:pk>/", UserView.as_view(), name="users"),
    path("new/", RegisterView.as_view(), name="user_registration"),
]
