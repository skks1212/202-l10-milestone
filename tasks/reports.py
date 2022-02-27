from django.views.generic.edit import UpdateView

from django.forms import ModelForm

from tasks.models import Report

class ReportForm(ModelForm):

    class Meta:
        model = Report
        fields = ["timing"]
    
    def __init__(self, *args, **kwargs):
       super(ReportForm, self).__init__(*args, **kwargs)

       input_styling = "p-3 bg-gray-200 rounded-xl block w-full my-2 text-base text-black"

       self.fields['timing'].widget.attrs.update({'class' : input_styling})

class GenericReportUpdateView(UpdateView):
    model = Report
    form_class = ReportForm
    template_name = "report_update.html"
    success_url = "/tasks"

    def get_queryset(self):
        return Report.objects.filter(user=self.request.user)
