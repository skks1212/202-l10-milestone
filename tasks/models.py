from django.db import models

#from django.contrib.auth.models import User

from task_manager.users.models import User

from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save

from datetime import datetime, timezone

STATUS_CHOICES = (
    ("PENDING", "PENDING"),
    ("IN_PROGRESS", "IN_PROGRESS"),
    ("COMPLETED", "COMPLETED"),
    ("CANCELLED", "CANCELLED"),
)

class Task(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    completed = models.BooleanField(default=False) #dont think we need this after adding the status column
    created_date = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(default=False)
    user = models.ForeignKey(User , on_delete=models.CASCADE , null=True,blank=True)
    status = models.CharField(max_length=100, choices=STATUS_CHOICES, default=STATUS_CHOICES[0][0])
    priority = models.IntegerField(default=0)

    def __str__(self):
        return self.title

class TaskHistory(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE,null=True,blank=True)
    old_status = models.CharField(max_length=100, choices=STATUS_CHOICES)
    new_status = models.CharField(max_length=100, choices=STATUS_CHOICES)
    date_time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.task)

class Report(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null = True, blank = True)
    timing = models.IntegerField(default = 0)
    last_report = models.DateTimeField(null=True, default=datetime.now(timezone.utc).replace(hour=0))

    def __str__(self):
        return f"{str(self.user)} : {str(self.timing)}" 

@receiver(pre_save, sender=Task)
def generateHistory(instance, **kwargs):
    try:
        task = Task.objects.get(pk=instance.id)
    except:
        task = None

    if task is not None and task.status != instance.status:
        TaskHistory.objects.create(
            task=task,
            old_status=task.status,
            new_status=instance.status
        )

@receiver(post_save, sender=User)
def generateReport(instance, **kwargs):
    try:
        user = User.objects.get(pk=instance.id)
        try:
            report = Report.objects.get(user=user)
        except:
            report = None
    except:
        user = None
        report = None

    if user is not None and report is None:
        Report.objects.create(
            user=user,
            timing=0
        )

@receiver(post_save, sender=Report)
def setReportTime(instance, **kwargs):
    try:
        report = Report.objects.get(pk=instance.id)
    except:
        report = None

    if report is not None:
        report.last_report = datetime.now(timezone.utc).replace(hour=report.timing)
        report.save()