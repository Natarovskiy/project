# Generated by Django 5.0.6 on 2024-05-31 12:55

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models

class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CustomUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=255, unique=True)),
                ('password', models.CharField(max_length=255)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('token', models.CharField(blank=True, max_length=255, null=True)),
                ('profile_photo', models.ImageField(blank=True, null=True, upload_to='profile_photos/')),
            ],
        ),
        migrations.CreateModel(
            name='Text',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('short_description', models.CharField(blank=True, max_length=255, null=True)),
                ('full_description', models.TextField()),
                ('photo', models.ImageField(blank=True, null=True, upload_to='photos/')),
                ('category', models.CharField(choices=[('Рецепт', 'Рецепт'), ('Совет', 'Совет'), ('Диета', 'Диета')], max_length=50)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='registration_app.customuser')),
            ],
        ),
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('rating', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(5)])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='registration_app.customuser')),
                ('text', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='registration_app.text')),
            ],
        ),
        migrations.AddField(
            model_name='customuser',
            name='favorite_texts',
            field=models.ManyToManyField(blank=True, related_name='favorited_by', to='registration_app.text'),
        ),
        migrations.CreateModel(
            name='FavoriteText',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('added_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='registration_app.customuser')),
                ('text', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='registration_app.text')),
            ],
            options={
                'unique_together': {('user', 'text')},
            },
        ),
    ]
