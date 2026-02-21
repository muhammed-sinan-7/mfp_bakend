from django.shortcuts import render
from .serializers import IndustrySerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.industries.models import Industry
from rest_framework.permissions import AllowAny
# Create your views here.
class GetIndustries(APIView):
    permission_classes = [AllowAny]
    def get(self,request):
        industries = Industry.objects.all()
        serializer = IndustrySerializer(industries, many=True)
        return Response(serializer.data)
