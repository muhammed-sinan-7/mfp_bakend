from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.ai.services.post_service import PostService
from apps.ai.services.llm_service import AIService


class AITestView(APIView):
    
    def post(self,request):
        prompt = request.data.get("message","Say Hello From MFP")
        ai_service = AIService()
        result = ai_service.generate(prompt)
        
        return Response({"response":result},
                        status=status.HTTP_200_OK)
        
        
class GeneratePostView(APIView):
    def post(self,request):
        topic = request.data.get("topic")
        platform = request.data.get("platform")
        tone = request.data.get("tone")
        audience = request.data.get("audience")
        additional_context = request.data.get('additional_context',"")
        
        service = PostService()
        
        result = service.generate_post(
            topic,
            platform,
            tone,
            audience,
            additional_context
        )
        
        return Response(result, status=status.HTTP_200_OK)