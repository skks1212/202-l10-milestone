from django import forms
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.detail import DetailView

from django.forms import ModelForm, ValidationError

from tasks.models import Task, TaskHistory, Report, User

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView

from django.contrib.auth.mixins import LoginRequiredMixin

#User Views

class AuthorizedTaskManager(LoginRequiredMixin):
    def get_queryset(self):
        return Task.objects.filter(deleted=False, user=self.request.user)

class UserLoginView(LoginView):
    template_name = "user_login.html"


class StyledUserCreationForm(UserCreationForm):

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super(StyledUserCreationForm, self).__init__(*args, **kwargs)

        input_styling = "p-3 bg-gray-200 rounded-xl block w-full my-2 text-base text-black"

        self.fields['username'].widget.attrs.update({'class' : input_styling})
        self.fields['password1'].widget.attrs.update({'class' : input_styling})
        self.fields['password2'].widget.attrs.update({'class' : input_styling})
    

class UserCreateView(CreateView):
    form_class = StyledUserCreationForm
    template_name = "user_create.html"
    success_url = "/user/login"

#Task Views

class GenericTaskView(LoginRequiredMixin, ListView):
    queryset = Task.objects.filter(deleted=False, completed=False)
    template_name = "tasks.html"
    context_object_name = "tasks"
    #paginate_by = 5 #not specified in milestone

    def get_queryset(self):
        search_term = self.request.GET.get("search")
        list_type = self.request.GET.get("type")

        if list_type == 'pending':
            tasks = Task.objects.filter(deleted=False, completed=False, user=self.request.user).order_by('priority')
        elif list_type == 'completed':
            tasks = Task.objects.filter(deleted=False, completed=True, user=self.request.user).order_by('priority')
        else :
            tasks = Task.objects.filter(deleted=False, user=self.request.user).order_by('priority')
        if search_term:
            tasks = tasks.filter(title__icontains=search_term)
        return tasks

    def get_context_data(self):
        context = {"tasks" : self.get_queryset()}
        context['completed_tasks'] = Task.objects.filter(deleted=False, completed=True, user=self.request.user).count()
        context['total_tasks'] = Task.objects.filter(deleted=False, user=self.request.user).count()
        context['report_id'] = Report.objects.get(user=self.request.user).id
        return context


class GenericTaskDeleteView(AuthorizedTaskManager, DeleteView):
    model = Task
    template_name = "task_delete.html"
    success_url = "/tasks"

class TaskCreateForm(ModelForm):

    def clean_title(self):
        title = self.cleaned_data["title"]
        if(len(title) < 3):
            raise ValidationError("Your Title should have more than 3 characters")
        return title

    class Meta:
        model = Task
        fields = ["title","description","priority","completed","status"]
    
    def __init__(self, *args, **kwargs):
       super(TaskCreateForm, self).__init__(*args, **kwargs)

       input_styling = "p-3 bg-gray-200 rounded-xl block w-full my-2 text-base text-black"

       self.fields['title'].widget.attrs.update({'class' : input_styling})
       self.fields['description'].widget.attrs.update({'class' : f'{input_styling} h-[150px]'})
       self.fields['priority'].widget.attrs.update({'class' : input_styling})
       self.fields['completed'].widget.attrs.update({'class' : 'form-check-input appearance-none h-6 w-6 border border-gray-200 rounded bg-gray-200 checked:bg-red-600 checked:border-red-600 focus:outline-none transition align-top bg-no-repeat bg-center bg-contain cursor-pointer block text-black'})

class GenericTaskUpdateView(AuthorizedTaskManager, UpdateView):
    model = Task
    form_class = TaskCreateForm
    template_name = "task_update.html"
    success_url = "/tasks"

    def form_valid(self, form):
        if 'priority' in form.changed_data:
            form_priority = form.cleaned_data['priority']
            checkPriority(form_priority, self.request.user)

        '''
        if 'status' in form.changed_data:
            new_status = form.cleaned_data['status']
            pr_key = self.object.pk

            this_task = Task.objects.get(id=pr_key)
            old_status = this_task.status

            hist = TaskHistory(task = this_task, old_status = old_status, new_status = new_status)
            hist.save()
        '''

        self.object = form.save()
        return HttpResponseRedirect(self.get_success_url())

class GenericTaskCreateView(CreateView):
    form_class = TaskCreateForm
    template_name = "task_create.html"
    success_url = "/tasks"

    def form_valid(self, form):

        #check and append all priorities
        form_priority = form.cleaned_data['priority']

        checkPriority(form_priority, self.request.user)

        self.object = form.save()
        self.object.user = self.request.user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

def checkPriority(priority_num, user_a):
    has_issue = True
    p_i = priority_num
    to_change = []

    while(has_issue):
        #check if there is a task with priority
        print(f"Checking for priority {p_i}")
        try:
            model = Task.objects.get(priority=p_i,deleted=False,completed=False,user=user_a)
            to_change.append(model)
        except Task.DoesNotExist:
            has_issue = False
            print(f"There is no task with this priority")

        p_i += 1

    for i in range(len(to_change)):
        obj = to_change[i]
        print(f"Old Priority = {obj.priority}")
        obj.priority = int(obj.priority) + 1
        print(f"New Priority = {obj.priority}")

    if(len(to_change) > 0):
        Task.objects.bulk_update(to_change, ['priority'])