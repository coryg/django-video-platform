import os
from django.conf import settings
from django.db import models
from mediascope_cms import boto

class Pipeline(models.Model):
	aws_pipeline_id = models.CharField(max_length=50, unique=True)
	name = models.CharField(max_length=40)
	input_bucket = models.CharField(max_length=1000)
	output_bucket = models.CharField(max_length=1000)

	#internal settings
	auto_process_inputs = models.BooleanField()

	def __unicode__(self):
		return self.name

	@staticmethod
	def sync_with_aws():
		et = boto.connect_elastictranscoder(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
		pipelines = et.list_pipelines()
		for p in pipelines['Pipelines']:
			id = p['Id']
			found_object = Pipeline.objects.filter(aws_pipeline_id=id)
			if found_object.count() == 0:
				found_object = Pipeline()
				found_object.aws_pipeline_id = id
				found_object.auto_process_inputs = False
			else:
				found_object = found_object[0]

			found_object.name = p['Name']
			found_object.input_bucket = p['InputBucket']
			found_object.output_bucket = p['ContentConfig']['Bucket']
			found_object.save()

	def import_videos(self):
		s3 = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
		et = boto.connect_elastictranscoder(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
		b = s3.get_bucket(self.input_bucket)

		default_presets = RenderPreset.objects.filter(default=True)

		keys = b.list()

		for key in keys:
			if not key.key.endswith('/'):
				Video.create_video(key.key, self, default_presets)

	def push_pending_jobs_to_aws(self):
		jobs = self.transcodejob_set.filter(status='pending_creation')
		for j in jobs:
			j.push_to_aws()


class TranscodeJob(models.Model):
	STATUS_CHOICES = (
		('pending_creation', 'Pending Creation'),
		('submitted', 'Submitted'),
		('progressing', 'Progressing'),
		('complete', 'Complete'),
		('error', 'Error'),
		('canceled', 'Canceled'),
	)

	pipeline = models.ForeignKey(Pipeline, to_field='aws_pipeline_id')
	aws_job_id = models.CharField(max_length=50, blank=True)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_creation')

	input_filename = models.CharField(max_length=1000)

	def push_to_aws(self):
		et = boto.connect_elastictranscoder(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)

		renders = self.render_set.all()

		transInput = {
			'Key': self.input_filename,
			'FrameRate': 'auto',
			'Resolution': 'auto',
			'AspectRatio': 'auto',
			'Interlaced': 'auto',
			'Container': 'auto'
		}
		outputs = []
		for r in renders:
			outputs.append(r.get_aws_output())

		et.create_job(
			pipeline_id=self.pipeline.aws_pipeline_id,
			input_name=transInput,
			outputs=outputs,
			)

		self.status = 'submitted'
		self.save()

class RenderPreset(models.Model):
	aws_preset_id = models.CharField(max_length=50, unique=True)
	name = models.CharField(max_length=40)
	description = models.CharField(max_length=255)
	container = models.CharField(max_length=10)

	#internal settings
	default = models.BooleanField()

	def __unicode__(self):
		return self.name

	@staticmethod
	def sync_with_aws():
		et = boto.connect_elastictranscoder(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
		presets = et.list_presets()
		for p in presets['Presets']:
			id = p['Id']
			found_object = RenderPreset.objects.filter(aws_preset_id=id)
			if found_object.count() == 0:
				found_object = RenderPreset()
				found_object.aws_preset_id = id
				found_object.default = False
			else:
				found_object = found_object[0]

			found_object.name = p['Name']
			found_object.description = p['Description']
			found_object.container = p['Container']
			found_object.save()


class Video(models.Model):
	title = models.CharField(max_length=100)
	short_description = models.CharField(max_length=250, blank=True, null=True)
	long_description = models.CharField(max_length=5000, blank=True, null=True)
	related_link_on = models.BooleanField(default=False)
	related_link = models.URLField(max_length=500, blank=True, null=True)
	related_link_description = models.CharField(max_length=255, blank=True, null=True)
	reference_id = models.CharField(max_length=150, blank=True, null=True)

	#Images
	video_still = None
	video_thumbnail = None

	#Monetization
	show_advertising = models.BooleanField()

	#storage info
	s3_bucket = models.CharField(max_length=1000)

	@staticmethod
	def create_video(input_filename, pipeline, presets):
		clean_filename = input_filename.split('/')[-1]

		video = Video()
		video.title = clean_filename
		video.save()

		job = TranscodeJob()
		job.input_filename = input_filename
		job.pipeline = pipeline
		job.save()

		for p in presets:
			video.create_render(job, p)


	def get_s3_bucket(self):
		s3 = boto.connect_s3(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY)
		b = s3.get_bucket(self.input_bucket)
		return b

	def create_render(self, job, preset):
		found_objects = Render.objects.filter(video=self, preset=preset)
		if found_objects.count() > 0:
			for render in found_objects:
				if render.status == 'ready':
					render.delete()

		render = Render()
		render.video = self
		render.job = job
		render.preset = preset
		render.asset_id = render.generate_asset_id()
		render.original_filename = render.job.input_filename
		render.save()

class Render(models.Model):

	STATUS_CHOICES = (
		('queued', 'Queued for Transcoding'),
		('transcoding', 'Transcoding'),
		('ready', 'Ready for Serving'),
	)

	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
	video = models.ForeignKey(Video)
	job = models.ForeignKey(TranscodeJob,)
	preset = models.ForeignKey(RenderPreset, to_field='aws_preset_id')
	asset_id = models.CharField(max_length=50)
	original_filename = models.CharField(max_length=500, blank=True, null=True)
	filename = models.CharField(max_length=500, blank=True, null=True)
	duration = models.CharField(max_length=20, blank=True, null=True)
	create_date = models.DateTimeField(auto_now_add=True)
	container_type = models.CharField(max_length=20, blank=True, null=True)
	video_codec = models.CharField(max_length=20, blank=True, null=True)
	audio_codes = models.CharField(max_length=20, blank=True, null=True)

	def delete(self):
		b = self.video.get_s3_bucket()
		if b.get_key(self.filename) is not None:
			b.delete_key(self.filename)

		super(Render, self).delete()

	def generate_asset_id(self):
		return '{preset}-{video}'.format(preset=self.preset.aws_preset_id, video=self.video.id)

	def generate_filename(self):
		if self.status == 'queued':
			if self.asset_id is None:
				self.asset_id = self.generate_asset_id()
			self.filename = '{filename}.{ext}'.format(filename=self.asset_id, ext=self.preset.container)
			self.save()
		return self.filename

	def get_aws_output(self):
		return {
			'PresetId': self.preset.aws_preset_id,
			'Rotate': '0',
			'ThumbnailPattern': 'thumb-' + self.asset_id + '-{count}',
			'Key': self.generate_filename()
		}