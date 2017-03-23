from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^v1/text/$', 'app.entity_detection.text'),
    url(r'^v1/location/$', 'app.entity_detection.location'),
    url(r'^v1/phone_number/$', 'app.entity_detection.phone_number'),
    url(r'^v1/email/$', 'app.entity_detection.email'),
    url(r'^v1/city/$', 'app.entity_detection.city'),
    url(r'^v1/pnr/$', 'app.entity_detection.pnr'),
    url(r'^v1/shopping_size/$', 'app.entity_detection.shopping_size'),
    url(r'^v1/number/$', 'app.entity_detection.number'),
    url(r'^v1/time/$', 'app.entity_detection.time'),
    url(r'^v1/date/$', 'app.entity_detection.date'),
    url(r'^v1/budget/$', 'app.entity_detection.budget'),
    url(r'^v1/city_advance/$', 'app.entity_detection.city_advance'),
    url(r'^v1/date_advance/$', 'app.entity_detection.date_advance'),
    url(r'^v1/ner/$', 'app.entity_detection.ner'),
    url(r'^v1/combine_output/$', 'app.entity_detection.combine_output'),
)
