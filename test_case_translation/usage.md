## Install requirements
In addition to chatbot_ner requirements.  
`pip install ruamel.yaml`

## Create csv from existing test cases.
`python yaml_to_csv.py /path/to/existing_file.yaml`

This command will create a new csv file at `/path/to/existing_file.csv`
This new csv will contain `message` and `original_text` from existing test cases with a corresponding `unique_id` and `language`.

## Map outputs from old test cases to new translated test cases.

`python generate_translated_tests.py /path/to/existing_file.yaml /path/to/translated_csv.csv `

This will create a new yaml file with translated test cases at path `/path/to/existing_file_<"language">.yaml`

## Example -  Test cases for time detection.

`python yaml_to_csv.py ../ner_v2/tests/temporal/time/time_ner_tests.yaml`

Creates a csv file at ner_v2/tests/temporal/time/time_ner_tests.csv
Get this file translated to marathi language

`python generate_translated_tests.py ../ner_v2/tests/temporal/time/time_ner_tests.yaml /path/to/translated_csv.csv`

Creates a new yaml file with test cases in marathi at `ner_v2/tests/temporal/time/time_ner_tests_mr.yaml`
