from . models import Profile, Relationship

def profile_pic(request):  # Need to register this to settings.py [inside TEMPLATES -> context_processors]
    if request.user.is_authenticated:
        profile_obj = Profile.objects.get(user=request.user)
        pic = profile_obj.avatar
        return {'picture': pic}
    return {}  # If not authenticated then return empty dictionary.


def invitations_received_no(request):  # Go to settings.py and register this.
    if request.user.is_authenticated:
        profile_obj = Profile.objects.get(user=request.user)
        qs_count = Relationship.objects.invitations_received(profile_obj).count()
        return {'invites_num': qs_count}
    return {}

def logged_in_user_info(request):
    if request.user.is_authenticated:
        user_obj = Profile.objects.get(user=request.user)
        return {'user_obj': user_obj}
    return {}

'''
Create context processors here, then register it settings.py. Then you can use this
wherever you want.
'''