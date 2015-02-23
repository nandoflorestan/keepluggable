# -*- coding: utf-8 -*-

'''Amazon S3 storage backend.

    To enable this backend, use this configuration::

        storage.file = keepluggable.storage_file.amazon_s3:AmazonS3Storage

    Configuration settings
    ======================

    - ``s3.access_key_id``: part of your Amazon credentials
    - ``s3.secret_access_key``: part of your Amazon credentials
    - ``s3.region_name``: part of your Amazon credentials
    - ``s3.bucket``: name of the bucket in which to store objects. If you'd
      like to come up with the bucket name in code rather than configuration,
      you may omit this setting and override the _set_bucket() method.
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
from . import BasePayloadStorage


class AmazonS3Storage(BasePayloadStorage):
    __doc__ = __doc__

    def __init__(self, settings):
        self.access_key_id = read_setting(settings, 's3.access_key_id')
        self.secret_access_key = read_setting(settings, 's3.secret_access_key')
        session = Session(aws_access_key_id=self.access_key_id,
                          aws_secret_access_key=self.secret_access_key,
                          region_name=read_setting(settings, 's3.region_name'))
        # self.s3 = resource('s3')
        self.s3 = session.resource('s3')

        self._set_bucket(settings)

    def _set_bucket(self, settings):
        self.bucket_name = read_setting(settings, 's3.bucket')
        self.bucket = self.s3.Bucket(self.bucket_name)

    def create_bucket(self, name):
        return self.s3.create_bucket(Name=name)

    @property
    def _buckets(self):
        return self.s3.buckets.all()

    @property
    def bucket_names(self):  # generator
        return (b.name for b in self._buckets)

    def _get_bucket(self, bucket=None):
        if bucket is None:
            return self.bucket
        return self.s3.Bucket(bucket) if isinstance(bucket, str) else bucket

    def delete_bucket(self, bucket=None):
        '''Empty the whole bucket.'''
        return self._get_bucket(bucket).delete()

    # Intrabucket operations are below

    SEP = '-'

    @property
    def namespaces(self):  # generator of namespace names
        return set((o.split(self.SEP, 1)[0]
                    for o in self.bucket.objects.all()))

    def _cat(self, namespace, key):
        return namespace + self.SEP + key

    def _get_object(self, namespace, key, bucket=None):
        return self._get_bucket(bucket).Object(self._cat(namespace, key))

    def gen_keys(self, namespace, bucket=None):
        '''Generator of the keys in a namespace. Too costly.'''
        for o in self._get_bucket(bucket).objects.all():
            composite = o.key
            if composite.startswith(namespace + '/'):
                yield composite.split(self.SEP, 1)[1]

    def delete_namespace(self, namespace, bucket=None):
        '''Delete all files in ``namespace``. Too costly.'''
        for key in self.gen_keys(namespace, bucket=bucket):
            self.delete(namespace, key, bucket=bucket)

    def get_reader(self, namespace, key, bucket=None):
        adict = self._get_object(namespace, key, bucket).get()
        return adict['Body']

    def put(self, namespace, metadata, bytes_io, bucket=None):
        subset = dict_subset(metadata, lambda k, v: k not in (
            'length', 'md5', 'mime_type'))
        md5 = metadata['md5']
        result = self._get_bucket(bucket).put_object(
            Key=self._cat(metadata, md5), ContentMD5=md5,
            ContentType=metadata['mime_type'],
            ContentLength=metadata['length'], Body=bytes_io, Metadata=subset)
        print(result)
        import ipdb; ipdb.set_trace() # TODO Remove debug

    def get_url(self, namespace, key, seconds=3600, https=False, bucket=None):
        """Return S3 authenticated URL sans network access or phatty
            dependencies like boto.

            Stolen from https://gist.github.com/kanevski/655022
            """
        bucket = bucket or self.bucket_name
        composite = self._cat(namespace, key)
        seconds = int(time()) + seconds
        to_sign = "GET\n\n\n{}\n/{}/{}".format(seconds, bucket, composite)
        digest = hmac.new(self.secret_access_key, to_sign, sha1).digest()
        return '{scheme}{bucket}.s3.amazonaws.com/{key}?AWSAccessKeyId=' \
            '{access_key_id}&Expires={seconds}&Signature={signature}'.format(
                scheme='https://' if https else 'http://',
                bucket=bucket, key=composite,
                access_key_id=self.access_key_id, seconds=seconds,
                signature=urllib.quote(base64.encodestring(digest).strip()),
            )

    def delete(self, namespace, keys, bucket=None):
        '''Delete many files'''
        if isinstance(keys, (str, int)):
            keys = (keys,)
        number = len(keys)
        assert number <= 1000, 'Amazon allows us to delete only 1000 ' \
            'objects per request; you tried {}'.format(number)
        # return self._get_object(namespace, key, bucket).delete()
        return self._get_bucket(bucket).delete_objects(Delete={
            'Objects': [{'Key': self._cat(namespace, k) for k in keys}]})
