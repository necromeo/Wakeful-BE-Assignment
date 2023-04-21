import phonenumbers
from django.core.exceptions import ValidationError


def phone_validator(value):
    try:
        number = phonenumbers.parse(value)
    except phonenumbers.NumberParseException as e:
        raise ValidationError(e) from e
    if not phonenumbers.is_possible_number(number) or not phonenumbers.is_valid_number(
        number
    ):
        raise ValidationError("Invalid phone number")
