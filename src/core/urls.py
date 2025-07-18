"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path,include
from django.views.generic.base import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dashboard/',include("dashboard.urls")),
    path('student/',include("student.urls")),
    path('course/',include("course.urls")),
    path('exams/', include(("exam.urls"), namespace="exam")),
    path('invoice/',include("invoice.urls")),
    path('subscription/',include("subscription.urls")),
    path('view/',include("view.urls")),
    path('mobile-app/',include("mobile_app.urls")),
    path('info/',include("info.urls")),
    path('parent/',include("parent.urls")),
    path('notification/',include("notification.urls")),
    path('center/', include("desktop_app.urls")),
    path('teacher/', include("teacher.urls")),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)