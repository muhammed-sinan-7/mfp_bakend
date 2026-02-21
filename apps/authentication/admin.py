from django.contrib import admin
from .models import OTPToken,User
from apps.organizations.models import Organization,OrganizationInvite,OrganizationMember
from apps.industries.models import Industry
# Register your models here.
admin.site.register(OTPToken)
admin.site.register(User)
admin.site.register(Organization)
admin.site.register(OrganizationInvite)
admin.site.register(OrganizationMember)
admin.site.register(Industry)