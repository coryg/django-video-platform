from django.core.urlresolvers import reverse

## The basic reverse format is this "admin:APP_MODEL_AdminViewName"
## More info on how to reverse Admin URLS is located here:
##
## https://docs.djangoproject.com/en/dev/ref/contrib/admin/#reversing-admin-urls
##
from video.models import Pipeline, AWSSyncHistory, RenderPreset


class VideoMiddleware(object):
	def process_request(self, request):
		if not hasattr(request, '__checked_sync_status'):
			if AWSSyncHistory.is_first_load():
				Pipeline.sync_with_aws()
				RenderPreset.sync_with_aws()
			else:
				if request.path.startswith(reverse('admin:video_pipeline_changelist')):
					self.__pipeline_admin_list(request)
				if request.path.startswith(reverse('admin:video_renderpreset_changelist')):
					self.__renderpreset_admin_list(request)

			request.__checked_sync_status = True

	def __pipeline_admin_list(self, request):
		if Pipeline.sync_required():
			Pipeline.sync_with_aws()

	def __renderpreset_admin_list(self, request):
		if RenderPreset.sync_required():
			RenderPreset.sync_with_aws()