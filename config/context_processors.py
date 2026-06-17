from django.conf import settings


def site_settings(request):
    return {
        "SITE_NAME": settings.SITE_NAME,
        "SITE_SUBTITLE": settings.SITE_SUBTITLE,
    }
