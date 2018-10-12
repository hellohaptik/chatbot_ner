from django.conf.urls import patterns, include, url
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^v1/text/$', 'ner_v2.api.text'),
    url(r'^v1/location/$', 'ner_v2.api.location'),
    url(r'^v1/phone_number/$', 'ner_v2.api.phone_number'),
    url(r'^v1/email/$', 'ner_v2.api.email'),
    url(r'^v1/city/$', 'ner_v2.api.city'),
    url(r'^v1/pnr/$', 'ner_v2.api.pnr'),
    url(r'^v1/shopping_size/$', 'ner_v2.api.shopping_size'),
    url(r'^v1/passenger_count/$', 'ner_v2.api.passenger_count'),
    url(r'^v1/number/$', 'ner_v2.api.number'),
    url(r'^v1/time/$', 'ner_v2.api.time'),
    url(r'^v1/time_with_range/$', 'ner_v2.api.time_with_range'),
    url(r'^v1/date/$', 'ner_v2.api.date'),
    url(r'^v1/budget/$', 'ner_v2.api.budget'),
    url(r'^v1/ner/$', 'ner_v2.api.ner'),
    url(r'^v1/combine_output/$', 'ner_v2.api.combine_output'),
    url(r'^v1/person_name/$', 'ner_v2.api.person_name'),
    url(r'^v1/regex/$', 'ner_v2.api.regex'),

    # Dictionary Read Write
    url(r'^entities/get_entity_word_variants', 'external_api.api.get_entity_word_variants'),
    url(r'^entities/update_dictionary', 'external_api.api.update_dictionary'),

    # Transfer Dictioanry
    url(r'^entities/transfer_entities', 'external_api.api.transfer_entities'),

    # Training Data Read Write
    url(r'^entities/get_crf_training_data', 'external_api.api.get_crf_training_data'),
    url(r'^entities/update_crf_training_data', 'external_api.api.update_crf_training_data'),

    #  Train Crf Model
    url(r'^entities/train_crf_model', 'external_api.api.train_crf_model'),
)
