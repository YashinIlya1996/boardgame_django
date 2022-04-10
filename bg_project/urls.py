from django.contrib import admin
from django.urls import path, include, register_converter
from django.conf import settings
from django.conf.urls.static import static

from rest_framework.urlpatterns import format_suffix_patterns

from bg_project.apps.boardgames import views as boardgames_views
from bg_project.apps.users import views as user_views
from bg_project.converters import MeetCategory

register_converter(MeetCategory, "meet_category")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('accounts/', include('bg_project.apps.users.urls')),
    path('games/', include('bg_project.apps.boardgames.urls')),
    path('wishlist/', user_views.UsersWishlistView.as_view(), name="wishlist"),
    path('meet/<int:meet_pk>/', user_views.MeetDetail.as_view(), name="meet_detail"),
    path('meets/manage/<int:meet_id>/', user_views.manage_meeting, name="manage_meeting"),
    path('meets/create/', user_views.create_meet, name="create_meet"),
    path('meets/send-request/<int:meet_id>/', user_views.send_meet_request, name="send_meet_request"),
    path('meets/leave-meet/<int:meet_id>/', user_views.leave_meet_and_cancel_meet_request, name="leave_meet"),
    path('meets/reject-request/<int:meet_id>/<int:user_id>/', user_views.reject_meet_request, name="reject_meet_request"),
    path('meets/confirm-request/<int:meet_id>/<int:user_id>/', user_views.confirm_meet_request, name="confirm_meet_request"),
    path('meets/delete-player/<int:meet_id>/<int:user_id>/', user_views.delete_from_players, name="delete_player"),
    path('meets/<meet_category:category>/', user_views.MeetsListView.as_view(), name="meets"),
    path('add-to-wl/<alias>/', user_views.add_to_remove_from_wishlist, name="wl_adding"),
    path('profile/<int:user_id>/', user_views.ProfileDetailView.as_view(), name="profile_detail"),
    path('profile/edit/<int:user_id>/', user_views.profile_editing, name="profile_editing"),
    path('profile/read-notification/', user_views.read_notification, name="read_all_notification"),
    path('profile/read-notification/<int:not_id>/', user_views.read_notification, name="read_notification"),
    path('profiles-list/', user_views.ProfilesList.as_view(), name="profiles_list"),
    path('friendship-query-send/<int:user_id>/', user_views.send_friendship_query, name="send_friendship_query"),
    path('delete-from-friendlist/<int:user_id>/', user_views.delete_from_friendlist, name="delete_from_friendlist"),
    path('friedship-confirm/<int:user_id>/', user_views.confirm_friendship_query, name="friendship_confirm"),
    path('friendsip-reject/<int:user_id>/', user_views.reject_friendship_query, name="friendship_reject"),
    path('friendsip-cancel-query/<int:user_id>/', user_views.cancel_friendship_query, name="cancel_friendship_query"),
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
    urlpatterns += [path('debug-toolbar/', include('debug_toolbar.urls'))]
