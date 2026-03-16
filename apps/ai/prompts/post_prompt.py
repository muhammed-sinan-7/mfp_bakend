POST_PROMPT = """
You are a social media strategist.

Generate a {platform} post.

Topic: {topic}
Audience: {audience}
Tone: {tone}

Additional Context:
{additional_context}

Structure the response as JSON with:

headline
caption
hashtags

Caption format:
Hook
Insight
Explanation
Closing

Hashtags must be a list.
"""