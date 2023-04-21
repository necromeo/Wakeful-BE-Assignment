from rest_framework.permissions import BasePermission


class IsSameUserOrSuperUser(BasePermission):
    """
    Allows access only if the users match.
    """

    def has_object_permission(self, request, view, obj):
        user_id = request.user.id
        pk = view.kwargs.get(view.lookup_url_kwarg)
        return user_id == pk or request.user.is_superuser
