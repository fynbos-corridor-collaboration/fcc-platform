from django.conf import settings

def site(request):

    work_offline = False
    try:
        if settings.WORK_OFFLINE:
            work_offline = True
    except:
        work_offline = False
    return {
        "DEBUG": settings.DEBUG,
        "WORK_OFFLINE": True if work_offline else False,
    }
