from django.contrib import admin
from .models import Post, Category, Tag, qkCookies, avatarImages, ImgTag, wallpaperImages


class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'created_time', 'modified_time', 'category', 'author']


admin.site.register(Post, PostAdmin)
admin.site.register(Category)
admin.site.register(Tag)
admin.site.register(qkCookies)

class avatarImagesAdmin(admin.ModelAdmin):
    list_display = ['image_data', 'url', 'downloads']

admin.site.register(avatarImages,avatarImagesAdmin)

class wallpaperImagesAdmin(admin.ModelAdmin):
    list_display = ['image_data', 'url', 'downloads']

admin.site.register(wallpaperImages,wallpaperImagesAdmin)

admin.site.register(ImgTag)

