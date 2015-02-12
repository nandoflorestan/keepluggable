# -*- coding: utf-8 -*-

'''Amazon S3 storage backend'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import base64
import urllib
import hmac
from time import time
from hashlib import sha1
# import boto3
# from boto3 import resource
from boto3.session import Session
from keepluggable import read_setting


class AmazonS3Storage(object):
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
        return self.get_bucket(name).delete()

    def all_buckets(self):  # buckets have a .name
        return self.s3.buckets.all()

    def bucket_names(self):  # generator
        return (b.name for b in self.all_buckets())

    def get_bucket(self, name):
        return self.s3.Bucket(name) if isinstance(name, str) else name

    def gen_objects(self, bucket):
        '''List the contents of a bucket.'''
        for obj in self.get_bucket(bucket).objects.all():
            yield obj  # which has .key

    def get_object(self, bucket, key):
        # return self.get_bucket(bucket).Object(key)
        return self.s3.Object(bucket_name=bucket, key=key)

    def get_content(self, bucket, key):
        adict = self.get_object(bucket, key).get()
        return adict['Body'].read()

    def put_object(self, bucket, key, metadata, content):
        '''*content* may be an open file.'''
        return self.get_bucket(bucket).put_object(
            Key=key, Metadata=metadata, Body=content)
        # TODO ContentMD5, ContentLength, ContentType (the MIME type)

    def delete_object(self, bucket, key):
        return self.get_object(bucket, key).delete()

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
