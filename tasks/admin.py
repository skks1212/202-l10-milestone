from django.contrib import admin

# Register your models here.

from tasks.models import *

admin.sites.site.register(Task)
admin.site.register(Report)
admin.site.register(TaskHistory)
