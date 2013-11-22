from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
import simplejson as json
from django.views.decorators.csrf import csrf_exempt
from mediascope_cms.apps.api.decorators import api_key_required
from mediascope_cms.apps.api.json_template import JsonTemplate
from mediascope_cms.apps.news.models import Category, Story


@csrf_exempt
def get_video(request):

	return render_to_response('video/iphone_video.html', {

	}, context_instance=RequestContext(request))