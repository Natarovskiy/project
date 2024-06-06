from django.contrib import admin
from django.urls import path
from registration_app import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('success/', views.success, name='success'),
    path('logout/', views.logout, name='logout'),
    path('create_text/', views.create_text, name='create_text'),
    path('edit_text/<int:text_id>/', views.edit_text, name='edit_text'),
    path('delete_text/<int:text_id>/', views.delete_text, name='delete_text'),
    path('profile/', views.profile, name='profile'),
    path('change_password/', views.change_password, name='change_password'),
    path('delete_review/<int:review_id>/', views.delete_review, name='delete_review'),
    path('text_detail/<int:text_id>/', views.text_detail, name='text_detail'),
    path('favorite_texts/', views.favorite_texts, name='favorite_texts'),
    path('add_to_favorites/<int:text_id>/', views.add_to_favorites, name='add_to_favorites'),
    path('search/', views.search_results, name='search_results'),
    path('moderator/', views.moderator_unpublished_texts, name='moderator_unpublished_texts'),
    path('unpublished_text_detail/<int:text_id>/', views.unpublished_text_detail, name='unpublished_text_detail'),
    path('remove_from_favorites/<int:text_id>/', views.remove_from_favorites, name='remove_from_favorites'),
    path('admin/', admin.site.urls),
    path('chats/', views.chat_list, name='chat_list'),
    path('chats/<int:chat_id>/', views.chat_detail, name='chat_detail'),
    path('create_chat/<int:moderator_id>/', views.create_chat, name='create_chat'),
    path('delete_chat/<int:chat_id>/', views.delete_chat, name='delete_chat'),
    path('all_reviews/', views.all_reviews, name='all_reviews'),
    path('all_texts/', views.all_texts, name='all_texts'),
    path('all_favorite_texts/', views.all_favorite_texts, name='all_favorite_texts'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
