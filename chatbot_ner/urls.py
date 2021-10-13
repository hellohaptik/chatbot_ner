from __future__ import absolute_import

from django.urls import re_path

from external_api import api as external_api
from ner_v1 import api as api_v1
from ner_v2 import api as api_v2

urlpatterns = [
    re_path(r'^v1/text_bulk/$', api_v1.text),
    re_path(r'^v1/text/$', api_v1.text),
    re_path(r'^v1/location/$', api_v1.location),
    re_path(r'^v1/phone_number/$', api_v1.phone_number),
    re_path(r'^v1/email/$', api_v1.email),
    re_path(r'^v1/city/$', api_v1.city),
    re_path(r'^v1/pnr/$', api_v1.pnr),
    re_path(r'^v1/shopping_size/$', api_v1.shopping_size),
    re_path(r'^v1/passenger_count/$', api_v1.passenger_count),
    re_path(r'^v1/number/$', api_v1.number),
    re_path(r'^v1/time/$', api_v1.time),
    re_path(r'^v1/time_with_range/$', api_v1.time_with_range),
    re_path(r'^v1/date/$', api_v1.date),
    re_path(r'^v1/budget/$', api_v1.budget),
    re_path(r'^v1/ner/$', api_v1.ner),
    re_path(r'^v1/combine_output/$', api_v1.combine_output),
    re_path(r'^v1/person_name/$', api_v1.person_name),
    re_path(r'^v1/regex/$', api_v1.regex),

    # V2 detectors
    re_path(r'^v2/date/$', api_v2.date),
    re_path(r'^v2/time/$', api_v2.time),
    re_path(r'^v2/number/$', api_v2.number),
    re_path(r'^v2/phone_number/$', api_v2.phone_number),
    re_path(r'^v2/number_range/$', api_v2.number_range),
    re_path(r'^v2/text/$', api_v2.text),

    # V2 bulk detectors
    re_path(r'^v2/date_bulk/$', api_v2.date),
    re_path(r'^v2/time_bulk/$', api_v2.time),
    re_path(r'^v2/number_bulk/$', api_v2.number),
    re_path(r'^v2/number_range_bulk/$', api_v2.number_range),
    re_path(r'^v2/phone_number_bulk/$', api_v2.phone_number),

    # Deprecated dictionary read write, use entities/data/v1/*
    re_path(r'^entities/get_entity_word_variants', external_api.get_entity_word_variants),
    re_path(r'^entities/update_dictionary', external_api.update_dictionary),

    # Transfer Dictioanry
    re_path(r'^entities/transfer_entities', external_api.transfer_entities),

    # Training Data Read Write
    re_path(r'^entities/get_crf_training_data', external_api.get_crf_training_data),
    re_path(r'^entities/update_crf_training_data', external_api.update_crf_training_data),

    re_path(r'^entities/languages/v1/(?P<entity_name>.+)$', external_api.entity_language_view),
    re_path(r'^entities/data/v1/(?P<entity_name>.+)$', external_api.entity_data_view),

    #  Read unique values for text entity
    re_path(r'^entities/values/v1/(?P<entity_name>.+)$', external_api.read_unique_values_for_text_entity),

]
