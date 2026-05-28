from django.contrib import admin
from .models import Episode, Category, LiveStream, Comment, Event


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon']


@admin.register(Episode)
class EpisodeAdmin(admin.ModelAdmin):
    list_display = ['title', 'episode_type', 'category', 'host', 'duration', 'views_count', 'is_published', 'created_at']
    list_filter = ['episode_type', 'category', 'is_published']
    search_fields = ['title', 'description', 'host']
    list_editable = ['is_published']


@admin.register(LiveStream)
class LiveStreamAdmin(admin.ModelAdmin):
    list_display = ['title', 'platform', 'status', 'viewers_count', 'scheduled_at']
    list_filter = ['platform', 'status']
    search_fields = ['title']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author_name', 'episode', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'episode__episode_type']
    search_fields = ['author_name', 'author_email', 'content']
    list_editable = ['is_approved']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display  = ['title', 'event_type', 'event_date', 'location', 'is_online', 'is_featured', 'is_published']
    list_filter   = ['event_type', 'is_published', 'is_featured', 'is_online']
    search_fields = ['title', 'description', 'location']
    list_editable = ['is_published', 'is_featured']
    readonly_fields = ['created_at']
    date_hierarchy  = 'event_date'
    fieldsets = [
        ('Informations',   {'fields': ('title', 'description', 'event_type', 'image')}),
        ('Dates',          {'fields': ('event_date', 'end_date')}),
        ('Lieu',           {'fields': ('location', 'is_online', 'online_url')}),
        ('Liens',          {'fields': ('registration_url',)}),
        ('Publication',    {'fields': ('is_published', 'is_featured', 'created_at')}),
    ]
