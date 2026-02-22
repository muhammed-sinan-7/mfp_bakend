from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from apps.organizations.permissions import HasOrganization, IsOwner
from apps.audit.models import AuditLog
from .serializers import AuditLogSerializer
class AuditLogListView(ListAPIView):
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, HasOrganization, IsOwner]

    def get_queryset(self):
        return AuditLog.objects.filter(
            organization=self.request.organization
        ).select_related("actor")