from .models import Group, Post, Comment
from django.contrib import admin


class PostAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'text',
        'pub_date',
        'author',
        'group'
    )
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('pub_date',)
    # Это свойство сработает для всех колонок: где пусто — там будет эта строка
    empty_value_display = '-пусто-'


class GroupAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'title',
        'slug',
        'description',
    )
    list_editable = ('description',)


class CommentAdmin(admin.ModelAdmin):
    list_display = (
        'post',
        'created',
        'author',
        'text',
        'active',
    )
    list_filter = (
        'active',
        'created',
    )


admin.site.register(Comment, CommentAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Post, PostAdmin)
