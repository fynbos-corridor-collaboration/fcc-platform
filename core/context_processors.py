from django.conf import settings
import random

def site(request):

    work_offline = False
    try:
        if settings.WORK_OFFLINE:
            work_offline = True
    except:
        work_offline = False

    header_bg = random.choice(range(0,44))

    return {
        "DEBUG": settings.DEBUG,
        "WORK_OFFLINE": True if work_offline else False,
        "HEADER_BG": f"/img/bg/{header_bg}.jpg",
    }
