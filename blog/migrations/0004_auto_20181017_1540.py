# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2018-10-17 07:40
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0003_avatarimages_wallpaperimages'),
    ]

    operations = [
        migrations.CreateModel(
            name='ImgTag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.AddField(
            model_name='avatarimages',
            name='downloads',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='wallpaperimages',
            name='downloads',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='avatarimages',
            name='tags',
            field=models.ManyToManyField(blank=True, to='blog.ImgTag'),
        ),
        migrations.AddField(
            model_name='wallpaperimages',
            name='tags',
            field=models.ManyToManyField(blank=True, to='blog.ImgTag'),
        ),
    ]
