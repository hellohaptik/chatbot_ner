External API Documentation
=================

***

### Get languages supported by an entity ###


**URL:** entities/languages/v1/<entity_name>

**Method:** GET

**Supported Query Params:**
None

**Response:**
```json
{
    "result": {
        "supported_languages": [
            "en",
            "hi",
            "mr"
        ]
    },
    "success": true,
    "error": ""
}
```

***
### Add language support for an entity ###

**URL:** entities/languages/v1/<entity_name>

**Method:** POST

**Request Body**
```json
{
    "supported_languages": [
        "en",
        "hi",
        "mr"
    ]
}
```
**Response:**
```json
{
    "result": true,
    "success": true,
    "error": ""
}
```

***
### Get data associated with the specific entity ###

**URL:** entities/data/v1/<entity_name>

**Method:** GET

**Supported Query Params:**

- value_search_term (str): Search term to filter entity values
- variant_search_term (str): Search term to filter entiy variants
- empty_variants_only (bool): Filter only values with empty variants
- pagination_from (int): Filter results offset for pagination
- pagination_size (int): Filter results size for pagination

**Response:**
```json
{
    "result": {
        "records": [
            {
                "variants": {
                    "hi": {
                        "_id": "AWhgNBQdLvkU3x32pO7K",
                        "value": [
                            "दिल्ली"
                        ]
                    },
                    "en": {
                        "_id": "AWhgNBQdLvkU3x32pO7L",
                        "value": [
                            "Delhi"
                        ]
                    }
                },
                "word": "Delhi"
            },
            {
                "variants": {
                    "hi": {
                        "_id": "AWhgNBQdLvkU3x32pO7I",
                        "value": [
                            "इंडिया"
                        ]
                    },
                    "en": {
                        "_id": "AWhgNBQdLvkU3x32pO7J",
                        "value": [
                            "India"
                        ]
                    }
                },
                "word": "India"
            }
        ],
        "total": 2
    },
    "success": true,
    "error": ""
}
```

***
### Add/Edit/Remove data associated with a specific entity ###

**URL:** entities/data/v1/<entity_name>

**Method:** POST

**Request Body:**
```json
```
**Response:**
```json
```
