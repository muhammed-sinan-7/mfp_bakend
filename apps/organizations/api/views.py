from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db import transaction
from apps.industries.models import Industry
from apps.organizations.models import Organization, OrganizationMember
from .serializers import OrganizationCreateSerializer
from apps.industries.api.serializers import IndustrySerializer






class CreateOrganizationView(APIView):
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self,request):
        user = request.user
        
        if OrganizationMember.objects.filter(user=user).exists():
            return Response({
                "error":"User already belongs to an organization."
            },status=status.HTTP_400_BAD_REQUEST)
            
        serializer = OrganizationCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        organization = serializer.save()
        
        OrganizationMember.objects.create(
            organization=organization,
            user=user,
            role="OWNER"
            
        )
        
        return Response({
            "message":"Organization created successfully",
            "organization_id":organization.id
        },status=status.HTTP_201_CREATED)