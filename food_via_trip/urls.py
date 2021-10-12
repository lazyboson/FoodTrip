from django.conf.urls import url
from food_via_trip import views

urlpatterns = [
    url(r'^all-location/$', views.LocationInfoList.as_view(), name='LocationInfoList'),
    url(r'^location/$', views.GenerateLocationInfo.as_view(), name='GenerateLocationInfo'),
    url(r'^fare/(?P<location_id>[0-9a-z-]+)/$', views.PopulateRestaurantWithFare.as_view(),
        name='PopulateRestaurantWithFare'),
]
