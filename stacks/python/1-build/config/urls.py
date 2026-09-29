from django.urls import path

from conduit.api import api

urlpatterns = [path("", api.urls)]
