from django.contrib import admin

from .models import *



@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['id', 'subject_name', 'is_active', 'is_delete']


admin.site.register(Answer)
# admin.site.register(Subject)
admin.site.register(Question)
admin.site.register(TestPaper)