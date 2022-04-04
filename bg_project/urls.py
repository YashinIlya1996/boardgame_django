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

from rest_framework.urlpatterns import format_suffix_patterns

from bg_project.apps.boardgames import views as boardgames_views
from bg_project.apps.users import views as user_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('test-celery-parse/', boardgames_views.test_celery_downloader),
    path('accounts/', include('bg_project.apps.users.urls')),
    path('games/', include('bg_project.apps.boardgames.urls')),
    path('wishlist/', user_views.UsersWishlistView.as_view(), name="wishlist"),
    path('meets/', user_views.MeetsListView.as_view(), name="meets"),
    path('add-to-wl/<alias>', user_views.add_to_remove_from_wishlist, name="wl_adding"),
    path('profile/<int:user_id>/', user_views.ProfileDetailView.as_view(), name="profile_detail"),
    path('profile/edit/<int:user_id>/', user_views.profile_editing, name="profile_editing"),
    path('profiles-list/', user_views.ProfilesList.as_view(), name="profiles_list"),
    path('friendship-query-send/<int:user_id>/', user_views.send_friendship_query, name="send_friendship_query"),
    path('delete-from-friendlist/<int:user_id>/', user_views.delete_from_friendlist, name="delete_from_friendlist"),
    path('friedship-confirm/<int:user_id>/', user_views.confirm_friendship_query, name="friendship_confirm"),
    path('friendsip-reject/<int:user_id>/', user_views.reject_friendship_query, name="friendship_reject"),
    path('', boardgames_views.index, name="index"),
]

# Добавление urlpatterns для ViewSet BoardGame
urlpatterns += format_suffix_patterns([
    path('api/v0/games/<int:pk>/', boardgames_views.BoardGameViewSet.as_view({'get': 'retrieve'})),
    path('api/v0/games/', boardgames_views.BoardGameViewSet.as_view({'get': 'list'})),
])

# Для доступа к медиа в режиме DEBUG нужно отдельно прописать urls для обработки путей файлов
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
