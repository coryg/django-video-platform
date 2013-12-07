Django Video Platform
=====================

A video management workflow based on Amazon Web Services

Requirements
-----------
* Boto
* A Cup of Coffee (For Now)

Quick start
-----------

1. Add "video" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = (
        ...
        'video',
    )

2. Include the polls URLconf in your project urls.py like this::

    url(r'^videos/', include('video.urls')),

3. Run `python manage.py syncdb` to create the polls models.

4. Start the development server and visit http://127.0.0.1:8000/admin/
   to manage your videos (you'll need the Admin app enabled).


What is Working:
-----------
* Importing of Pipelines and Listing videos in Buckets.

What is Needed:
-----------
* Status monitoring for transcoding jobs
* Video player HTML generation
* Uploading directly from browser
* MUCH better documentation
* Remove References to original project