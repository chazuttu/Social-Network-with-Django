from django.shortcuts import render, redirect, get_object_or_404
from .models import Profile, Relationship
from .forms import ProfileModelForm
from django.views.generic import ListView, DetailView
from django.contrib.auth.models import User
from django.db.models import Q

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
# Create your views here.

@login_required
def my_profile_view(request):
    profile = Profile.objects.get(user=request.user)
    form = ProfileModelForm(request.POST or None, request.FILES or None ,instance=profile)
    confirm = False

    if request.method == 'POST':
        if form.is_valid():
            form.save()
            confirm = True

    context = {
        'profile': profile,
        'form': form,
        'confirm': confirm,
    }
    return render(request, 'profiles/myprofile.html', context)


@login_required
def invites_received_view(request):  # Others user when send me a request.
    profile = Profile.objects.get(user=request.user)
    qs = Relationship.objects.invitations_received(profile)  # Geeting all the invitations for this particular profile. invitations_received function from model Manager.

    results = list(map(lambda x: x.sender, qs)) # To see only the senders. If we pass qs only then we will see the receiver also.
    is_empty = False
    if len(results) == 0:
        is_empty = True
    
    context = {
        'qs': results,
        'is_empty': is_empty,
    }
    return render(request, 'profiles/my_invites.html', context)


@login_required
def accept_invitation(request):
    if request.method == 'POST':
        pk = request.POST.get('profile_pk') # Graving the pk.
        sender = Profile.objects.get(pk=pk) # Get sender by the pk
        receiver = Profile.objects.get(user=request.user)
        rel = get_object_or_404(Relationship, sender=sender, receiver=receiver)
        if rel.status == 'send':
            rel.status = 'accepted'
            rel.save()
    return redirect('profiles:my-invites-view')


@login_required
def reject_invitation(request):
    if request.method == 'POST':
        pk = request.POST.get('profile_pk') # Graving the pk.
        sender = Profile.objects.get(pk=pk)
        receiver = Profile.objects.get(user=request.user)
        rel = get_object_or_404(Relationship, sender=sender, receiver=receiver)
        rel.delete()
    return redirect('profiles:my-invites-view')


@login_required
def invite_profiles_list_view(request): # The list of the profiles whom I can send invites.
    user = request.user
    qs = Profile.objects.get_all_profiles_to_invite(user)

    context = {
        'qs': qs,
    }
    return render(request, 'profiles/to_invite_list.html', context)



# def profiles_list_view(request): # All the profiles.
#     user = request.user
#     qs = Profile.objects.get_all_profiles(user)

#     context = {
#         'qs': qs,
#     }
#     return render(request, 'profiles/profile_list.html', context)



class ProfileListView(LoginRequiredMixin, ListView):
    model = Profile
    template_name = 'profiles/profile_list.html'
    context_object_name = 'qs' # Also we can use object_list as context instead of qs by default.

    def get_queryset(self): # Override the get_queryset method because of we can get what we want.
        qs = Profile.objects.get_all_profiles(self.request.user)
        return qs

    def get_context_data(self, **kwargs): # This method allows us to provide some additional context to the template. 
        context = super().get_context_data(**kwargs)
        user = User.objects.get(username__iexact=self.request.user)   # Grab this user. This should give us each time a user.
        profile = Profile.objects.get(user=user) # Grab the profile once we get the user.
        
        rel_r = Relationship.objects.filter(sender=profile)   # Relationship receiver where we are going to simply query relationships by the sender equal to our profile. Here we are storing relationships where we invited other users to friends. 
        rel_s = Relationship.objects.filter(receiver=profile)  # Relationship sender where we are going to simply query relationships by the receiver equal to our profile.        
        rel_receiver = []
        rel_sender = []
        for item in rel_r:
            rel_receiver.append(item.receiver.user) # receiver is relate to the user.
        for item in rel_s:
            rel_sender.append(item.sender.user)
        context['rel_receiver'] = rel_receiver 
        context['rel_sender'] = rel_sender 
        
        context['is_empty'] = False
        if len(self.get_queryset()) == 0:
            context['is_empty'] = True
        return context


class ProfileDetailView(LoginRequiredMixin, DetailView):
    model = Profile
    template_name = 'profiles/profile_detail.html'
    
    def get_object(self, slug=None):
        slug = self.kwargs.get('slug')
        profile = Profile.objects.get(slug=slug)
        return profile

    def get_context_data(self, **kwargs): # This method allows us to provide some additional context to the template. 
        context = super().get_context_data(**kwargs)
        user = User.objects.get(username__iexact=self.request.user)   # Grab this user. This should give us each time a user.
        profile = Profile.objects.get(user=user) # Grab the profile once we get the user.
        rel_r = Relationship.objects.filter(sender=profile)   # Relationship receiver where we are going to simply query relationships by the sender equal to our profile. Here we are storing relationships where we invited other users to friends. 
        rel_s = Relationship.objects.filter(receiver=profile)  # Relationship sender where we are going to simply query relationships by the receiver equal to our profile.        
        rel_receiver = []
        rel_sender = []
        for item in rel_r:
            rel_receiver.append(item.receiver.user) # receiver is relate to the user.
        for item in rel_s:
            rel_sender.append(item.sender.user)
        context['rel_receiver'] = rel_receiver 
        context['rel_sender'] = rel_sender 
        context['posts'] = self.get_object().get_all_authors_posts()   # Get all the post of this particular profile. get_all_authors_posts from models.py file.
        context['len_posts'] = True if len(self.get_object().get_all_authors_posts()) > 0 else False
        return context


@login_required
def send_invitations(request):
    if request.method == 'POST':
        pk = request.POST.get('profile_pk')  # profile_pk is the name of input field inside the form into html.
        user = request.user
        sender = Profile.objects.get(user=user)
        receiver = Profile.objects.get(pk=pk)

        rel = Relationship.objects.create(sender=sender, receiver=receiver, status='send')
        return redirect(request.META.get('HTTP_REFERER'))
    return redirect('profiles:my-profile-view')


@login_required
def remove_from_friends(request):  # Also write some code in signals.
    if request.method == 'POST':
        pk = request.POST.get('profile_pk')  # profile_pk is the name of input field inside the form into html.
        user = request.user
        sender = Profile.objects.get(user=user)
        receiver = Profile.objects.get(pk=pk)

        rel = Relationship.objects.get(
            (Q(sender=sender) & Q(receiver=receiver)) | (Q(sender=receiver) & Q(receiver=sender))
        )
        rel.delete()
        return redirect(request.META.get('HTTP_REFERER'))
    return redirect('profiles:my-profile-view')