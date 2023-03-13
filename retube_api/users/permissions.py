from rest_framework import permissions

SAFE_METHODS = ['POST']

class IsOwner(permissions.BasePermission):
    def has_object_permissions(self, request, view, obj):
        if request.method in SAFE_METHODS or obj.owner == request.user:
            return True
        return obj.owner == request.user