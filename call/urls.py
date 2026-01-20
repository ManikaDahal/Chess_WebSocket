from django.urls import path
from . import views

urlpatterns=[
   path("sent-invite/",views.send_invite),
   path("pending-invites/",views.pending_invites),
   path("accept-invite/",views.accept_invite),
   path("api/decline-invite/", views.decline_invite),
]