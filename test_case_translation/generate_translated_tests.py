# -*- coding: utf-8 -*-
import io
import pandas as pd
import sys
from operator import itemgetter


def match_output_to_translated_test(yaml_tests, translated_data):
    from ruamel import yaml
    yaml.preserve_quotes = True
    double_quote = yaml.scalarstring.DoubleQuotedScalarString
    """
    Function to map outputs to translated test cases if len(translated_data) == len(yaml_tests)
    Args:
        yaml_tests (list of dicts): Original test cases(english or hindi).
        translated_data(list of dicts): Translated test cases for a given language to be mapped to respective outputs

    Eg.
    yaml_tests = [
                    {
                     'id': 'en_1', 'message': 'the time is 12:35 am',
                     'outputs': [
                                    {
                                        'hh': 12, 'mm': 35, 'nn': 'am', 'original_text': '12:35 am',
                                        'output_id': 1, 'range': None, 'time_type': None
                                    }
                                ],
                    'range_enabled': False
                    }
                ]

    translated_data = [
                        {
                            'id': 'en_1',
                            'rows': [
                                        {
                                            'unique_id': 'en_1-1', 'language': 'mr',
                                            'message': 'वेळ 12:35 वाजत आहे', 'original_text': '12:35',
                                            'id': 'en_1', 'output_id': '1'
                                        }
                                    ]
                        }
                    ]

    >> match_output_to_translated_test(yaml_tests, translated_data)
    Output:
        [
                    {
                     'id': 'en_1', 'message': 'वेळ 12:35 वाजत आहे',
                     'outputs': [
                                    {
                                        'hh': 12, 'mm': 35, 'nn': 'am', 'original_text': '12:35',
                                        'output_id': 1, 'range': None, 'time_type': None
                                    }
                                ],
                    'range_enabled': False
                    }
                ]

    Returns:
        translated_tests (dict): translated test cases matched with respective outputs.
    """
    translated_tests = {}
    language = None
    for yaml_test, translated_test in zip(yaml_tests, translated_data):
        yaml_test.update({"message": double_quote(translated_test["rows"][0]["message"])})

        if not language:
            language = translated_test["rows"][0]["language"]

        for output_index in range(len(yaml_test["outputs"])):

            for key in yaml_test["outputs"][output_index].keys():
                value = yaml_test["outputs"][output_index][key]
                if not isinstance(value, (int, type(None), float, bool)):
                    if key != "original_text":
                        yaml_test["outputs"][output_index][key] = double_quote(value)

            for i in range(len(translated_test["rows"])):
                if yaml_test["outputs"][output_index]["output_id"] == translated_test["rows"][i]["output_id"]:
                    original_text = translated_test["rows"][i]["original_text"]
                    yaml_test["outputs"][output_index].update(
                        {"original_text": double_quote(original_text) if not pd.isna(original_text) else None})

        if language not in translated_tests:
            translated_tests.update({language: []})
        translated_tests[language].append(yaml_test)

    return translated_tests, language


def match():
    """
    Function to map outputs to translated test cases if len(translated_data) == len(yaml_tests)
    Returns:

    """
    pass


def my_represent_none(self, data):
    """
    yaml representer for NoneType
    """
    return self.represent_scalar(u"tag:yaml.org,2002:null", u"null")


def main():
    from ruamel import yaml
    yaml.RoundTripRepresenter.add_representer(type(None), my_represent_none)
    yaml_filepath = sys.argv[1]
    file_name = yaml_filepath.split(".yaml")[0]
    yaml_data = yaml.load(io.open(yaml_filepath, "r", encoding="utf-8"), Loader=yaml.Loader)
    yaml_tests = []
    args = yaml_data.get("args", None)
    for language in yaml_data["tests"]:
        yaml_tests.extend(yaml_data["tests"][language])

    csv_filepath = sys.argv[2]
    csv_data = pd.read_csv(csv_filepath, encoding="utf-8")
    csv_rows = csv_data.to_dict(orient="records")
    csv_data["id"] = csv_data["unique_id"].apply(lambda x: x.split("-")[0])
    csv_data["output_id"] = csv_data["unique_id"].apply(lambda x: int(x.split("-")[1]))

    translated_data = []
    test_groups = csv_data.groupby("id")
    for test_case_id, test_case_df in test_groups:
        translated_data.append({"id": test_case_id, "rows": test_case_df.to_dict(orient="records")})

    if yaml_tests and translated_data:
        if len(yaml_tests) == len(translated_data):
            yaml_tests, translated_data = [sorted(l, key=itemgetter('id')) for l in (yaml_tests, translated_data)]
            output_tests, language = match_output_to_translated_test(yaml_tests, translated_data)
            if language is not None:
                yaml.round_trip_dump({"args": args, "tests": output_tests},
                                     io.open("{file_name}_{language}.yaml".format(file_name=file_name,
                                                                                  language=language), "w",
                                             encoding="utf-8"),
                                     default_flow_style=False,
                                     allow_unicode="utf-8")
            else:
                raise Exception('No language found. Filename: {}'.format(csv_filepath))
    else:
        if yaml_tests:
            raise Exception(
                "Empty translated data. {filename} might not be in proper format".format(filename=csv_filepath))
        elif translated_data:
            raise Exception("Empty yaml tests {filename} might not be in proper format".format(filename=yaml_filepath))
        else:
            raise Exception("{filename1} and {filename2} might not be proper format".format(filename1=yaml_filepath,
                                                                                            filename2=csv_filepath))


main()
