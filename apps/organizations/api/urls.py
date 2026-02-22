from django.urls import path
from .views import (
    CreateOrganizationView,
    ListMembersView,
    ChangeRoleView,
    DeleteOrganizationView,
    RemoveMemberView,
    TransferOwnershipView,
)

urlpatterns = [
    
    path("create/", CreateOrganizationView.as_view(), name="create-organization"),
    path("delete/", DeleteOrganizationView.as_view(), name="delete-organization"),

    
    path("members/", ListMembersView.as_view(), name="list-members"),
    path("members/<uuid:member_id>/remove/", RemoveMemberView.as_view(), name="remove-member"),
    path("members/<uuid:member_id>/change-role/", ChangeRoleView.as_view(), name="change-role"),
    path("members/<uuid:member_id>/transfer-ownership/", TransferOwnershipView.as_view(), name="transfer-ownership"),
]