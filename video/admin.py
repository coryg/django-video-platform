from models import *
from django.contrib import admin

class RenderPresetAdmin(admin.ModelAdmin):
	list_display = ('default', 'name', 'description', 'aws_preset_id', 'container')
	list_display_links = ('name', 'description',)
	ordering = ('-default', 'aws_preset_id')

class PipelineAdmin(admin.ModelAdmin):
	list_display = ('name', 'input_bucket', 'output_bucket', 'auto_process_inputs',)
	list_display_links = ('name',)

class TranscodeJobAdmin(admin.ModelAdmin):
	list_display = ('input_filename', 'pipeline', 'aws_job_id', 'status',)
	list_display_links = ('input_filename',)

admin.site.register(Video)
admin.site.register(Render)
admin.site.register(RenderPreset, RenderPresetAdmin)
admin.site.register(Pipeline, PipelineAdmin)
admin.site.register(TranscodeJob, TranscodeJobAdmin)