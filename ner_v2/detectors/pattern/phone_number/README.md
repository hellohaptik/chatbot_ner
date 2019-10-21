## Phone Number Detector 

The Phone Number Detector has the capability to detect phone numbers from within the given text. The detector has the ability to handle multi language text. Additionally, this detector is scaled to handle domestic as well as international phone numbers

 We are currently providing phone number detection support in 6 languages, which are

- English
- Hindi
- Marathi
- Gujarati
- Telugu
- Tamil

### Usage

- **Python Shell**

  ```python
  >> from ner_v2.detectors.pattern.phone_number.phone_number_detection import PhoneDetector      
  >> detector = PhoneDetector(language='en', entity_name='phone_number', locale='en-IN')
  # here language will be ISO 639-1 code and locale can be of the form 'language[-_]country_code'
  >> detector.detect_entity(text=u'send a message on 91 9820334455')
  >> ([{'country_calling_code': '91', 'phone_number': '9820334455'}],['91 9820334455'])
  ```

- **Curl Command**

  ```bash
  # For a sample query with following parameters
  # message="Call 022 2612985 and send 100 rs to +919820334416 and 1(408) 234-6192"
  # entity_name='phone_number'
  # structured_value=None
  # fallback_value=None
  # bot_message=None
  # source_language='en'
  # locale='en-us'

  $ URL='localhost'
  $ PORT=8081

 $ curl -i 'http://'$URL':'$PORT'v2/phone_number?entity_name=phone_number&message=Call%20022%202612985%20and%20send%20100%20rs%20to%20%2B919820334416%20and%201(408)%20234-6192&source_language=en&locale=en-us&structured_value=&fallback_value=&bot_message=' -H 'cache-control: no-cache' -H 'postman-token: dad3f116-37f2-2627-b8c6-f89f00f19924'
  # Curl output
  $ {
    "data": [
        {
            "detection": "message",
            "original_text": "022 2612985",
            "entity_value": {
                "phone_number": "222612985",
                "country_calling_code": "1"
            },
            "language": "en"
        },
        {
            "detection": "message",
            "original_text": "+919820334416",
            "entity_value": {
                "phone_number": "9820334416",
                "country_calling_code": "91"
            },
            "language": "en"
        },
        {
            "detection": "message",
            "original_text": "1(408) 234-6192",
            "entity_value": {
                "phone_number": "4082346192",
                "country_calling_code": "1"
            },
            "language": "en"
        }
    ]
}
  ```