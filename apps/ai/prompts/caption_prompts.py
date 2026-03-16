# apps/ai/prompts/caption_prompts.py

CAPTION_REWRITE_PROMPT = """
Rewrite the following caption.

Caption: {caption}
Platform: {platform}
Mode: {mode}

Rules:
- Keep original meaning
- Improve engagement
- Follow platform style

Return JSON:

{{
 "caption": ""
}}

Return ONLY JSON.
"""