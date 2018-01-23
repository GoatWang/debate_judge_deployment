from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from .deploy_utl import handle_uploaded_file
from django.http import HttpResponseRedirect
from .forms import UploadFileForm


# Create your tests here.


def index(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        arranged_table = handle_uploaded_file(request.FILES['xlsx_file'])
        return HttpResponse(arranged_table)
    else:
        template = loader.get_template('deployer/index.html')
        context = {}
        return HttpResponse(template.render(context, request))

def success(request):
    return HttpResponse("Success!")
