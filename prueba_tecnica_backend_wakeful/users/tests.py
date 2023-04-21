import json

import pyotp
from django.contrib.auth import get_user_model
from django.core import mail
from django.http import HttpResponse
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from rest_framework import status
from trench.models import MFAMethod

from prueba_tecnica_backend_wakeful import settings


def extract_code_from_email():
    return list(filter(None, mail.outbox[0].body.split("\n")))[1]


class AuthenticationCaseUtils(TransactionTestCase):
    def get_access_token(self, email: str, password: str):
        token_request_data: dict[str, str] = {
            "email": email,
            "password": password,
        }
        response = self.client.post(
            reverse("generate-code-jwt"), data=token_request_data
        )
        return json.loads(response.content.decode("utf-8"))

    def get_access_token_email_mfa(self, email: str, password: str) -> HttpResponse:
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        token_request_data: dict[str, str] = {
            "email": email,
            "password": password,
        }
        response = self.client.post(
            reverse("generate-code-jwt"), data=token_request_data
        )

        ephemeral_token: str = response.json().get("ephemeral_token")

        # Get code from email
        # If email template is updated has to be updated as well!
        code: list[str] = extract_code_from_email()

        # Second Step
        response = self.client.post(
            reverse("generate-token-jwt"),
            format="json",
            data={"ephemeral_token": ephemeral_token, "code": code},
        )

        return response

    def get_access_token_app_mfa(self, username: str, password: str):
        # First step
        response = self.client.post(
            reverse("generate-code-jwt"),
            format="json",
            data={"email": username, "password": password},
        )
        response_json = response.json()

        ephemeral_token = response_json.get("ephemeral_token")

        get_user_otp_secret = (
            MFAMethod.objects.filter(user_id=1, name="app").values("secret").first()
        )
        totp = pyotp.TOTP(get_user_otp_secret.get("secret"))

        # Second Step
        response = self.client.post(
            reverse("generate-token-jwt"),
            format="json",
            data={"ephemeral_token": ephemeral_token, "code": totp.now()},
        )

        return response.json()

    def request_email_token(self, auth_headers: dict[str, str]):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

        token_request_data = {"method": "email"}
        self.client.post(
            reverse("mfa-request-code"),
            data=token_request_data,
            **auth_headers,
        )

        # Get code from email
        code: list[str] = list(filter(None, mail.outbox[0].body.split("\n")))[1]

        return code


class TestUserRegistration(TestCase):
    def test_user_creation_endpoint_success(self):
        data = {
            "email": "test@user.com",
            "password": "testpassword",
            "password2": "testpassword",
        }

        response = self.client.post(
            reverse("user_registration"),
            data=data,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_creation_endpoint_no_matching_passwords(self):
        data = {
            "email": "test@user.com",
            "password": "testpassword",
            "password2": "testpasswordz",
        }

        response = self.client.post(
            reverse("user_registration"),
            data=data,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {"password": ["Password fields didn't match."]},
        )

    def test_user_creation_endpoint_invalid_email(self):
        data = {
            "email": "test@user",
            "password": "testpassword",
            "password2": "testpasswordz",
        }

        response = self.client.post(
            reverse("user_registration"),
            data=data,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {"email": ["Enter a valid email address."]},
        )


class TestUsersManagers(TestCase):
    def test_create_user(self):
        User = get_user_model()
        user = User.objects.create_user(
            email="normal@user.com", password="TestPassword"
        )
        self.assertEqual(user.email, "normal@user.com")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        try:
            self.assertIsNone(user.username)
        except AttributeError:
            pass
        with self.assertRaises(TypeError):
            User.objects.create_user()
        with self.assertRaises(ValueError):
            User.objects.create_user(email="")
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password="TestPassword")

    def test_create_superuser(self):
        User = get_user_model()
        admin_user = User.objects.create_superuser(
            email="super@user.com", password="TestPassword"
        )
        self.assertEqual(admin_user.email, "super@user.com")
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        try:
            # username is None for the AbstractUser option
            # username does not exist for the AbstractBaseUser option
            self.assertIsNone(admin_user.username)
        except AttributeError:
            pass
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email="super@user.com", password="TestPassword", is_superuser=False
            )


