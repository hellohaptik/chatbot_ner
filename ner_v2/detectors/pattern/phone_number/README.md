## Phone Number Detector 

The Phone Number Detector has the capability to detect phone numbers from within the given text. The detector has the ability to handle multilanguage text. Additionally, this detector is scaled to handle domestic as well as international phone numbers

 We are currently providing phone number detection support in 6 languages, which are

- English
- Hindi
- Marathi
- Gujarati
- Telgu
- Tamil

### Usage

- **Python Shell**

  ```python
  >> from ner_v2.detectors.pattern.phone_number.phone_number_detection import PhoneDetector      
  >> detector = PhoneDetector(language='en', entity_name='phone_number') # here language will be ISO 639-1 code
  >> detector.detect_entity(text=u'send a message on 91 9820334455')
  >> (['919820334455'], [u'91 9820334455'])
  ```

- **Curl Command**

  ```bash
  # For a sample query with following parameters
  # message="Call 022 26129857 and send 100 rs to +919820334416 and 1(408) 234-619"
  # entity_name='phone_number'
  # structured_value=None
  # fallback_value=None
  # bot_message=None
  # source_language='en'

  $ URL='localhost'
  $ PORT=8081

  $ curl -i 'http://'$URL':'$PORT'/v2/phone_number?message=Call%20022%2026129857%20and%20send%20100%20rs%20to%20+919820334416%20and%201%28408%29%20234-619&entity_name=phone_number&fallback_value=&bot_message=&structured_value=&source_language=en'

  # Curl output
  $ {
      "data": [
          {
              "detection": "message",
              "original_text": "022 26129857",
              "entity_value": {
                  "value": "02226129857"
              },
              "language": "en"
          },
          {
              "detection": "message",
              "original_text": "919820334416",
              "entity_value": {
                  "value": "919820334416"
              },
              "language": "en"
          },
          {
              "detection": "message",
              "original_text": "1(408) 234-619",
              "entity_value": {
                  "value": "1408234619"
              },
              "language": "en"
          }
      ]
  }
  ```