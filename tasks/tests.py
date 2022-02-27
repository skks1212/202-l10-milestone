from django.test import TestCase, Client, RequestFactory, TestCase
from .models import Task, TaskHistory, Report, User
from .views import GenericTaskView, UserCreateView
from .tasks import *
from unittest import mock

from datetime import datetime, timezone


class AuthenticationTests(TestCase):
    def test_authenticated(self):
        """
        Try to GET the tasks listing page, expect the response to redirect to the login page
        """
        response = self.client.get("/tasks")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "user/login?next=/tasks")



class ModelTests(TestCase):
    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.user = User.objects.create(username="shivank", email="shivank@writeroo.in", password="helloworld")

    def test_task_model(self):
        self.task_entry = Task.objects.create(title="Simple Task", description="Sample", user = self.user)
        self.assertEqual(str(self.task_entry), self.task_entry.title)

    def test_taskhistory_model(self):
        create_task = Task.objects.create(title="Simple Task", description="Sample", user = self.user)
        create_task.status = 'COMPLETED'
        create_task.save()

        get_history = TaskHistory.objects.filter(task = create_task, old_status = 'PENDING', new_status = 'COMPLETED')
        
        self.assertEqual(get_history.exists(), True)
        self.assertEqual(str(get_history[0]), create_task.title)

    def test_reports_model(self):
        try:
            check_report = Report.objects.get(user=self.user)
        except:
            check_report = None

        self.assertEqual(str(check_report), 'shivank : 0')



class QuestionModelTests(TestCase):
    
    
    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.user = User.objects.create(username="bruce_wayne", email="bruce@wayne.org", password="i_am_batman")

    def test_authenticated(self):
        request = self.factory.get("/tasks")
        request.user = self.user
        response = GenericTaskView.as_view()(request)
        self.assertEqual(response.status_code, 200)

        request = self.factory.get("/create-task")
        request.user = self.user
        response = GenericTaskView.as_view()(request)
        self.assertEqual(response.status_code, 200)

class CronTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.users = []
        self.users.append(User.objects.create(username="test1", email="1@test.com", password="test1"))
        self.users.append(User.objects.create(username="test2", email="2@test.com", password="test2"))

        Report.objects.filter(user__username="test1").update(last_report=datetime.now(timezone.utc).replace(hour = 0) - timedelta(days=1))
        Report.objects.filter(user__username="test2").update(last_report=datetime.now(timezone.utc).replace(hour = 0) - timedelta(days=1))


    def test_reports(self):
        self.assertEqual(send_reports(), ['test1', 'test2'])

class ViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.users = []
        self.users.append(User.objects.create(username="test1", email="1@test.com", password="test1"))
        self.users.append(User.objects.create(username="test2", email="2@test.com", password="test2"))

    def test_all_views(self):
        
        task_1 = Task.objects.create(title="Normal Task", description = "sample desc", user = self.users[0])
        task_2 = Task.objects.create(title="Normal Task 2", description = "sample desc 2", user = self.users[1])
        
        self.client.login(username='test1', password='test1')

        response = self.client.get(f"/update-task/{task_1.pk}")
        self.assertEqual(response.status_code, 200)

        response = self.client.get(f"/delete-task/{task_1.pk}")
        self.assertEqual(response.status_code, 200)

        self.client.login(username='test2', password='test2')

        response = self.client.get(f"/update-task/{task_1.pk}")
        self.assertEqual(response.status_code, 404)

        get_report = Report.objects.get(user=self.users[1])
        response = self.client.get(f"/reports/{get_report.pk}")
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            '/create-task', 
            {
                'title' : 'Appending Priority',
                'description' : 'Lets test if priorities are appended',
                'priority' : 0,
                'completed' : False,
                'status' : 'PENDING'
            }
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/tasks")

        get_old_task = Task.objects.get(title="Normal Task 2", user=self.users[1])
        

        self.assertEqual(get_old_task.priority, 1)
