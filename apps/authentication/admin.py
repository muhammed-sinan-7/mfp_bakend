from django.contrib import admin
from .models import OTPToken,User
from apps.organizations.models import Organization,OrganizationInvite,OrganizationMember
from apps.industries.models import Industry
from apps.posts.models import Post,PostPlatformMedia,PostPlatform,PostStatus
from apps.social_accounts.models import SocialAccount,PublishingTarget,MetaPage
# Register your models here.
admin.site.register(OTPToken)
admin.site.register(User)
admin.site.register(Organization)
admin.site.register(OrganizationInvite)
admin.site.register(OrganizationMember)
admin.site.register(Industry)
admin.site.register(Post)
admin.site.register(PostPlatformMedia)
admin.site.register(PostPlatform)
# admin.site.register(PostStatus)
admin.site.register(SocialAccount)
admin.site.register(PublishingTarget)
admin.site.register(MetaPage)