from django.shortcuts import render, redirect, get_object_or_404
from registration_app.models import CustomUser, Text, Review, FavoriteText, UnpublishedText
from django.contrib.auth.hashers import make_password, check_password
from datetime import datetime, timedelta
import jwt
from django.utils import timezone
from django.urls import reverse
import re
from django.contrib import messages
from django.db.models import Avg
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseBadRequest, HttpResponseNotFound, HttpResponseRedirect
from .models import Chat, Message, CustomUser
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q

def get_user_from_token(request):
    token = request.COOKIES.get('token')
    if not token:
        return None, render(request, 'registration_app/token_invalid.html')
    try:
        payload = jwt.decode(token, 'secret_key', algorithms=['HS256'])
        user_id = payload['user_id']
        user = CustomUser.objects.get(id=user_id)
        return user, None
    except (jwt.ExpiredSignatureError, jwt.DecodeError, CustomUser.DoesNotExist):
        return None, render(request, 'registration_app/token_invalid.html')

def edit_text(request, text_id):
    text = get_object_or_404(Text, id=text_id)
    user, error_response = get_user_from_token(request)
    if error_response:
        return error_response

    if text.user != user and not user.is_moderator:
        return HttpResponseForbidden("You are not allowed to edit this post.")

    if request.method == 'POST':
        title = request.POST['title']
        short_description = request.POST['short_description']
        full_description = request.POST['full_description']
        photo = request.FILES.get('photo')
        delete_photo = request.POST.get('delete_photo')

        if delete_photo:
            text.photo.delete()
            text.save()
        elif photo:
            text.photo = photo
            text.save()
            
        if (text.title != title or 
            text.short_description != short_description or 
            text.full_description != full_description):

            text.title = title
            text.short_description = short_description
            text.full_description = full_description
            text.save()

        return redirect(reverse('text_detail', kwargs={'text_id': text.id}))

    return render(request, 'registration_app/edit_text.html', {'text': text})

def delete_text(request, text_id):
    user, error_response = get_user_from_token(request)
    if error_response:
        return error_response

    text = get_object_or_404(Text, id=text_id)

    if text.user != user and not user.is_moderator:
        return HttpResponseForbidden("You are not allowed to delete this post.")

    if request.method == 'POST':
        text.delete()
        messages.success(request, 'The post has been deleted.')
        return redirect('success')

    return render(request, 'registration_app/delete_text.html', {'text': text})

def logout(request):
    response = redirect('/success/')
    response.delete_cookie('token')
    return response

