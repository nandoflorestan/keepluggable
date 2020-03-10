"""A storage strategy that keeps files in AWS S3."""

import base64
from hashlib import sha1
import hmac
from time import time
from typing import Any, BinaryIO, Callable, Dict, Iterable, Sequence
from urllib.parse import quote

from bag import dict_subset

# http://botocore.readthedocs.org/en/latest/
from botocore.exceptions import ClientError
from boto3.session import Session  # easy_install -UZ boto3
from pydantic import PyObject, validator

from keepluggable import Pydantic, ReqStr
from keepluggable.orchestrator import get_middle_path, Orchestrator
from keepluggable.storage_file import BasePayloadStorage, get_extension

DAY = 60 * 60 * 24  # seconds


class S3Config(Pydantic):
    """Configuration settings for AmazonS3Storage.

    - ``s3_access_key_id``: part of your Amazon credentials
    - ``s3_access_key_secret``: part of your Amazon credentials
    - ``s3_region_name``: part of your Amazon credentials
    - ``s3_bucket``: name of the bucket in which to store objects.
    """

    s3_access_key_id: ReqStr
    s3_access_key_secret: ReqStr
    s3_region_name: ReqStr
    s3_bucket: ReqStr


class AmazonS3Storage(BasePayloadStorage):
    """Storage backend that keeps files in an Amazon S3 bucket.

    To enable this backend, use this configuration::

        storage.file = keepluggable.storage_file.amazon_s3.AmazonS3Storage
    """

    def __init__(self, orchestrator: Orchestrator) -> None:
        """Read settings and instantiate an S3 Session."""
        super().__init__(orchestrator)
        self.config = S3Config(**self.orchestrator.config.settings)
        session = Session(
            aws_access_key_id=self.config.s3_access_key_id,
            aws_secret_access_key=self.config.s3_access_key_secret,
            region_name=self.config.s3_region_name,
        )
        self.s3 = session.resource("s3")
        self._set_bucket()

    def _set_bucket(self, bucket_name=None):
        self.bucket_name = bucket_name or self.config.s3_bucket
        self.bucket = self.s3.Bucket(self.bucket_name)

    SEP = "/"

    def _get_path(self, namespace: str, metadata: Dict[str, Any]) -> str:
        return (
            get_middle_path(
                name=self.orchestrator.config.name, namespace=namespace
            )
            + self.SEP
            + self._get_filename(metadata)
        )

    def _get_object(self, namespace: str, metadata: Dict[str, Any]):
        return self.bucket.Object(self._get_path(namespace, metadata))

    def get_reader(self, namespace: str, metadata: Dict[str, Any]):
        """Return a stream for the file content."""
        try:
            adict = self._get_object(namespace, metadata).get()
        except ClientError as e:  # amazon_s3: key not found
            raise KeyError(
                "Key not found: {} / {}".format(namespace, metadata["md5"])
            ) from e
        else:
            # botocore.response.StreamingBody has .read(), but not .tell():
            return adict["Body"]

    def put(
        self, namespace: str, metadata: Dict[str, Any], bytes_io: BinaryIO,
    ) -> None:
        """Store a file."""
        subset = dict_subset(
            metadata,
            lambda k, v: k
            in (
                # We are not storing the 'file_name'
                "image_width",
                "image_height",
                "original_id",
                "version",
            ),
        )
        self._convert_values_to_str(subset)
        if hasattr(bytes_io, "seekable") and bytes_io.seekable():
            bytes_io.seek(0)

        # When botocore.response.StreamingBody is passed in as bytes_io,
        # the bucket.put_object() call below fails with
        # "AttributeError: 'StreamingBody' object has no attribute 'tell'"
        # so we have to read the stream, getting the bytes:
        if not hasattr(bytes_io, "tell"):
            bytes_io = bytes_io.read()  # type: ignore

        result = self.bucket.put_object(
            Key=self._get_path(namespace, metadata),
            # done automatically by botocore:  ContentMD5=encoded_md5,
            ContentType=metadata["mime_type"],
            ContentLength=metadata["length"],
            Body=bytes_io,
            Metadata=subset,
        )
        # print(result)
        return result

    def _convert_values_to_str(self, subset: Dict[str, Any]) -> None:
        """Replace ints with the strings that botocore likes values to be."""
        for k in subset.keys():
            subset[k] = str(subset[k])

    def get_url(
        self,
        namespace: str,
        metadata: Dict[str, Any],
        seconds: int = DAY,
        https: bool = True,
    ) -> str:
        """Return S3 authenticated URL without making a request.

        Stolen from https://gist.github.com/kanevski/655022
        """
        composite = self._get_path(namespace, metadata)
        seconds = int(time()) + seconds
        to_sign = "GET\n\n\n{}\n/{}/{}".format(
            seconds, self.bucket_name, composite
        ).encode("ascii")
        digest = hmac.new(
            self.config.s3_access_key_secret.encode("ascii"), to_sign, sha1
        ).digest()
        return (
            "{scheme}{bucket}.s3.amazonaws.com/{key}?AWSAccessKeyId="
            "{access_key_id}&Expires={seconds}&Signature={signature}".format(
                scheme="https://" if https else "http://",
                bucket=self.bucket_name,
                key=composite,
                access_key_id=self.config.s3_access_key_id,
                seconds=seconds,
                signature=quote(base64.encodestring(digest).strip()),
            )
        )

    def delete(
        self, namespace: str, metadatas: Sequence[Dict[str, Any]],
    ) -> Any:
        """Delete up to 1000 files."""
        number = len(metadatas)
        assert number <= 1000, (
            "Amazon allows us to delete only 1000 "
            "objects per request; you tried {}".format(number)
        )
        return self.bucket.delete_objects(
            Delete={
                "Objects": [
                    {"Key": self._get_path(namespace, metadata)}
                    for metadata in metadatas
                ]
            }
        )

    def get_superpowers(self) -> "AmazonS3Power":
        """Get a really dangerous subclass instance."""
        return AmazonS3Power(self.orchestrator)


