from __future__ import absolute_import

from django.conf.urls import url

from ner_v1 import api as api_v1
from ner_v2 import api as api_v2

from external_api import api as external_api


urlpatterns = [
    url(r'^v1/text_bulk/$', api_v1.text),
    url(r'^v1/text/$', api_v1.text),
    url(r'^v1/location/$', api_v1.location),
    url(r'^v1/phone_number/$', api_v1.phone_number),
    url(r'^v1/email/$', api_v1.email),
    url(r'^v1/city/$', api_v1.city),
    url(r'^v1/pnr/$', api_v1.pnr),
    url(r'^v1/shopping_size/$', api_v1.shopping_size),
    url(r'^v1/passenger_count/$', api_v1.passenger_count),
    url(r'^v1/number/$', api_v1.number),
    url(r'^v1/time/$', api_v1.time),
    url(r'^v1/time_with_range/$', api_v1.time_with_range),
    url(r'^v1/date/$', api_v1.date),
    url(r'^v1/budget/$', api_v1.budget),
    url(r'^v1/ner/$', api_v1.ner),
    url(r'^v1/combine_output/$', api_v1.combine_output),
    url(r'^v1/person_name/$', api_v1.person_name),
    url(r'^v1/regex/$', api_v1.regex),

    # V2 detectors
    url(r'^v2/date/$', api_v2.date),
    url(r'^v2/time/$', api_v2.time),
    url(r'^v2/number/$', api_v2.number),
    url(r'^v2/phone_number/$', api_v2.phone_number),
    url(r'^v2/number_range/$', api_v2.number_range),
    url(r'^v2/text/$', api_v2.text),

    # V2 bulk detectors
    url(r'^v2/date_bulk/$', api_v2.date),
    url(r'^v2/time_bulk/$', api_v2.time),
    url(r'^v2/number_bulk/$', api_v2.number),
    url(r'^v2/number_range_bulk/$', api_v2.number_range),
    url(r'^v2/phone_number_bulk/$', api_v2.phone_number),

    # Dictionary Read Write
    url(r'^entities/get_entity_word_variants', external_api.get_entity_word_variants),
    url(r'^entities/update_dictionary', external_api.update_dictionary),

    # Transfer Dictioanry
    url(r'^entities/transfer_entities', external_api.transfer_entities),

    # Training Data Read Write
    url(r'^entities/get_crf_training_data', external_api.get_crf_training_data),
    url(r'^entities/update_crf_training_data', external_api.update_crf_training_data),

    #  Train Crf Model
    url(r'^entities/train_crf_model', external_api.train_crf_model),

    url(r'^entities/languages/v1/(?P<entity_name>.+)$', external_api.entity_language_view),
    url(r'^entities/data/v1/(?P<entity_name>.+)$', external_api.entity_data_view),

    #  Read unique values for text entity
    url(r'^entities/values/v1/(?P<entity_name>.+)$', external_api.read_unique_values_for_text_entity),

]
