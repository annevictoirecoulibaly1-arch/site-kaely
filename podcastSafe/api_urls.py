from django.urls import path
from . import api_views

app_name = 'api'

urlpatterns = [
    # Dashboard overview
    path('dashboard-data/', api_views.dashboard_data, name='dashboard_data'),

    # Episodes
    path('episodes/', api_views.episodes_api, name='episodes_api'),
    path('episodes/create/', api_views.episode_create, name='episode_create'),
    path('episodes/<int:pk>/update/', api_views.episode_update, name='episode_update'),
    path('episodes/<int:pk>/upload/', api_views.episode_upload_file, name='episode_upload_file'),
    path('episodes/<int:pk>/delete/', api_views.episode_delete, name='episode_delete'),
    path('categories/', api_views.categories_api, name='categories_api'),
    path('categories/create/', api_views.category_create, name='category_create'),
    path('categories/<int:pk>/update/', api_views.category_update, name='category_update'),
    path('categories/<int:pk>/delete/', api_views.category_delete, name='category_delete'),

    # Analytics
    path('analytics/', api_views.analytics_data, name='analytics_data'),

    # Live Streams
    path('livestreams/', api_views.livestreams_api, name='livestreams_api'),
    path('livestreams/create/', api_views.livestream_create, name='livestream_create'),
    path('livestreams/<int:pk>/update/', api_views.livestream_update, name='livestream_update'),
    path('livestreams/<int:pk>/delete/', api_views.livestream_delete, name='livestream_delete'),

    # Messages
    path('messages/', api_views.messages_api, name='messages_api'),
    path('messages/<int:pk>/read/', api_views.message_mark_read, name='message_mark_read'),
    path('messages/<int:pk>/delete/', api_views.message_delete, name='message_delete'),
    path('messages/mark-all-read/', api_views.message_mark_all_read, name='message_mark_all_read'),

    # Subscriptions
    path('subscriptions/', api_views.subscriptions_api, name='subscriptions_api'),
    path('subscriptions/<int:pk>/delete/', api_views.subscription_delete, name='subscription_delete'),

    # Chunked upload (gros fichiers)
    path('episodes/<int:pk>/upload-chunk/', api_views.episode_upload_chunk, name='episode_upload_chunk'),

    # Comments
    path('comments/', api_views.comments_api, name='comments_api'),
    path('comments/<int:pk>/approve/', api_views.comment_approve, name='comment_approve'),
    path('comments/<int:pk>/delete/', api_views.comment_delete, name='comment_delete'),

    # Multistream
    path('multistream/config/', api_views.multistream_config, name='multistream_config'),
    path('multistream/start/', api_views.multistream_start, name='multistream_start'),
    path('multistream/stop/', api_views.multistream_stop, name='multistream_stop'),
    path('multistream/ingest/', api_views.multistream_ingest, name='multistream_ingest'),
    path('multistream/status/', api_views.multistream_status, name='multistream_status'),
]
