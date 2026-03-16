from rest_framework import serializers


class HashtagGenerateSerializer(serializers.Serializer):
    content = serializers.CharField()
    industry = serializers.CharField()
    platform = serializers.ChoiceField(
        choices=["instagram", "linkedin", "youtube", "twitter"]
    )
    
class CaptionRewriteSerializer(serializers.Serializer):
    caption = serializers.CharField()
    platform = serializers.ChoiceField(
        choices=["instagram", "linkedin", "youtube", "twitter"]
    )
    mode = serializers.ChoiceField(
        choices=["improve", "professional", "engaging", "shorter"]
    )
    
    
class EditPostSerializer(serializers.Serializer):
    original_post = serializers.CharField()
    instruction = serializers.CharField()
    platform = serializers.ChoiceField(
        choices=["instagram", "linkedin", "youtube", "twitter"]
    )