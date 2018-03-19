"""
Unit tests for completion models
"""
from django.test import TestCase
from django.contrib.auth.models import User
from pod.video.models import Type
from pod.video.models import Video
from pod.completion.models import Contributor

import datetime


class ContributorModelTestCase(TestCase):

    def setUp(self):
        test = User.objects.create(username='test')
        owner = Owner.objects.get(user__username='test')
       	video = Video.objects.create(
       		title='video',
       		owner=owner,
       		video='test.mp4'
       	)
        Contributor.objects.create(
        	video=video,
        	name='contributor',
        	email_address='contributor@pod.com',
        	role='actor',
        	weblink='http://pod.com'
        )
        Contributor.objects.create(
        	video=video,
        	name='contributor2'
        )

