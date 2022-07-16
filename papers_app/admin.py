from django.contrib import admin

from .models import *

# admin.site.register(Answer)
# admin.site.register(Subject)
# admin.site.register(Question)
# admin.site.register(TestPaper)
# admin.site.register()
# admin.site.register()
# admin.site.register()

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['id', 'subject_name', 'is_active', 'is_delete']
    