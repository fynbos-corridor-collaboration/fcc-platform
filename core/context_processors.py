from django.conf import settings
import random

def site(request):

    work_offline = False
    try:
        if settings.WORK_OFFLINE:
            work_offline = True
    except:
        work_offline = False

    l = [24,26,29,11,9,19,8,34,12,27]
    header_bg = random.choice(l)

    return {
        "DEBUG": settings.DEBUG,
        "WORK_OFFLINE": True if work_offline else False,
        "HEADER_BG": f"/img/bg/{header_bg}.jpg",
        "MAPBOX_API_KEY": "pk.eyJ1IjoiY29tbXVuaXRyZWUiLCJhIjoiY2lzdHZuanl1MDAwODJvcHR1dzU5NHZrbiJ9.0ETJ3fXYJ_biD7R7FiwAEg",
    }