def password_is_valid(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character."
    return True, ""


def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST['email']

        is_valid, validation_error = password_is_valid(password)
        if not is_valid:
            return render(request, 'registration_app/register.html', {'error': validation_error})

        if CustomUser.objects.filter(username=username).exists():
            return render(request, 'registration_app/register.html', {'error': 'Username already exists'})
        if CustomUser.objects.filter(email=email).exists():
            return render(request, 'registration_app/register.html', {'error': 'Email already exists'})

        hashed_password = make_password(password)

        user = CustomUser(username=username, password=hashed_password, email=email)
        user.save()

        return redirect('/login/')

    return render(request, 'registration_app/register.html')

def text_detail(request, text_id):
    user, error_response = get_user_from_token(request)
    if error_response and request.method == 'POST':
        return error_response

    text = get_object_or_404(Text, id=text_id)
    text.views += 1
    text.save()

    if request.method == 'POST':
        if user:
            content = request.POST['content']
            rating = request.POST.get('rating')

            review, created = Review.objects.get_or_create(text=text, user=user)

            if not created:
                review.content = content
                review.rating = rating
                review.save()
                messages.success(request, 'Your review has been updated.')
            else:
                review.content = content
                review.rating = rating
                review.save()
                messages.success(request, 'Your review has been submitted.')
        else:
            messages.error(request, 'You need to be logged in to leave a review.')
            return redirect('login')

    reviews = text.reviews.all()
    user_review = Review.objects.filter(text=text, user=user).first() if user else None
    is_favorite = user and text in user.favorite_texts.all() if user else False
    average_rating = text.reviews.aggregate(Avg('rating'))['rating__avg']

    return render(request, 'registration_app/text_detail.html', {
        'text': text,
        'reviews': reviews,
        'user_review': user_review,
        'average_rating': average_rating,
        'is_favorite': is_favorite,
        'user': user,
    })

def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        try:
            user = CustomUser.objects.get(username=username)
            if check_password(password, user.password):
                payload = {
                    'user_id': user.id,
                    'exp': datetime.utcnow() + timedelta(days=7)
                }
                token = jwt.encode(payload, 'secret_key', algorithm='HS256')

                user.token = token
                user.save()

                response = redirect('/success/')
                response.set_cookie('token', token)
                return response
            else:
                return render(request, 'registration_app/login.html', {'error': 'Invalid username or password'})
        except CustomUser.DoesNotExist:
            return render(request, 'registration_app/login.html', {'error': 'Invalid username or password'})

    return render(request, 'registration_app/login.html')

def success(request):
    user, error_response = get_user_from_token(request)
    
    texts = Text.objects.order_by('-id')[:5]
    search_query = request.GET.get('search_query')

    if search_query:
        texts = texts.filter(
            Q(title__icontains=search_query) |
            Q(short_description__icontains=search_query) |
            Q(full_description__icontains=search_query)
        )

    texts_by_category = {
        'Завтрак': Text.objects.filter(category='Завтрак').order_by('-id')[:5],
        'Обед': Text.objects.filter(category='Обед').order_by('-id')[:5],
        'Ужин': Text.objects.filter(category='Ужин').order_by('-id')[:5]
    }

    most_viewed_texts = Text.objects.order_by('-views')[:5]

    top_rated_texts = Text.objects.annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')[:5]

    for category, category_texts in texts_by_category.items():
        for text in category_texts:
            text.average_rating = text.reviews.aggregate(Avg('rating'))['rating__avg']

    for text in texts:
        text.average_rating = text.reviews.aggregate(Avg('rating'))['rating__avg']

    for text in most_viewed_texts:
        text.average_rating = text.reviews.aggregate(Avg('rating'))['rating__avg']

    for text in top_rated_texts:
        text.average_rating = text.reviews.aggregate(Avg('rating'))['rating__avg']
        
    categories = Text.CATEGORY_CHOICES

    return render(request, 'registration_app/success.html', {
        'username': user.username if user else None, 
        'texts': texts,
        'texts_by_category': texts_by_category,
        'most_viewed_texts': most_viewed_texts,
        'top_rated_texts': top_rated_texts,
        'token': request.COOKIES.get('token'),
        'is_moderator': user.is_moderator if user else False,
        'search_query': search_query,
        'categories': categories
    })


def search_results(request):
    user, error_response = get_user_from_token(request)

    search_query = request.GET.get('search_query')
    category_filter = request.GET.get('category_filter')

    texts = Text.objects.all().annotate(average_rating=Avg('reviews__rating'))

    if search_query:
        texts = texts.filter(
            Q(title__icontains=search_query) |
            Q(short_description__icontains=search_query) |
            Q(full_description__icontains=search_query)
        )

    if category_filter:
        texts = texts.filter(category=category_filter)

    paginator = Paginator(texts, 10)
    page = request.GET.get('page')
    
    try:
        texts = paginator.page(page)
    except PageNotAnInteger:
        texts = paginator.page(1)
    except EmptyPage:
        texts = paginator.page(paginator.num_pages)

    categories = Text.CATEGORY_CHOICES

    return render(request, 'registration_app/search_results.html', {
        'username': user.username if user else None, 
        'search_query': search_query,
        'texts': texts,
        'categories': categories,
        'selected_category': category_filter
    })

def profile(request):
    user, error_response = get_user_from_token(request)
    if error_response:
        return error_response

    texts = Text.objects.filter(user=user).annotate(average_rating=Avg('reviews__rating'))
    reviews = Review.objects.filter(user=user)

    texts_paginator = Paginator(texts, 5)
    reviews_paginator = Paginator(reviews, 5)

    texts_page_number = request.GET.get('texts_page')
    reviews_page_number = request.GET.get('reviews_page')

    texts_page_obj = texts_paginator.get_page(texts_page_number)
    reviews_page_obj = reviews_paginator.get_page(reviews_page_number)

    if request.method == 'POST':
        profile_photo = request.FILES.get('profile_photo')
        if profile_photo:
            user.profile_photo = profile_photo
            user.save()

    show_view_all_texts_button = texts.count() > 4
    show_view_all_reviews_button = reviews.count() > 4

    return render(request, 'registration_app/profile.html', {
        'user': user,
        'texts_page_obj': texts_page_obj,
        'reviews_page_obj': reviews_page_obj,
        'show_view_all_texts_button': show_view_all_texts_button,
        'show_view_all_reviews_button': show_view_all_reviews_button,
    })

def all_favorite_texts(request):
    user, error_response = get_user_from_token(request)
    if error_response:
        return error_response
    
    favorite_texts = user.favorite_texts.annotate(average_rating=Avg('reviews__rating')).all()
    paginator = Paginator(favorite_texts, 10)
    page = request.GET.get('page')
    
    try:
        favorite_texts = paginator.page(page)
    except PageNotAnInteger:
        favorite_texts = paginator.page(1)
    except EmptyPage:
        favorite_texts = paginator.page(paginator.num_pages)

    return render(request, 'registration_app/all_favorite_texts.html', {
        'user': user,
        'favorite_texts': favorite_texts,
    })

def all_reviews(request):
    user, error_response = get_user_from_token(request)
    if error_response:
        return error_response

    reviews = Review.objects.filter(user=user)
    paginator = Paginator(reviews, 10)
    page = request.GET.get('page')
    
    try:
        reviews = paginator.page(page)
    except PageNotAnInteger:
        reviews = paginator.page(1)
    except EmptyPage:
        reviews = paginator.page(paginator.num_pages)

    return render(request, 'registration_app/all_reviews.html', {
        'user': user,
        'reviews': reviews,
    })

def all_texts(request):
    user, error_response = get_user_from_token(request)
    if error_response:
        return error_response

    texts = Text.objects.filter(user=user).annotate(average_rating=Avg('reviews__rating'))
    paginator = Paginator(texts, 10)
    page = request.GET.get('page')
    
    try:
        texts = paginator.page(page)
    except PageNotAnInteger:
        texts = paginator.page(1)
    except EmptyPage:
        texts = paginator.page(paginator.num_pages)

    return render(request, 'registration_app/all_texts.html', {
        'user': user,
        'texts': texts,
    })

def create_text(request):
    user, error_response = get_user_from_token(request)
    if error_response:
        return error_response

    if request.method == 'POST':
        title = request.POST['title']
        short_description = request.POST['short_description']
        full_description = request.POST['full_description']
        category = request.POST['category']
        photo = request.FILES.get('photo')

        if not category:
            return render(request, 'registration_app/create_text.html', {
                'error': 'Please select a category.'
            })

        unpublished_text = UnpublishedText(
            title=title,
            short_description=short_description,
            full_description=full_description,
            user=user,
            photo=photo,
            category=category,
        )
        unpublished_text.save()

        return redirect('/success')

    return render(request, 'registration_app/create_text.html')

def change_password(request):
    user, error_response = get_user_from_token(request)
    if error_response:
        return error_response

    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            return render(request, 'registration_app/change_password.html', {'error': 'New password and confirm password do not match'})

        if not check_password(old_password, user.password):
            return render(request, 'registration_app/change_password.html', {'error': 'Old password is incorrect'})

        is_valid, validation_error = password_is_valid(new_password)
        if not is_valid:
            return render(request, 'registration_app/change_password.html', {'error': validation_error})

        hashed_password = make_password(new_password)
        user.password = hashed_password
        user.save()

        return redirect('/success/')

    return render(request, 'registration_app/change_password.html')

def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    user, error_response = get_user_from_token(request)
    if error_response:
        return error_response
    if review.user.id != user.id and not user.is_moderator:
        return HttpResponseForbidden("You don't have permission to delete this review.")

    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Review deleted successfully.')
        return redirect(reverse('text_detail', kwargs={'text_id': review.text.id}))

    return HttpResponseBadRequest("Invalid request method.")

def add_to_favorites(request, text_id):
    user, error_response = get_user_from_token(request)
    if error_response:
        return error_response

    text = get_object_or_404(Text, id=text_id)
    user.favorite_texts.add(text)
    messages.success(request, 'Text added to favorites.')
    return redirect('all_favorite_texts')

def remove_from_favorites(request, text_id):
    user, error_response = get_user_from_token(request)
    if error_response:
        return error_response

    text = get_object_or_404(Text, id=text_id)
    user.favorite_texts.remove(text)
    messages.success(request, 'Text removed from favorites.')
    return redirect('all_favorite_texts')

def favorite_texts(request):
    user, error_response = get_user_from_token(request)
    if error_response:
        return error_response

    favorite_texts = user.favorite_texts.all()

    paginator = Paginator(favorite_texts, 10)
    page_number = request.GET.get('page')
    try:
        favorite_texts = paginator.page(page_number)
    except PageNotAnInteger:
        favorite_texts = paginator.page(1)
    except EmptyPage:
        favorite_texts = paginator.page(paginator.num_pages)

    return render(request, 'registration_app/favorite_texts.html', {'favorite_texts': favorite_texts, 'username': user.username})

def moderator_unpublished_texts(request):
    user, error_response = get_user_from_token(request)
    if error_response:
        return error_response

    if not user.is_moderator:
        return render(request, 'registration_app/access_denied.html')

    unpublished_texts = UnpublishedText.objects.all()

    paginator = Paginator(unpublished_texts, 10)
    page_number = request.GET.get('page')
    try:
        unpublished_texts = paginator.page(page_number)
    except PageNotAnInteger:
        unpublished_texts = paginator.page(1)
    except EmptyPage:
        unpublished_texts = paginator.page(paginator.num_pages)

    return render(request, 'registration_app/moderator_unpublished_texts.html', {'unpublished_texts': unpublished_texts})

def unpublished_text_detail(request, text_id):
    user, error_response = get_user_from_token(request)
    if error_response:
        return error_response

    if not user.is_moderator:
        return render(request, 'registration_app/access_denied.html')

    unpublished_text = get_object_or_404(UnpublishedText, id=text_id)

    if request.method == 'POST':
        if 'publish' in request.POST:
            text_id = request.POST.get('publish')
            unpublished_text = get_object_or_404(UnpublishedText, id=text_id)
            text = Text.objects.create(
                title=unpublished_text.title,
                short_description=unpublished_text.short_description,
                full_description=unpublished_text.full_description,
                user=unpublished_text.user,
                photo=unpublished_text.photo,
                category=unpublished_text.category,
                views=unpublished_text.views
            )
            unpublished_text.delete()
            return redirect('moderator_unpublished_texts')
        elif 'reject' in request.POST:
            text_id = request.POST.get('reject')
            unpublished_text = get_object_or_404(UnpublishedText, id=text_id)
            unpublished_text.delete()
            return redirect('moderator_unpublished_texts')
    return render(request, 'registration_app/unpublished_text_detail.html', {'unpublished_text': unpublished_text})

def chat_list(request):
    user, error_response = get_user_from_token(request)
    if error_response:
        return error_response

    if user.is_moderator:
        chats = Chat.objects.filter(moderator=user)
    else:
        chats = Chat.objects.filter(user=user)

    return render(request, 'registration_app/chat_list.html', {'chats': chats, 'user': user})

def chat_detail(request, chat_id):
    user, error_response = get_user_from_token(request)
    if error_response:
        return error_response

    chat = get_object_or_404(Chat, id=chat_id)
    if user != chat.user and user != chat.moderator:
        return HttpResponseForbidden("You are not allowed to view this chat.")

    if request.method == 'POST':
        text = request.POST['text']
        message = Message.objects.create(chat=chat, sender=user, text=text)
        message.save()
        return redirect('chat_detail', chat_id=chat.id)

    messages = chat.messages.all()
    return render(request, 'registration_app/chat_detail.html', {'chat': chat, 'messages': messages})

def create_chat(request, moderator_id):
    user, error_response = get_user_from_token(request)
    if error_response:
        return error_response
    
    existing_chat = Chat.objects.filter(user=user).exists()
    if existing_chat:
        chat = Chat.objects.get(user=user)
        return redirect('chat_detail', chat_id=chat.id)

    moderator = get_object_or_404(CustomUser, id=moderator_id, is_moderator=True)
    chat, created = Chat.objects.get_or_create(user=user, moderator=moderator)
    return redirect('chat_detail', chat_id=chat.id)

def delete_chat(request, chat_id):
    user, error_response = get_user_from_token(request)
    if error_response:
        return error_response

    chat = get_object_or_404(Chat, id=chat_id)

    if chat.user != user and not user.is_moderator:
        return HttpResponseForbidden("You are not allowed to delete this chat.")

    if request.method == 'POST':
        chat.delete()
        messages.success(request, 'Chat has been deleted.')
        return redirect('chat_list')

    return render(request, 'registration_app/delete_chat.html', {'chat': chat})