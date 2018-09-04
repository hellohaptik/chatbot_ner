from django.conf.urls import patterns, include, url
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^v1/text/$', 'ner_v1.api.text'),
    url(r'^v1/location/$', 'ner_v1.api.location'),
    url(r'^v1/phone_number/$', 'ner_v1.api.phone_number'),
    url(r'^v1/email/$', 'ner_v1.api.email'),
    url(r'^v1/city/$', 'ner_v1.api.city'),
    url(r'^v1/pnr/$', 'ner_v1.api.pnr'),
    url(r'^v1/shopping_size/$', 'ner_v1.api.shopping_size'),
    url(r'^v1/number/$', 'ner_v1.api.number'),
    url(r'^v1/time/$', 'ner_v1.api.time'),
    url(r'^v1/time_with_range/$', 'ner_v1.api.time_with_range'),
    url(r'^v1/date/$', 'ner_v1.api.date'),
    url(r'^v1/budget/$', 'ner_v1.api.budget'),
    url(r'^v1/ner/$', 'ner_v1.api.ner'),
    url(r'^v1/combine_output/$', 'ner_v1.api.combine_output'),
    url(r'^v1/person_name/$', 'ner_v1.api.person_name'),
    url(r'^v1/regex/$', 'ner_v1.api.regex'),

    # Dictionary Read Write
    url(r'^entities/get_entity_word_variants', 'external_api.api.get_entity_word_variants'),
    url(r'^entities/update_dictionary', 'external_api.api.update_dictionary'),

    # Transfer Dictioanry
    url(r'^entities/transfer_entities', 'external_api.api.transfer_entities'),

)
