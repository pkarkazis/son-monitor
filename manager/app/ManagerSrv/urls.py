"""
Copyright (c) 2015 SONATA-NFV [, ANY ADDITIONAL AFFILIATION]
ALL RIGHTS RESERVED.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Neither the name of the SONATA-NFV [, ANY ADDITIONAL AFFILIATION]
nor the names of its contributors may be used to endorse or promote 
products derived from this software without specific prior written 
permission.

This work has been performed in the framework of the SONATA project,
funded by the European Commission under Grant number 671517 through 
the Horizon 2020 and 5G-PPP programmes. The authors would like to 
acknowledge the contributions of their colleagues of the SONATA 
partner consortium (www.sonata-nfv.eu).
"""

from django.conf.urls import url
from django.contrib import admin
from django.conf.urls import include
from rest_framework import routers
from usersMng import views
from api.urls import internal_apis
from api.urls import public_apis_v1, public_apis_v2

#router = routers.DefaultRouter()
#router.register(r'users', views.UserViewSet)
#router.register(r'groups', views.GroupViewSet)


urlpatterns = [
    url(r'^docs/', include('rest_framework_swagger.urls')),
    url(r'^', include(public_apis_v1, namespace='public_apis')),
    url(r'^', include(public_apis_v2, namespace='public_apis_v2')),
    url(r'^', include(internal_apis, namespace='internal_apis')),
]