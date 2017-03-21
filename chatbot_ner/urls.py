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

"""
curl -i 'http://localhost:8000/v1/text/?message=i%20want%20to%20order%20chinese%20from%20%20mainland%20china%20and%20pizza%20from%20domminos&entity_name=restaurant&structured_value=&structured_value_verification=&fallback_value=None&expert_message='
{"data": [{"detection": "message", "original_text": "mainland china", "entity_value": "Mainland China"}, {"detection": "message", "original_text": "domminos", "entity_value": "Domino's Pizza"}]}

curl -i 'http://localhost:8000/v1/text/?message=i%20wanted%20to%20watch%20movie&entity_name=movie&structured_value=inferno&structured_value_verification=0&fallback_value=None&expert_message='
{"data": [{"detection": "structure_value_verified", "original_text": "inferno", "entity_value": "Inferno"}]}

curl -i 'http://localhost:8000/v1/phone_number/?message=my%20contact%20number%20is%209049961794&entity_name=phone_number&structured_value=&structured_value_verification=0&fallback_value=None&expert_message='
{"data": [{"detection": "message", "original_text": "9049961794", "entity_value": "9049961794"}]}

curl -i 'http://localhost:8000/v1/phone_number/?message=Please%20call%20me&entity_name=phone_number&structured_value=&structured_value_verification=&fallback_value=9049961794&expert_message='
{"data": [{"detection": "fallback_value", "original_text": "9049961794", "entity_value": "9049961794"}]}

curl -i 'http://localhost:8000/v1/email/?message=my%20email%20id%20is%20apurv.nagvenkar%40gmail.com&entity_name=email&structured_value=&structured_value_verification=&fallback_value=&expert_message='
{"data": [{"detection": "message", "original_text": "apurv.nagvenkar@gmail.com", "entity_value": "apurv.nagvenkar@gmail.com"}]}

curl -i 'http://localhost:8000/v1/email/?message=send%20me%20the%20email&entity_name=email&structured_value=&structured_value_verification=&fallback_value=apurv.nagvenkar@gmail.com&expert_message='
{"data": [{"detection": "fallback_value", "original_text": "apurv.nagvenkar@gmail.com", "entity_value": "apurv.nagvenkar@gmail.com"}]}

curl -i 'http://localhost:8000/v1/city/?message=i%20want%20to%20go%20to%20mummbai&entity_name=city&structured_value=&structured_value_verification=&fallback_value=&expert_message='
{"data": [{"detection": "message", "original_text": "mummbai", "entity_value": "Mumbai"}]}

curl -i 'http://localhost:8000/v1/pnr/?message=check%20my%20pnr%20status%20for%202141215305.&entity_name=pnr&structured_value=&structured_value_verification=&fallback_value=&expert_message='
{"data": [{"detection": "message", "original_text": "2141215305", "entity_value": "2141215305"}]}

curl -i 'http://localhost:8000/v1/numeric/?message=I%20want%20to%20purchase%2030%20units%20of%20mobile%20and%2040%20units%20of%20Television&entity_name=number_of_unit&structured_value=&structured_value_verification=&fallback_value=&expert_message='
{"data": [{"detection": "message", "original_text": "30", "entity_value": "30"}, {"detection": "message", "original_text": "40", "entity_value": "40"}]}

curl -i 'http://localhost:8000/v1/numeric/?message=I%20want%20to%20reserve%20a%20table%20for%203%20people&entity_name=number_of_people&structured_value=&structured_value_verification=&fallback_value=&expert_message='
{"data": [{"detection": "message", "original_text": "for 3 people", "entity_value": "3"}]}

curl -i 'http://localhost:8000/v1/time/?message=John%20arrived%20at%20the%20bus%20stop%20at%2013%3A50%20hrs%2C%20expecting%20the%20bus%20to%20be%20there%20in%2015%20mins.%20But%20the%20bus%20was%20scheduled%20for%2012%3A30%20pm&entity_name=time&structured_value=&structured_value_verification=&fallback_value=&expert_message='
{"data": [{"detection": "message", "original_text": "12:30 pm", "entity_value": {"mm": 30, "hh": 12, "nn": "pm"}}, {"detection": "message", "original_text": "in 15 mins", "entity_value": {"mm": "15", "hh": 0, "nn": "df"}}, {"detection": "message", "original_text": "13:50", "entity_value": {"mm": 50, "hh": 13, "nn": "hrs"}}]}

curl -i 'http://localhost:8000/v1/date/?message=set%20me%20reminder%20on%2023rd%20december&entity_name=date&structured_value=&structured_value_verification=&fallback_value=&expert_message='
{"data": [{"detection": "message", "original_text": "23rd december", "entity_value": {"mm": 12, "yy": 2017, "dd": 23, "type": "date"}}]}

curl -i 'http://localhost:8000/v1/date/?message=set%20me%20reminder%20day%20after%20tomorrow&entity_name=date&structured_value=&structured_value_verification=&fallback_value=&expert_message='
{"data": [{"detection": "message", "original_text": "day after tomorrow", "entity_value": {"mm": 3, "yy": 2017, "dd": 13, "type": "day_after"}}]}

curl -i 'http://localhost:8000/v1/city_advance/?message=I%20want%20to%20book%20a%20flight%20from%20delhhi%20to%20mumbai&entity_name=city&structured_value=&structured_value_verification=&fallback_value=&expert_message='
{"data": [{"detection": "message", "original_text": "from delhhi to mumbai", "entity_value": {"departure_city": "New Delhi", "arrival_city": "Mumbai"}}]}

curl -i 'http://localhost:8000/v1/city_advance/?message=mummbai&entity_name=city&structured_value=&structured_value_verification=&fallback_value=&expert_message=Please%20help%20me%20departure%20city%3F'
{"data": [{"detection": "message", "original_text": "mummbai", "entity_value": {"departure_city": "Mumbai", "arrival_city": null}}]}

curl -i 'http://localhost:8000/v1/date_advance/?message=21st%20dec&entity_name=date&structured_value=&structured_value_verification=&fallback_value=&expert_message=Please%20help%20me%20with%20return%20date%3F'
{"data": [{"detection": "message", "original_text": "21st dec", "entity_value": {"date_return": {"mm": 12, "yy": 2017, "dd": 21, "type": "date"}, "date_departure": null}}]}

curl -i 'http://localhost:8000/v1/ner/?entities=\[%22date%22,%22time%22,%22restaurant%22\]&message=Reserve%20me%20a%20table%20today%20at%206:30pm%20at%20Mainland%20China%20and%20on%20Monday%20at%207:00pm%20at%20Barbeque%20Nation'
{"data": {"tag": "reserve me a table __date__ at __time__ at __restaurant__ and on monday at __time__ at __restaurant__", "entity_data": {"date": [{"detection": "message", "original_text": "today", "entity_value": {"mm": 3, "yy": 2017, "dd": 13, "type": "day_within_one_week"}}], "time": [{"detection": "message", "original_text": "6:30pm", "entity_value": {"mm": 30, "hh": 6, "nn": "pm"}}, {"detection": "message", "original_text": "7:00pm", "entity_value": {"mm": 0, "hh": 7, "nn": "pm"}}], "restaurant": [{"detection": "message", "original_text": "barbeque nation", "entity_value": "Barbeque Nation"}, {"detection": "message", "original_text": "mainland china", "entity_value": "Mainland China"}]}}}

"""
