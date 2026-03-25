from rest_framework.permissions import BasePermission


class IsOwnerOrAdmin(BasePermission):
    """Разрешает доступ только владельцу объекта или администратору."""

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'user'):
            return obj.user == request.user or request.user.is_staff
        return obj == request.user or request.user.is_staff