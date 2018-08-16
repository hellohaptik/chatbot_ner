import requests
import json
import logging
from elasticsearch import Elasticsearch, RequestsHttpConnection
from elasticsearch import helpers
from chatbot_ner.config import CHATBOT_NER_DATASTORE

logger = logging.getLogger('exception')


class IndexNotFoundException(Exception):
    """
    This exception will be raised if index is not found in ES
    """
    pass


class InvalidESURLException(Exception):
    """
    This exception will be raised if the ES URL is invalid
    """
    pass


class SourceDestinationSimilarException(Exception):
    """
    This exception will be raised if source is the same as destination
    """
    pass


class InternalBackupException(Exception):
    """
    This exception will be raised for transfer of documents from one index to other within a ES URL
    """
    pass


class AliasNotFoundException(Exception):
    """
    This exception will be raised if alias not found in ES
    """
    pass


class PointIndexToAliasException(Exception):
    """
    This exception is raised if the assignment of an index to an alias fails
    """
    pass


class FetchIndexForAliasException(Exception):
    """
    This exception is raised if fetch for indices for an alias fails
    """
    pass


class DeleteIndexFromAliasException(Exception):
    """
    This exception is raised if deletion of an index from an alias fails
    """
    pass


class ESTransfer(object):

    def __init__(self, source, destination):
        """
        Constructor to initialize the ESTransfer object

        Args
            source (string): source elastic search url with port e.g. http://localhost:9200
            destination (string): destination elastic search url with port e.g. http://localhost:9400
            index_name (string): index to be transferred from source to destination
        """
        self.source = source
        self.destination = destination
        self.es_index_1 = CHATBOT_NER_DATASTORE.get('elasticsearch').get('es_index_1')
        self.es_index_2 = CHATBOT_NER_DATASTORE.get('elasticsearch').get('es_index_2')
        self.es_alias = CHATBOT_NER_DATASTORE.get('elasticsearch').get('es_alias')

    def _validate_source_destination_index_name(self):
        """
        This function validates source, destination, index
        """
        # validation phase
        if self.source == self.destination:
            raise SourceDestinationSimilarException("source and destination cannot be the same")

        if not self.source or not self.destination:
            raise InvalidESURLException("invalid source or destination")

    @staticmethod
    def check_if_alias_exists(es_url, alias_name):
        """
        This function checks if alias exists in ES URL

        Args
            es_url (str): The elasticsearch URL
            alias_name (str): The name of the alias to check the existence for
        """
        response = requests.get(es_url + '/_cat/aliases?v')
        if alias_name not in response.content:
            raise AliasNotFoundException(alias_name + ' does not exist in ' + es_url)

    def _validate_alias_and_index(self):
        # check if 'self.es_index_1' and 'self.es_index_2' exist in source
        self.check_if_index_exits(self.source, self.es_index_1)
        self.check_if_index_exits(self.source, self.es_index_2)

        # check is ' alias exists in destination
        self.check_if_alias_exists(self.destination, self.es_alias)

    @staticmethod
    def check_if_index_exits(es_url, index_name):
        """
        This function checks if index exists in es_url

        Args
        es_url (string): The elsticsearch URL
        index_name (string): Name of the index to check the existence for
        """
        index_response = requests.get('{es_url}/_cat/indices?v'.format(**{"es_url": es_url}))
        # check if index is present in source
        if " " + index_name + " " not in index_response.content:
            message = index_name + " does not exist in " + es_url
            logger.debug("check_if_index_exits - " + str(message))
            raise IndexNotFoundException(message)

    def _scroll_over_es_return_object(self, results):
        """
        This function scrolls over the ES return object
        """
        data_new = []
        total_records = 0
        if 'hits' in results:
            total_records = results['hits']['total']
            for post in results['hits']['hits']:
                data_new.append(post)
            if '_scroll_id' in results.keys():
                scroll_size = len(results['hits']['hits'])
                while (scroll_size > 0):
                    scroll_id = results['_scroll_id']
                    scroll_req = {
                        "scroll": "2m",
                        "scroll_id": scroll_id
                    }
                    r = requests.post(self.source + "/_search/scroll", json=scroll_req, timeout=30)
                    results = json.loads(r.content)
                    for post in results['hits']['hits']:
                        data_new.append(post)
                    scroll_size = len(results['hits']['hits'])
        return {
            'hits': data_new,
            'total': total_records
        }

    def _get_all_entities(self, query):
        """
        Fetch all entities from source ES
        """
        response = {
            'hits': [],
            'total': 0,
            'aggregations': {}
        }
        # generate url
        url = self.source + '/' + self.es_alias + "/_search"
        url = url + '?scroll=2m'
        query['size'] = 10000
        r = requests.post(url, json=query, timeout=30)
        results = json.loads(r.content)
        if 'error' not in results:
            # deriving data, with scrolling if required
            derived_data = self._scroll_over_es_return_object(results)
            response['hits'] = derived_data['hits']
            response['total'] = derived_data['total']
            if 'aggregations' in results:
                response['aggregations'] = results['aggregations']
        return response

    def _generate_update_json(self, index, hits):
        """
        Generate the update JSON to update specific entities

        Args
            index (string): The documents will be updated in the index created on destination from source
            hits (object): Hits generated from the ES query
        """
        str_query = []
        for i in hits:
            str_query.append(
                {
                    "_index": index,
                    "_type": i['_type'],
                    "entity_data": i['_source']['entity_data'],
                    "dict_type": i['_source']['dict_type'],
                    "value": i['_source']['value'],
                    "variants": i['_source']['variants'],
                    "language_script": i['_source']['language_script'],
                    "_op_type": "index"
                }
            )
        return str_query

    def _run_update_query_on_es(self, update_query):
        """
        This function runs the update query on ES

        """
        # TODO - this works differently from other connects, picks scheme from the full URL
        scheme, host, port = self.destination.split(':')
        ip = host[2:] if host.startswith('//') else host
        if scheme == 'http':

            es_destination_connection = Elasticsearch(hosts=[{'host': ip, 'port': int(port)}],
                                                      use_ssl=False, verify_certs=False, scheme=scheme,
                                                      connection_class=RequestsHttpConnection)
        else:
            es_destination_connection = Elasticsearch(hosts=[{'host': ip, 'port': int(port)}],
                                                      use_ssl=True, verify_certs=True, scheme=scheme,
                                                      connection_class=RequestsHttpConnection)

        helpers.bulk(es_destination_connection, update_query, stats_only=True)

    def _run_delete_query_on_es(self, index, query):
        """
        This function runs the delete query on ES

        Args
            index (string): The index on which the ES query should be executed
            query (string): The ES query to be executed
        """
        url = self.destination + '/' + index + "/_delete_by_query"
        result = requests.post(url, json=query, timeout=30)
        return result

    def _transfer_specific_documents(self, new_live_index, list_of_entities):
        """
        Transfer list of entities from source ES to new_live_index in destination

        Args
            new_live_index (string): name of the new live index on destination
            list_of_entities (string): list of entity names
        """
        query = {
            "query": {
                "bool": {
                    "must_not": [{
                        "match": {
                            "entity_data": 'person_name'
                        }
                    }]
                }
            }
        }
        if list_of_entities:
            query['query']['bool']['must'] = [
                {
                    "terms": {
                        "entity_data": list_of_entities
                    }
                }
            ]

        full_result = self._get_all_entities(query)
        update_query = self._generate_update_json(new_live_index, full_result['hits'])
        query.pop('size', None)
        self._run_delete_query_on_es(new_live_index, query)
        self._run_update_query_on_es(update_query)

    @staticmethod
    def transfer_data_internal(es_url, index_to_backup, backup_index):
        """
        Transfer data from index_to_backup to backup_index in ES

        Args
            es_url (str): The elasticsearch URL
            index_to_backup (str): The name of the index to take the backup for
            backup_index (str): The name of the backup index
        """
        index_to_backup_url = '{es_url}/{index_to_backup}'.\
            format(**{"es_url": es_url, "index_to_backup": index_to_backup})

        backup_index_url = '{es_url}/{backup_index}'.\
            format(**{"es_url": es_url, "backup_index": backup_index})

        # Fetch index to backup config
        index_to_backup_url_response = requests.get(index_to_backup_url)

        if index_to_backup_url_response.status_code != 200:
            message = "index to backup details could not be fetched"
            raise IndexNotFoundException(message)

        index_to_backup_config = json.loads(index_to_backup_url_response.content)[index_to_backup]
        index_to_backup_config["settings"]["index"].pop("creation_date", None)
        index_to_backup_config["settings"]["index"].pop("uuid", None)
        index_to_backup_config["settings"]["index"].pop("provided_name", None)
        index_to_backup_config["settings"]["index"].pop("version", None)
        index_to_backup_config.pop("aliases", None)

        requests.delete(backup_index_url)

        requests.put(backup_index_url, json=index_to_backup_config)

        final_request_dict = {
            "source": {
                "index": index_to_backup,
                "size": 10000
            },
            "dest": {
                "index": backup_index
            }
        }
        reindex_response = requests.post('{es_url}/_reindex'.format(**{'es_url': es_url}), json=final_request_dict)
        if reindex_response.status_code != 200:
            message = "transfer from " + index_to_backup + "to " + backup_index + " failed"
            raise InternalBackupException(message)

    @staticmethod
    def point_an_alias_to_index(es_url, alias_name, index_name):
        """
        This function assigns the index to an alias

        Args
            es_url (str): The elasticsearch URL
            alias_name (str): The name of the alias to assign the index to
            index_name (str): The index name
        """
        response = requests.put(es_url + '/' + index_name + '/_alias/' + alias_name)
        if response.status_code != 200:
            raise PointIndexToAliasException('pointing ' + index_name + 'to ' + alias_name + ' failed')

    def fetch_index_alias_points_to(self, es_url, alias_name):
        """
        This function fetches the current live index, ie the index the alias points to

        Args
            es_url (str): The elasticsearch URL
            alias_name (str):  The name of alias for which the list of indices has to be fetched

        Returns
            current_live_index (str): The current live index
        """
        response = requests.get(es_url + '/*/_alias/' + alias_name)
        if response.status_code == 200:
            json_obj = json.loads(response.content)
            indices = json_obj.keys()
            if self.es_index_1 in indices:
                return self.es_index_1
            elif self.es_index_2 in indices:
                return self.es_index_2
            else:
                raise FetchIndexForAliasException('neither es_index_1 nor es_index_2' + '' +
                                                  'belong to alias: ' + alias_name)
        raise FetchIndexForAliasException('fetch index for ' + alias_name + ' failed')

    @staticmethod
    def delete_an_index_from_alias(es_url, alias_name, index_name):
        """
        This function deletes an index from the alias

        Args
            es_url (str): The elasticsearch URL
            alias_name (str): The name of the alias
            index_name (str): The name of the index to be deleted from the alias
        """
        response = requests.delete(es_url + '/' + index_name + '/_alias/' + alias_name)
        if response.status_code != 200:
            raise DeleteIndexFromAliasException('delete ' + index_name + 'from ' + alias_name + ' failed')

    def get_new_live_index(self, current_live_index):
        """
        It sets the current_live_index, new_live_index

        Args
            current_live_index (str): The current live index

        Returns
            new_live_index(str): The name of the next live index
        """
        new_live_index = self.es_index_2 if current_live_index == self.es_index_1 else \
            self.es_index_1
        return new_live_index

    def swap_index_in_es_url(self, es_url):
        """
        This function swaps the indices of the alias

        Args
            es_url (str): The elasticsearch URL
        """
        current_live_index = self.fetch_index_alias_points_to(es_url, self.es_alias)
        new_live_index = self.get_new_live_index(current_live_index)
        ESTransfer.delete_an_index_from_alias(es_url, self.es_alias, current_live_index)
        ESTransfer.point_an_alias_to_index(es_url, self.es_alias, new_live_index)

    def transfer_specific_entities(self, list_of_entities=[]):
        """
        This function transfers specific entities of the bot from source to destination

        Args
            list_of_entities (string): list of ES dictionary names to be transferred
        """
        self._validate_source_destination_index_name()
        # self._validate_alias_and_index()

        current_live_index = self.fetch_index_alias_points_to(self.destination, self.es_alias)

        new_live_index = self.get_new_live_index(current_live_index)

        # Backup process
        self.transfer_data_internal(self.destination, current_live_index, new_live_index)

        # call utils function to transfer specific entities
        self._transfer_specific_documents(new_live_index, list_of_entities)

        # swap the index for the alias
        self.swap_index_in_es_url(self.destination)
