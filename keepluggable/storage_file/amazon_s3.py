# -*- coding: utf-8 -*-

'''Amazon S3 storage backend.

    To enable this backend, use this configuration::

        storage.file = keepluggable.storage_file.amazon_s3:AmazonS3Storage

    Configuration settings
    ======================

    - ``s3.access_key_id``: part of your Amazon credentials
    - ``s3.secret_access_key``: part of your Amazon credentials
    - ``s3.region_name``: part of your Amazon credentials
    '''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import base64
import urllib
import hmac
from time import time
from hashlib import sha1
from bag import dict_subset
# from boto3 import resource
from boto3.session import Session  # easy_install -UZ boto3
from keepluggable import read_setting


class AmazonS3Storage(object):
    __doc__ = __doc__

    def __init__(self, settings):
        self.access_key_id = read_setting(settings, 's3.access_key_id')
        self.secret_access_key = read_setting(settings, 's3.secret_access_key')
        session = Session(aws_access_key_id=self.access_key_id,
                          aws_secret_access_key=self.secret_access_key,
                          region_name=read_setting(settings, 's3.region_name'))
        # self.s3 = resource('s3')
        self.s3 = session.resource('s3')

    def create_bucket(self, name):
        self.s3.create_bucket(Name=name)

    def delete_bucket(self, name):
        return self._get_bucket(name).delete()

    def _buckets(self):  # buckets have a .name
        return self.s3.buckets.all()

    def bucket_names(self):  # generator
        return (b.name for b in self._buckets())

    def _get_bucket(self, name):
        return self.s3.Bucket(name) if isinstance(name, str) else name

    def gen_objects(self, bucket):
        '''Generator of the keys in a bucket.'''
        for obj in self._get_bucket(bucket).objects.all():
            yield obj  # which has .key

    def _get_object(self, bucket, key):
        # return self._get_bucket(bucket).Object(key)
        return self.s3.Object(bucket_name=bucket, key=key)

    def get_content(self, bucket, key):
        adict = self._get_object(bucket, key).get()
        return adict['Body'].read()

    def put_object(self, bucket, metadata, bytes_io):
        subset = dict_subset(metadata, lambda k, v: k not in (
            'length', 'md5', 'mime_type'))
        md5 = metadata['md5']
        result = self._get_bucket(bucket).put_object(
            Key=md5, ContentMD5=md5, ContentType=metadata.pop('mime_type'),
            ContentLength=metadata['length'], Body=bytes_io, Metadata=subset)
        import ipdb; ipdb.set_trace() # TODO Remove debug

    def delete_object(self, bucket, key):
        return self._get_object(bucket, key).delete()

    def get_url(self, bucket, key, seconds=3600, https=False):
        """Return S3 authenticated URL sans network access or phatty
            dependencies like boto.

            Stolen from https://gist.github.com/kanevski/655022
            """
        seconds = int(time()) + seconds
        to_sign = "GET\n\n\n{}\n/{}/{}".format(seconds, bucket, key)
        digest = hmac.new(self.secret_access_key, to_sign, sha1).digest()
        return '{scheme}{bucket}.s3.amazonaws.com/{key}?AWSAccessKeyId=' \
            '{access_key_id}&Expires={seconds}&Signature={signature}'.format(
                scheme='https://' if https else 'http://',
                bucket=bucket, key=key,
                access_key_id=self.access_key_id, seconds=seconds,
                signature=urllib.quote(base64.encodestring(digest).strip()),
            )
