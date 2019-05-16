import yaml
import io
import pandas as pd
import sys

"""
Script to convert YAML test cases to csv format to be translated.
The csv file will contain the message and the corresponding original text to be translated.
Each test case is identified by a unique id.
"""

yaml_filepath = sys.argv[1]
file_name = yaml_filepath.split(".")[0]
yaml_data = yaml.load(io.open(yaml_filepath, "r", encoding="utf-8"))
csv_data = []
for language in yaml_data["tests"]:
    for i, testcase in enumerate(yaml_data["tests"][language]):
        test_id = testcase["_id_"]
        message = testcase["message"]
        for output in testcase["outputs"]:
            output_id = output["output_id"]
            original_text = output["original_text"]
            csv_data.append(["{}-{}".format(test_id, output_id), language, message, original_text])

df = pd.DataFrame(csv_data, columns=["unique_id", "language", "message", "original_text"])
df.to_csv("{}.csv".format(file_name), index=False, encoding="utf-8")
