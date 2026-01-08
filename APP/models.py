from django.db import models
class Participant(models.Model):


    full_name = models.CharField(max_length=150)
    report_data = models.JSONField(default=dict, blank=True)
    report_file = models.FileField(upload_to='reports/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name