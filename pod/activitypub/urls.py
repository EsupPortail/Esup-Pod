from django.urls import path

from . import views

app_name = "activitypub"


urlpatterns = [
    path(".well-known/nodeinfo", views.nodeinfo, name="nodeinfo"),
    path(".well-known/webfinger", views.webfinger, name="webfinger"),
    path("ap", views.account, name="account"),
    path("ap/account/<str:username>", views.account, name="account"),
    path("ap/inbox", views.inbox, name="inbox"),
    path("ap/account/<str:username>/inbox", views.inbox, name="inbox"),
    path(
        "ap/account/<str:username>/channel",
        views.account_channel,
        name="account_channel",
    ),
    path("ap/outbox", views.outbox, name="outbox"),
    path("ap/account/<str:username>/outbox", views.outbox, name="outbox"),
    path("ap/following", views.following, name="following"),
    path("ap/account/<str:username>/following", views.following, name="following"),
    path("ap/followers", views.followers, name="followers"),
    path("ap/account/<str:username>/followers", views.followers, name="followers"),
    path("ap/video/<id>", views.video, name="video"),
    path("ap/video/<id>/likes", views.likes, name="likes"),
    path("ap/video/<id>/dislikes", views.dislikes, name="dislikes"),
    path("ap/video/<id>/shares", views.shares, name="comments"),
    path("ap/video/<id>/comments", views.comments, name="shares"),
    path("ap/video/<id>/chapters", views.chapters, name="chapters"),
    path("ap/channel/<id>", views.channel, name="channel"),
]

urlpatterns += [
    path("external_video/<slug>", views.external_video, name="external_video"),
]
