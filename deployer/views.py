from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from .deploy_utl import handle_uploaded_file
from django.http import HttpResponseRedirect
from .forms import UploadFileForm
from django.http import JsonResponse
import os



def index(request):
    if request.method == 'POST':
        competition_name = request.POST['competition_name']
        form = UploadFileForm(request.POST, request.FILES)
        all_schools, all_judges, arranged_table, num_nan, filename = handle_uploaded_file(request.FILES['xlsx_file'], competition_name)
        response_data = {
            'all_schools' : all_schools,
            'all_judges' : all_judges,
            'arranged_table' : arranged_table,
            'filename' : filename,
            'num_nan': num_nan
        }
        return JsonResponse(response_data)
    else:
        template = loader.get_template('deployer/index.html')
        context = {}
        return HttpResponse(template.render(context, request))

def download(request, filename):
    with open(os.path.join(os.getcwd(), 'deployer', 'files_for_download', filename), 'rb') as f:
        response = HttpResponse(f, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="' + filename[3:] + '"'
        return response

def downloadsample(request):
    with open(os.path.join(os.getcwd(), 'deployer', 'upload_sample.xlsx'), 'rb') as f:
        response = HttpResponse(f, content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename="upload_sample.xlsx"'
        return response
