from django.db import models
from django.shortcuts import reverse
from django.contrib.auth.models import User

from .utils import get_random_code # For slug field
from django.template.defaultfilters import slugify

from django.db.models import Q
# Create your models here.

'''
Django Model Manager  -- Manager is responsible for the communication with the database 

While creating queryset we use objects as the default model Manager for each model. But we can extended it
very easy to organise our code just a little bit better. We will do it with the help of custom Manager.

With the help of the custom Manager we are going to get invitations received from different users all the
profiles in our system excluding of course ourselves. And finally all the profiles that we can invite to
our friends.

Create RelationshipManager class and in order to have RelationshipManager working need to write 
objects = RelationshipManager() inside Relationship model. Then create views, url and templates for this.


Create ProfileManager class and in order to have ProfileManager working write objects = ProfileManager()
inside Profile model. Then create views, url and templates for this.
'''

class ProfileManager(models.Manager):
    # Get all the profiles whom I can send invites.
    def get_all_profiles_to_invite(self, sender): # sender because we need to know who is the sender.
        profiles = Profile.objects.all().exclude(user=sender)  # sender from Relationship model. And excluding our own.
        profile = Profile.objects.get(user=sender)
        qs = Relationship.objects.filter(Q(sender=profile) | Q(receiver=profile))

        accepted = set([])  # It will take unique and will not take duplicate value/users. For this set, we will use add() instead of append()
        for rel in qs:
            if rel.status == 'accepted':
                accepted.add(rel.receiver) # instead of append() write add() for set in empty list.
                accepted.add(rel.sender)
        print(accepted)

        available = [profile for profile in profiles if profile not in accepted] # List comprehension. List of all the available profile to invite.
        print(available)
        return available

    def get_all_profiles(self, me): # Get all the profiles which are available excluding me.
        profiles = Profile.objects.all().exclude(user=me) # Excluded by user field from Profile model and user is set to me.
        return profiles

class Profile(models.Model):
    first_name = models.CharField(max_length=200, blank=True)
    last_name = models.CharField(max_length=200, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # Every user will have only his own profile.
    bio = models.TextField(default='No bio ....', max_length=300)
    email = models.EmailField(max_length=200, blank=True)
    country = models.CharField(max_length=200, blank=True)
    avatar = models.ImageField(default='avatar.png', upload_to='avatars/') # Create media_root folder within static_cdn. Put a avatar.png within media_root folder.
    friends = models.ManyToManyField(User, blank=True, related_name='friends')
    slug = models.SlugField(unique=True, blank=True)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    objects = ProfileManager()

    def __str__(self):
        # return f'{self.user.username}-{self.created}'
        return f'{self.user.username}-{self.created.strftime("%d-%m-%Y")}'

    def get_absolute_url(self):
        return reverse('profiles:profile-detail-view', kwargs={'slug': self.slug})

    def get_friends(self):
        return self.friends.all()

    def get_friends_no(self):
        return self.friends.all().count()

    def get_posts_no(self):
        return self.posts.all().count()  # posts is the related_name from author field of Post model. Also we can use modelname_set.

    def get_all_authors_posts(self):
        return self.posts.all()

    def get_likes_given_no(self):
        likes = self.like_set.all()  # modelname_set. relationship with post field of like model.
        total_liked = 0
        for item in likes:
            if item.value == 'Like':
                total_liked +=1
        return total_liked

    def get_likes_received_no(self):
        posts = self.posts.all()  # posts is the related_name of author field of Post model.
        total_liked = 0
        for item in posts:
            total_liked += item.liked.all().count()
        return total_liked

    ##--## Slug Start ##--##

    __initial_first_name = None
    __initial_last_name = None
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__initial_first_name = self.first_name
        self.__initial_last_name = self.last_name

    def save(self, *args, **kwargs):  # For random slug field, created get_random_code function into utils.py file.
        ex = False
        to_slug = self.slug
        if self.first_name != self.__initial_first_name or self.last_name != self.__initial_last_name or self.slug == '':
            if self.first_name and self.last_name:
                to_slug = slugify(str(self.first_name) + '' + str(self.last_name))
                ex = Profile.objects.filter(slug=to_slug).exists()
                while ex:
                    to_slug = slugify(to_slug + '' + str(get_random_code()))
                    ex = Profile.objects.filter(slug=to_slug).exists()
            else:
                to_slug = str(self.user)
        self.slug = to_slug
        super().save(*args, **kwargs)
    
    ##--## Slug End ##--##



STATUS_CHOICES = (   # for status field. 
    ('send', 'send'),
    ('accepted', 'accepted'),
)

class RelationshipManager(models.Manager):
    # This will give us all the invitations that we received from different users.
    def invitations_received(self, receiver): # receiver is the ForeignKey(to the Profile) field of Relationship model.
        qs = Relationship.objects.filter(receiver=receiver, status='send') # receiver(first one) that is we pass over here.
        return qs

    # Relationship.objects.invitations_received(myprofile)  # All the relationship received for this particular profile.


class Relationship(models.Model):
    sender = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='sender')
    receiver = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='receiver')
    status = models.CharField(max_length=8, choices=STATUS_CHOICES)
    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    objects = RelationshipManager() # Extends our existing manager.

    def __str__(self):
        return f'{self.sender}-{self.receiver}-{self.status}'

