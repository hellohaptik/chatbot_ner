## CSV file structure and adding new entities to DataStore

Following csv files are already included in the repository at `data/entity_data/` . These contain entity values that Haptik uses for their operations.

| Filename       | Description                              |
| -------------- | ---------------------------------------- |
| brand.csv      | Brand names of various shopping brands   |
| budget.csv     | Commonly used units used for specifying money amount - (hundred, thousand, lakhs) |
| city.csv       | Indian city names and their variations   |
| clothes.csv    | apparel types                            |
| cuisine.csv    | food cuisines                            |
| day_list.csv   | day of the week names and thier short forms - Mon, Tue, etc |
| dish.csv       | Indian food dish names                   |
| footwear.csv   | footwear types - shoes, boots, etc       |
| locality.csv   | Selected locality/area/street names in India |
| month_list.csv | month names and and thier short forms    |
| movie.csv      | Selected few Indian movie names          |
| restaurant.csv | Selected Indian restaurant names         |

### Format

-----------

Chatbot ner reads data from these csv files and puts them into the datastore under a entity named after the filename of the csv file. 

> *csv filename should contain only lowercase english alphabets and '_' (underscore) symbol*

Each line of the csv file contains two values separated by a comma.

- First is the entity value - the expected value in a ideal case and you would want to use while any computation

- Second is a list containing values of variants (and possibly expected spelling errors) and synonyms for this entity value separated by '|'. We want to use the entity value (first part) if any of these are detected in the text.

  > *All special symbols are allowed in variants and synonyms values except ',' (comma) and '|' (vertical bar)*
  >
  > *Avoid adding '|' (vertical bar) at the end of the line*

**Example:**

Let's take an example - we want to build a natural language email search agent. We would require to detect mentions of email attachment types in such search queries. Users may specify such attachments by their file extensions or their commonly known file types. 

Example `"Show me all the word documents I received in the last week"` or `"Download the pdf attacthed in the email from Air India"`

We will go ahead and make a csv called `attachment_types.csv`

Then we will fill in our data as follows:

```
pdf,pdf|pdfs
doc,doc|docx|word document|rtf|word documents
image,png|jpeg|jpg|png|bmp|gif|image|images
plain_text,txt
excel_sheet,xls|xlsx|csv|spreadsheet|spread sheet|excel sheet|sheets
audio,mp3|aac|wav
video,mp4|mkv|mov
```

### Adding new data from csv file to datastore

--------

Now lets add the newly created csv file to the datastore. 

- Make sure to start the engine you configured with datastore( eg. elasticsearch)

  ```shell
  $ ~/chatbot_ner_elasticsearch/elasticsearch-2.4.4/bin/elasticsearch -d
  ```

- Activate chatbot_ner virtual environment

  ```shell
  $ source /usr/local/bin/virtualenvwrapper.sh
  $ workon chatbotnervenv
  ```

- Start a `manage.py shell` as follows

  ```bash
  $ # change to your repository clone directory
  $ cd ~/chatbot_ner/
  $ python manage.py shell
  ```

- Now run the following

  ```python
  from datastore import DataStore
  csv_file = '~/attachment_types.csv' # example file path to the csv file
  db = DataStore()
  db.populate(csv_file_paths=[csv_file,])
  ```

  In case, you want to add multiple csv files at once, you can pass the directory path to `entity_data_directory_path` parameter of `populate` method as follows:

  ```python
  from datastore import DataStore
  csv_directory = '~/my_csv_files/' # example directory path containing csv files
  db = DataStore()
  db.populate(entity_data_directory_path=csv_directory)
  ```

### Updating the DataStore after editing a csv file

---------

After editing and saving your csv, you will need to update the datastore with new data. For this you need to call `repopulate()` on DataStore. It follows the same API as `populate()`

> **Note:** The filename needs to be same as it was before editing the file. If the new data is saved under a different filename it would be populated as a new entity with the name same as new file name.

> Make sure you are working in chatbotnervenv virtual environment and datastore engine is running. See above section

On a `manage.py shell` run

```python
from datastore import DataStore
csv_file = '~/attachment_types.csv' # example file path to the csv file
db = DataStore()
db.repopulate(csv_file_paths=[csv_file,])
```

 In case, you want to update multiple csv files at once, you can pass the directory path to `entity_data_directory_path` parameter of `populate` method as follows:

```python
from datastore import DataStore
csv_directory = '~/my_csv_files/' # example directory path containing csv files
db = DataStore()
db.repopulate(entity_data_directory_path=csv_directory)
```

### Deleting entity data

-----------

To delete all data for entity, simply call `delete_entity()` on Datastore. It takes one argument- the name of the entity. This is the same as the name of the csv file used for this entity while populating its data.

> Make sure you are working in chatbotnervenv virtual environment and datastore engine is running. See above section

On a `manage.py shell` run

```python
from datastore import DataStore
db = DataStore()
db.delete_entity(entity_name='attachment_types')
  ```