class TestUserEndpoints(TestCase, AuthenticationCaseUtils):
    fixtures = ["custom_user.json"]

    def test_show_user_info_not_logged_in(self):
        response = self.client.get(reverse("users", kwargs={"pk": 1}))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_show_user_info_not_same_user(self):
        get_token = self.get_access_token("test2@user.com", "TestPassword")
        auth_headers = {"HTTP_AUTHORIZATION": f"Bearer {get_token.get('access')}"}

        response = self.client.get(
            reverse("users", kwargs={"pk": 1}), format="json", **auth_headers
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_show_user_info_not_same_user_if_admin(self):
        get_token = self.get_access_token("test@user.com", "TestPassword")
        auth_headers = {"HTTP_AUTHORIZATION": f"Bearer {get_token.get('access')}"}

        response = self.client.get("/users/2/", format="json", **auth_headers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_show_user_info(self):
        get_token = self.get_access_token("test@user.com", "TestPassword")
        auth_headers = {"HTTP_AUTHORIZATION": f"Bearer {get_token.get('access')}"}

        response = self.client.get(
            reverse("users", kwargs={"pk": 1}), format="json", **auth_headers
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            {
                "email": "test@user.com",
                "first_name": "",
                "last_name": "",
                "birthdate": None,
                "phone": "",
            },
        )

    def test_modify_user_info(self):
        get_token = self.get_access_token("test@user.com", "TestPassword")
        auth_headers = {"HTTP_AUTHORIZATION": f"Bearer {get_token.get('access')}"}

        data = {"first_name": "test", "last_name": "user"}

        response = self.client.put(
            reverse("users", kwargs={"pk": 1}),
            data=data,
            content_type="application/json",
            **auth_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            {
                "email": "test@user.com",
                "first_name": "test",
                "last_name": "user",
                "birthdate": None,
                "phone": "",
            },
        )

    def test_modify_user_info_invalid_date(self):
        get_token = self.get_access_token("test@user.com", "TestPassword")
        auth_headers = {"HTTP_AUTHORIZATION": f"Bearer {get_token.get('access')}"}

        data = {
            "birthdate": "YYYY-m-d",
        }

        response = self.client.put(
            reverse("users", kwargs={"pk": 1}),
            data=data,
            content_type="application/json",
            **auth_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {
                "birthdate": [
                    (
                        "Date has wrong format. Use one of these formats instead: "
                        "YYYY-MM-DD."
                    )
                ]
            },
        )


class TestSettingUpMFA(TestCase, AuthenticationCaseUtils):
    fixtures = ["custom_user.json"]

    def test_set_up_app_mfa(self):
        get_token = self.get_access_token("test@user.com", "TestPassword")
        auth_headers = {"HTTP_AUTHORIZATION": f"Bearer {get_token.get('access')}"}

        # First step

        response = self.client.post(
            reverse("mfa-activate", kwargs={"method": "app"}),
            format="json",
            **auth_headers,
        )
        response_json = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        extract_otp = response_json.get("details").split("=")[1].split("&")[0]

        totp = pyotp.TOTP(extract_otp)

        # Second step
        response = self.client.post(
            reverse("mfa-activate-confirm", kwargs={"method": "app"}),
            format="json",
            **auth_headers,
            data={"code": totp.now()},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("backup_codes", response.json())

    def test_set_up_email_mfa(self):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

        get_token = self.get_access_token("test@user.com", "TestPassword")
        auth_headers = {"HTTP_AUTHORIZATION": f"Bearer {get_token.get('access')}"}

        # First step
        response = self.client.post(
            reverse("mfa-activate", kwargs={"method": "email"}),
            format="json",
            **auth_headers,
        )

        # Get code from email
        code = extract_code_from_email()

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Second step
        response = self.client.post(
            reverse("mfa-activate-confirm", kwargs={"method": "email"}),
            format="json",
            **auth_headers,
            data={"code": code},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("backup_codes", response.json())


class TestLoginWithMFAAppActivated(TestCase):
    fixtures = ["custom_user.json", "user_mfa_app_method.json"]

    def test_two_step_app_login(self):
        # First step
        response = self.client.post(
            reverse("generate-code-jwt"),
            format="json",
            data={"email": "test@user.com", "password": "TestPassword"},
        )
        response_json = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("ephemeral_token", response_json)
        ephemeral_token = response_json.get("ephemeral_token")

        get_user_otp_secret = (
            MFAMethod.objects.filter(user_id=1, name="app").values("secret").first()
        )
        totp = pyotp.TOTP(get_user_otp_secret.get("secret"))

        # Second Step
        response = self.client.post(
            reverse("generate-token-jwt"),
            format="json",
            data={"ephemeral_token": ephemeral_token, "code": totp.now()},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("refresh", response.json())
        self.assertIn("access", response.json())


class TestLoginWithMFAEmailActivated(TestCase, AuthenticationCaseUtils):
    fixtures = ["custom_user.json", "user_mfa_email_method.json"]

    def test_two_step_email_login(self):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

        response = self.get_access_token_email_mfa("test@user.com", "TestPassword")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("refresh", response.json())
        self.assertIn("access", response.json())


class TestChangePrimaryMethod(TestCase, AuthenticationCaseUtils):
    fixtures = ["custom_user.json", "user_mfa_two_methods_email_primary.json"]

    def test_make_app_primary(self):
        """
        The fixture has email as the primary method.
        """
        get_token = self.get_access_token_email_mfa("test@user.com", "TestPassword")
        auth_headers = {
            "HTTP_AUTHORIZATION": f"Bearer {get_token.json().get('access')}"
        }

        # Check the current methods
        response = self.client.get(
            reverse("mfa-list-user-active-methods"),
            format="json",
            **auth_headers,
        )

        response_json = response.json()
        response_json.sort(key=lambda x: x.get("name"))  # type: ignore

        self.assertEqual(response_json[1].get("name"), "email")
        self.assertTrue(response_json[1].get("is_primary"))

        code = self.request_email_token(auth_headers)

        response = self.client.post(
            reverse("mfa-change-primary-method"),
            format="json",
            data={"method": "app", "code": code},
            **auth_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Check the updated methods
        response = self.client.get(
            reverse("mfa-list-user-active-methods"),
            format="json",
            **auth_headers,
        )

        response_json = response.json()
        response_json.sort(key=lambda x: x.get("name"))  # type: ignore

        self.assertEqual(response_json[1].get("name"), "email")
        self.assertFalse(response_json[1].get("is_primary"))


class TestDeactivateMethodEmailIsPrimary(TestCase, AuthenticationCaseUtils):
    fixtures = ["custom_user.json", "user_mfa_two_methods_email_primary.json"]

    def test_deactivate_primary_method(self):
        get_token = self.get_access_token_email_mfa("test@user.com", "TestPassword")
        auth_headers = {
            "HTTP_AUTHORIZATION": f"Bearer {get_token.json().get('access')}"
        }

        # Check the current methods
        response = self.client.get(
            reverse("mfa-list-user-active-methods"), format="json", **auth_headers
        )

        response_json = response.json()
        response_json.sort(key=lambda x: x.get("name"))  # type: ignore

        self.assertEqual(response_json[1].get("name"), "email")
        self.assertTrue(response_json[1].get("is_primary"))

        response = self.client.post(
            reverse("mfa-deactivate", kwargs={"method": "email"}),
            format="json",
            **auth_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {
                "error": "Deactivation of MFA method that is set as primary is not allowed."
            },
        )

    def test_deactivate_secondary_method(self):
        get_token = self.get_access_token_email_mfa("test@user.com", "TestPassword")
        auth_headers = {
            "HTTP_AUTHORIZATION": f"Bearer {get_token.json().get('access')}"
        }

        # Check the current methods
        response = self.client.get(
            reverse("mfa-list-user-active-methods"),
            format="json",
            **auth_headers,
        )

        response_json = response.json()
        response_json.sort(key=lambda x: x.get("name"))  # type: ignore

        self.assertEqual(response_json[1].get("name"), "email")
        self.assertTrue(response_json[1].get("is_primary"))

        response = self.client.post(
            reverse("mfa-deactivate", kwargs={"method": "app"}),
            format="json",
            **auth_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        response = self.client.get(
            reverse("mfa-list-user-active-methods"),
            format="json",
            **auth_headers,
        )

        self.assertEqual(len(response.json()), 1)


class TestDeactivateMethodAppIsPrimary(TestCase, AuthenticationCaseUtils):
    fixtures = ["custom_user.json", "user_mfa_two_methods_app_primary.json"]

    def test_deactivate_primary_method(self):
        get_token = self.get_access_token_app_mfa("test@user.com", "TestPassword")
        auth_headers = {"HTTP_AUTHORIZATION": f"Bearer {get_token.get('access')}"}

        # Check the current methods
        response = self.client.get(
            reverse("mfa-list-user-active-methods"),
            format="json",
            **auth_headers,
        )

        response_json = response.json()
        response_json.sort(key=lambda x: x.get("name"))  # type: ignore

        self.assertEqual(response_json[0].get("name"), "app")
        self.assertTrue(response_json[0].get("is_primary"))

        response = self.client.post(
            reverse("mfa-deactivate", kwargs={"method": "app"}),
            format="json",
            **auth_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {
                "error": "Deactivation of MFA method that is set as primary is not allowed."
            },
        )

    def test_deactivate_secondary_method(self):
        get_token = self.get_access_token_app_mfa("test@user.com", "TestPassword")
        auth_headers = {"HTTP_AUTHORIZATION": f"Bearer {get_token.get('access')}"}

        # Check the current methods
        response = self.client.get(
            reverse("mfa-list-user-active-methods"), format="json", **auth_headers
        )

        response_json = response.json()
        response_json.sort(key=lambda x: x.get("name"))  # type: ignore

        self.assertEqual(response_json[0].get("name"), "app")
        self.assertTrue(response_json[0].get("is_primary"))

        response = self.client.post(
            reverse("mfa-deactivate", kwargs={"method": "email"}),
            format="json",
            **auth_headers,
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        response = self.client.get(
            reverse("mfa-list-user-active-methods"), format="json", **auth_headers
        )

        self.assertEqual(len(response.json()), 1)
