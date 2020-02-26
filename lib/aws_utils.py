from __future__ import absolute_import
import boto
import boto3
from chatbot_ner.config import ner_logger


def read_model_dict_from_s3(bucket_name, bucket_region, model_path_location=None):
    """
    This method is used to read the model from S3 bucket and region specified.
    Args:
        bucket_name (str): name of the bucket to upload file to
        model_path_location (str): full path including filename on disk of the file to download
        bucket_region (str, Optional): region of the s3 bucket, defaults to None

    Returns:
        model_dict: Model from aws s3
    """
    model_dict = None
    try:
        s3 = boto3.resource('s3', region_name=bucket_region)
        bucket = s3.Bucket(bucket_name)
        pickle_file_handle = bucket.Object(model_path_location.lstrip('/'))
        # note read() will return str and hence cPickle.loads
        model_dict = pickle_file_handle.get()['Body'].read()
        ner_logger.debug("Model Read Successfully From s3")
    except Exception as e:
        ner_logger.exception("Error Reading model from s3 for domain %s " % e)
    return model_dict


def write_file_to_s3(bucket_name, address, disk_filepath, bucket_region=None):
    """
    Upload file on disk to s3 bucket with the given address
    WARNING! File will be overwritten if it exists

    Args:
        bucket_name (str): name of the bucket to upload file to
        address (str): full path including filename inside the bucket to upload the file at
        disk_filepath (str): full path including filename on disk of the file to upload to s3 bucket
        bucket_region (str, Optional): region of the s3 bucket, defaults to None

    Returns:
        bool: indicating whether file upload was successful

    """
    try:
        connection, bucket = get_s3_connection_and_bucket(bucket_name=bucket_name,
                                                          bucket_region=bucket_region)
        key = bucket.new_key(address)
        key.set_contents_from_filename(disk_filepath)
        connection.close()
        return True
    except Exception as e:
        ner_logger.error("Error in write_file_to_s3 - %s %s %s : %s" % (bucket_name, address, disk_filepath, e))

    return False


def get_s3_connection_and_bucket(bucket_name, bucket_region=None):
    """
    Connect to S3 bucket

    Args:
        bucket_name (str): name of the bucket to upload file to
        bucket_region (str, Optional): region of the s3 bucket, defaults to None

    Returns:
        tuple containing
            boto.s3.connection.S3Connection: Boto connection to s3 in the specified region
            boto.s3.bucket.Bucket: bucket object of the specified name

    """
    if bucket_region:
        connection = boto.s3.connect_to_region(bucket_region)
    else:
        connection = boto.connect_s3()
    bucket = connection.get_bucket(bucket_name)
    return connection, bucket
