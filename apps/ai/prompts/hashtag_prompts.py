
HASHTAG_PROMPT = """
You are a social media strategist.

Generate hashtags for the following post.

Content: {content}
Industry: {industry}
Platform: {platform}

Return JSON format:

{{
 "trending": [],
 "niche": [],
 "broad": []
}}

Return ONLY valid JSON.
"""