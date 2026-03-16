import json
from apps.ai.services.llm_service import AIService
from apps.ai.prompts.post_prompt import POST_PROMPT
import re


class PostService:
    
    def __init__(self):
        self.ai = AIService()
    
    def clean_json(self, text):

        match = re.search(r'\{.*\}', text, re.DOTALL)

        if match:
            return match.group(0)

        return text
        
    def generate_post(self,topic,platform,tone,audience,additional_context=""):
        prompt = POST_PROMPT.format(
            topic=topic,
            platform=platform,
            tone=tone,
            audience=audience,
            additional_context=additional_context
        )
        response = self.ai.generate(prompt)
        try:
            cleaned = self.clean_json(response)
            return json.loads(cleaned)
        except Exception:
            return {
                "headline": "",
                "caption": response,
                "hashtags": []
            }