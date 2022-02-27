'''
import datetime

from django.contrib.auth.models import User
from django.core.mail import send_mail
from tasks.models import Task, Report
from datetime import timedelta, datetime, timezone

from celery.decorators import periodic_task

from celery import Celery

from config.celery_app import app



@periodic_task(run_every=timedelta(hours=1))
def send_reports():
    #reports that were not sent in 1 day
    get_unsent_reports = Report.objects.filter(last_report__lte = (datetime.now(timezone.utc) - timedelta(days=1)))
    
    completed = []

    stat_choices = [
        ["Pending", "PENDING"],
        ["In Progress", "IN_PROGRESS"],
        ["Completed", "COMPLETED"],
        ["Cancelled", "CANCELLED"]
    ]

    for report in get_unsent_reports:
        base_qs = Task.objects.filter(user=report.user, deleted = False).order_by('priority')

        email_content = f'Hey there {report.user.username}\nHere is your daily task summary:\n\n'

        for status in stat_choices:
            stat_name = status[0]
            stat_id = status[1]

            stat_qs = base_qs.filter(status = stat_id)

            stat_count = stat_qs.count()
            status.append(stat_count)

            email_content += f"{stat_count} {stat_name} Tasks:\n"
            for q in stat_qs:
                email_content+= f" -> {q.title} ({q.priority}): \n  | {q.description} \n  | Created on {q.created_date} \n \n"

        send_mail(f"You have {stat_choices[0][2]} pending and {stat_choices[1][2]} in progress tasks", email_content, "tasks@task_manager.org", [report.user.email])

        completed.append(report.user.username)
        report.last_report = datetime.now(timezone.utc).replace(hour=report.timing)
        report.save()

        print(f"Completed Processing User {report.user.id}")

    return completed
'''