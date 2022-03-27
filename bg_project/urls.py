"""bg_project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
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
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from bg_project.apps.boardgames.views import index
from bg_project.apps.users.views import UsersWishlistView, add_to_remove_from_wishlist, ProfileDetailView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('bg_project.apps.users.urls')),
    path('games/', include('bg_project.apps.boardgames.urls')),
    path('wishlist/', UsersWishlistView.as_view(), name="wishlist"),
    path('add-to-wl/<alias>', add_to_remove_from_wishlist, name="wl_adding"),
    path('profile/<int:user_id>/', ProfileDetailView.as_view(), name="profile_detail"),
    path('', index, name="index"),
]

# Для доступа к медиа в режиме DEBUG нужно отдельно прописать urls для обработки путей файлов
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
