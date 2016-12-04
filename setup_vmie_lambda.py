#!/usr/bin/env python2.7

from os.path import basename, splitext, join as path_join
from shutil import rmtree
from tempfile import mkdtemp
from zipfile import ZipFile
from jinja2 import Template
import argparse
import boto3

parser = argparse.ArgumentParser(description='Sets up a CloudFormation stack to convert OVAs to AMIs')
parser.add_argument('stackname', metavar='STACK_NAME', help='CloudFormation stack name')
parser.add_argument('email', metavar='EMAIL', help='e-mail address for notificaitons')
args = parser.parse_args()

LAMBDA_DEPLOYMENT_FILES = (
    'lambda-code/import_ova.py',
    'lambda-code/check_import_status.py',
)

# Load template
template = Template(open('cfn-template.yaml.j2').read())

# CloudFormation client
client = boto3.client('cloudformation')

# Render template
cfn_template = template.render(
    email=args.email,
    stack_update=False
)

# Create CloudFormation stack
print('Creating stack...')
client.create_stack(
    StackName=args.stackname,
    TemplateBody=cfn_template,
    Capabilities=('CAPABILITY_NAMED_IAM', 'CAPABILITY_IAM'),
)

# Wait till stack is created
waiter = client.get_waiter('stack_create_complete')
waiter.wait(StackName=args.stackname)

print('Uploading Lambda code to S3...')

# Get CFn generated bucket name
cf_resources = boto3.resource('cloudformation')
bucket_resource = cf_resources.StackResource(args.stackname, 'S3BucketLambda')
bucket_name = bucket_resource.physical_resource_id

# Create temporary directory
tmpdir_path = mkdtemp(prefix='vmie-')

# S3 resource client
s3 = boto3.resource('s3')

# Update zip files
try:
    for filename in LAMBDA_DEPLOYMENT_FILES:

        # Filename used to name the zip file
        base_fn = splitext(basename(filename))[0]
        zip_fn = '{}.zip'.format(base_fn)
        zip_path = path_join(tmpdir_path, zip_fn)

        print('Compressing {}...'.format(zip_fn))

        # Create zip file and add the python code
        with ZipFile(zip_path, 'w') as zip_file:
            zip_file.write(filename)

        print('Uploading {} to S3...'.format(zip_fn))

        # Put on S3
        s3.Bucket(bucket_name).put_object(Key=zip_fn, Body=open(zip_path))

finally:

    # Cleanup by deleting temporary directory
    rmtree(tmpdir_path)

print('Adding Lambda code to stack...')

# Add lambda functions to template
cfn_template = template.render(
    email=args.email,
    lambda_code=True
)

# Run stack update
client.update_stack(
    StackName=args.stackname,
    TemplateBody=cfn_template,
    Capabilities=('CAPABILITY_NAMED_IAM', 'CAPABILITY_IAM'),
)

# Wait till stack is updated
waiter = client.get_waiter('stack_update_complete')
waiter.wait(StackName=args.stackname)

print('Adding S3 notification to stack...')

# Add lambda functions to template
cfn_template = template.render(
    email=args.email,
    lambda_code=True,
    s3_notification=True
)

# Run stack update
client.update_stack(
    StackName=args.stackname,
    TemplateBody=cfn_template,
    Capabilities=('CAPABILITY_NAMED_IAM', 'CAPABILITY_IAM'),
)

# Wait till stack is updated
waiter = client.get_waiter('stack_update_complete')
waiter.wait(StackName=args.stackname)

print('Done.')
