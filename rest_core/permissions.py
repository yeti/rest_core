from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Only the object's owner can view or edit
    Assumes the model instance has a `user` attribute.
    """

    def has_object_permission(self, request, view, obj):
        # Instance must have an attribute named `user`.
        return obj.user == request.user


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Unauthenticated users can still read.
    Assumes the model instance has a `user` attribute.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Instance must have an attribute named `user`.
        return obj.user == request.user


class IsOwnerOrAuthenticatedReadOnly(IsOwnerOrReadOnly, permissions.IsAuthenticated):
    """
    Object-level permission to only allow owners of an object to edit it.
    Unauthenticated users CANNOT read.
    Assumes the model instance has a `user` attribute.
    """
    # TODO: Test this inherits the correct methods from each mixin
    pass
