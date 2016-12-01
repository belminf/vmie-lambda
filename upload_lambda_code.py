#!/usr/bin/env python2.7

from os.path import basename, splitext
from zipfile import ZipFile
import argparse
import boto3

parser = argparse.ArgumentParser(description='Upload lambda code to S3')
parser.add_argument('bucket', metavar='S3_BUCKET', help='S3 bucket name for Lambda code')
args = parser.parse_args()

LAMBDA_DEPLOYMENT_FILES = (
    'lambda/import_ova.py',
    'lambda/check_import_status.py',
)

S3_BUCKET_NAME = args.bucket

# Load S3 and create bucket
s3 = boto3.resource('s3')
s3.create_bucket(Bucket=args.bucket)

# Update zip files
for filename in LAMBDA_DEPLOYMENT_FILES:

    # Filename used to name the zip file
    base_fn = splitext(basename(filename))[0]
    zip_fn = '{}.zip'.format(base_fn)

    # Create zip file and add the python code
    with ZipFile(zip_fn, 'w') as zip_file:
        zip_file.write(filename)

    # Put on S3
    s3.Bucket(S3_BUCKET_NAME).put_object(Key=zip_fn, Body=open(zip_fn))

    print('Uploaded {} to {}...'.format(zip_fn, S3_BUCKET_NAME))

print('Done.')
