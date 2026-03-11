from . import instagram, youtube, linkedin


FETCHERS = {
    "instagram": instagram.fetch,
    "meta":instagram.fetch,
    "youtube": youtube.fetch,
    "linkedin": linkedin.fetch,
}