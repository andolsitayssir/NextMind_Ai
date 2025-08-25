from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Participant

@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ('full_name',  'report_file', 'created_at')
    search_fields = ('full_name', )
    