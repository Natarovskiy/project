from django.contrib import admin
from .models import CustomUser, Text, UnpublishedText, Review, FavoriteText, Chat, Message

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_moderator')
    search_fields = ('username', 'email')
    list_filter = ('is_moderator',)

@admin.register(Text)
class TextAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'category', 'created_at')
    search_fields = ('title', 'user__username')
    list_filter = ('category', 'created_at')

@admin.register(UnpublishedText)
class UnpublishedTextAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'category', 'created_at')
    search_fields = ('title', 'user__username')
    list_filter = ('category', 'created_at')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('text', 'user', 'rating', 'created_at')
    search_fields = ('text__title', 'user__username')
    list_filter = ('rating', 'created_at')

@admin.register(FavoriteText)
class FavoriteTextAdmin(admin.ModelAdmin):
    list_display = ('user', 'text', 'added_at')
    search_fields = ('user__username', 'text__title')
    list_filter = ('added_at',)

@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('user', 'moderator', 'created_at')
    search_fields = ('user__username', 'moderator__username')
    list_filter = ('created_at',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('chat', 'sender', 'text', 'created_at')
    search_fields = ('chat__user__username', 'chat__moderator__username', 'sender__username')
    list_filter = ('created_at',)