def old_path_from_new_path(path: str) -> str:
    """Convert a new path to an old one.

    Useful for bucket migration. This is an example implementation.
    """
    parts = path.split("/")
    filename = parts[-1]
    md5 = filename.split(".")[0]
    first_dir = parts[0]
    namespace = "".join(filter(str.isnumeric, first_dir))
    return namespace + "-" + md5


class AmazonS3Power(AmazonS3Storage):
    """A subclass with dangerous methods, not part of the interface."""

    def create_bucket(self, name: str) -> None:
        """Add a bucket to your S3 account."""
        return self.s3.create_bucket(Name=name)

    @property
    def _buckets(self):
        return self.s3.buckets.all()

    @property
    def bucket_names(self) -> Iterable[str]:
        """Generate the existing bucket names."""
        return (b.name for b in self._buckets)

    def gen_paths(self, namespace: str) -> Iterable[str]:
        """Generate the paths in a namespace. Too costly -- avoid."""
        prefix = get_middle_path(
            name=self.orchestrator.config.name, namespace=namespace
        )
        for o in self.bucket.objects.all():
            composite = o.key
            if composite.startswith(prefix):
                yield composite

    def delete_namespace(self, namespace: str) -> None:
        """Delete all files in ``namespace``.

        This is probably too costly because it reads all objects from bucket.
        """
        # TODO Work around S3 limitation of 1000 objects per request
        self.bucket.delete_objects(
            Delete={
                "Objects": [
                    {"Key": path} for path in self.gen_paths(namespace)
                ]
            }
        )

    def empty_bucket(self):
        """Delete all files in this bucket. DANGEROUS."""
        # TODO Request up to 1000 files at a time
        items = list(self.bucket.objects.all())
        if not items:
            return None
        resp = self.bucket.delete_objects(
            Delete={"Objects": [{"Key": o.key} for o in items]}
        )
        print(resp)
        return resp

    def delete_bucket(self):
        """Delete the entire bucket."""
        # All items must be deleted before the bucket itself
        self.empty_bucket()
        return self.bucket.delete()

    def migrate_bucket(
        self,
        old_bucket: str,
        new_bucket: str = None,
        skip_the_first_n: int = 0,
        discard_img_sizes: Sequence[str] = [],
        old_path_from_new_path: Callable[[str], str] = old_path_from_new_path,
    ):
        """Migrate a bucket from keepluggable < 0.8.

        First you must configure the app to use a new bucket. Then you can
        use this method from Pyramid's shell, ``pshell server.ini``::

            from keepluggable.web.pyramid import Orchestrator
            orch = Orchestrator.instances['KEEPLUGGABLE_NAME']
            power = orch.storage_file.get_superpowers()
            power.migrate_bucket(
                'my_old_bucket_name',
                new_bucket='my_destination_bucket_name',
                discard_img_sizes=['thumb'])
        """
        # Open and iterate old_bucket
        old = self.s3.Bucket(old_bucket)
        if new_bucket:
            self._set_bucket(new_bucket)
        new_objects_collection = self.bucket.objects.all()
        print("   Retrieving existing keys in target {}".format(self.bucket))

        # TODO For a really big bucket we might need to use a database:
        existing = [
            old_path_from_new_path(fil.key) for fil in new_objects_collection
        ]
        print(
            "   There are {}. Migrating remaining files...".format(
                len(existing)
            )
        )

        for index, summary in enumerate(old.objects.all(), 1):
            if index < skip_the_first_n:
                continue
            namespace, md5 = summary.key.split("-")

            # Skip files that already exist in the target bucket
            if summary.key in existing:
                print(
                    "   {}. Already exists in destination: {}".format(
                        index, summary.key
                    )
                )
                continue

            # TODO Optionally ignore old files, using summary.last_modified

            obj = summary.Object()

            # Ignore image versions found in "discard_img_sizes"
            version = obj.metadata.get("version")
            if version in discard_img_sizes:
                print(
                    "   {}. Skipping unwanted version: {}".format(index, obj)
                )
                continue

            new_key = (
                get_middle_path(
                    name=self.orchestrator.config.name, namespace=namespace
                )
                + self.SEP
                + md5
                + get_extension(obj.content_type)
            )

            # Copy files, including metadata
            copy_source = {
                "Bucket": old_bucket,
                "Key": summary.key,
            }
            self.bucket.copy(copy_source, new_key)  # LastModified is not kept
            print("   {}. Copied: {}".format(index, new_key))
        print("Migration finished.")
