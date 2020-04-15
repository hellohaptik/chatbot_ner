## DataStore Environment Variables Description

A `config.example` file is provided at the root of the repository. It is an example file containing all variables that Chatbot NER sets in the environment for future use when connecting to the underlying engine.

Copy it to a file called `config` at the root of the repository and edit it to configure your settings. Chatbot NER will read and set variables from this file into the environment.

> **Note**: Do not use quotes while specifying values for variables. Do not put spaces around the '=' sign.
>
> Invalid Example:
>
>     ENGINE='elasticsearch'
>     ES_HOST = YOURHOST.us-east-1.es.amazonaws.com
>
> Valid Example:
>
>     ENGINE=elasticsearch
>     ES_HOST=YOURHOST.us-east-1.es.amazonaws.com

#### Variables

---------------

- `ENGINE`

  This specifies the which engine to use. In case multiple engines are supported and configured in the `config` file, the settings under the value provided by `ENGINE` are used. In other words, the value of `ENGINE` is used as key to access its connection settings from the constructed dictionary as shown above.

  At this point only Elasticsearch is supported and valid values for engine are:	

  | Engine        | `ENGINE` value |
  | ------------- | -------------- |
  | Elasticsearch | elasticsearch  |

- **ELASTICSEARCH Settings**

  All Elasticsearch related settings variables have `ES` in prefix

  | Variable Name      | Description                              |
  | ------------------ | ---------------------------------------- |
  | `ES_URL`           | The complete connection url, containing protocol, host and port and optionally username and password for basic authentication. When provided, this will override values for `ES_HOST`, `ES_PORT`, `ES_AUTH_NAME` and `ES_AUTH_PASSWORD` <br/>E.g.<br/>`https://user:secret@localhost:443`,<br/>`http://user:secret@localhost:9200/development/` |
  | `ES_HOST`          | Elasticsearch host address<br/>E.g.<br/>`localhost`,<br/>`127.0.0.1`,<br/>`YOURHOST.us-east-1.es.amazonaws.com` |
  | `ES_PORT`          | Elasticsearch service port, (usually http service)<br/>E.g.<br/>`9200`,<br/> `443` |
  | `ES_ALIAS`         | Alias to put index under for Elasticsearch.<br/>E.g.<br/>`chatbot_ner_alias` |
  | `ES_INDEX_1`       | Index name for Elasticsearch.<br/>E.g.<br/>`chatbot_ner_index` |
  | `ES_DOC_TYPE`      | Document type for elasticsearch. If not provided defaults to `data_dictionary`. |
  | `ES_AUTH_NAME`     | Name for basic http authentication. Optional if http authentication is not needed. |
  | `ES_AUTH_PASSWORD` | Password/Secret for basic http authentication. Optional if http authentication is not needed. |
  | `ES_BULK_MSG_SIZE` | Maximum size for Elasticsearch bulk queries. If not provided defaults to `10000`. |

  ***For AWS Elasticsearch Authentication***

  To use IAM based authentication on AWS, provide the following variables in the `config` file. These variables make up a `http_auth` object.
  
  | Variable Name              | Description                        |
  | -------------------------- | ---------------------------------- |
  | `ES_AWS_SECRET_ACCESS_KEY` | AWS Secret Key                     |
  | `ES_AWS_ACCESS_KEY_ID`     | AWS Access Key                     |
  | `ES_AWS_REGION`            | AWS Region (e.g. us-west-2)        |
  | `ES_AWS_SERVICE`           | AWS Service name, Defaults to 'es' |

  These variables are passed onto [requests-aws4auth](https://pypi.python.org/pypi/requests-aws4auth)
  See  http://elasticsearch-py.readthedocs.io/en/master/index.html?highlight=AWS#running-on-aws-with-iam



#### Example `config` file

----------

Please check [config.example](../config.example) file

