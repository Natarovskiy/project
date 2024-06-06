from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

class CustomUser(models.Model):
    username = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    token = models.CharField(max_length=255, blank=True, null=True)
    profile_photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)
    favorite_texts = models.ManyToManyField('Text', related_name='favorited_by', blank=True) 
    is_moderator = models.BooleanField(default=False)

    def __str__(self):
        return self.username

class Text(models.Model):
    CATEGORY_CHOICES = [
        ('Завтрак', 'Завтрак'),
        ('Обед', 'Обед'),
        ('Ужин', 'Ужин'),
    ]
    
    title = models.CharField(max_length=255)
    short_description = models.CharField(max_length=255, null=True, blank=True)
    full_description = models.TextField()
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    photo = models.ImageField(upload_to='photos/', null=True, blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    created_at = models.DateTimeField(default=timezone.now)
    views = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title

class UnpublishedText(models.Model):
    title = models.CharField(max_length=255)
    short_description = models.CharField(max_length=255, null=True, blank=True)
    full_description = models.TextField()
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    photo = models.ImageField(upload_to='unpublished_photos/', null=True, blank=True)
    category = models.CharField(max_length=50, choices=Text.CATEGORY_CHOICES)
    created_at = models.DateTimeField(default=timezone.now)
    views = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.title

class Review(models.Model):
    text = models.ForeignKey(Text, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.TextField()
    rating = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(5)])  # Оценка отзыва

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.username} on '{self.text.title}'"

class FavoriteText(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    text = models.ForeignKey(Text, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'text')

    def __str__(self):
        return f"{self.user.username} - {self.text.title}"

class Chat(models.Model):
    user = models.ForeignKey(CustomUser, related_name='user_chats', on_delete=models.CASCADE)
    moderator = models.ForeignKey(CustomUser, related_name='moderator_chats', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat between {self.user.username} and {self.moderator.username}"

class Message(models.Model):
    chat = models.ForeignKey(Chat, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender.username} at {self.created_at}"