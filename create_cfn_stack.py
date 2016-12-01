#!/usr/bin/env python2.7

from jinja2 import Template
import boto3
import argparse

parser = argparse.ArgumentParser(description='Create CloudFormation stack')
parser.add_argument('stackname', metavar='STACK_NAME', help='CloudFormation stack name')
parser.add_argument('bucket', metavar='S3_BUCKET', help='S3 bucket name for Lambda code')
parser.add_argument('email', metavar='EMAIL', help='e-mail address for notificaitons')
args = parser.parse_args()

# Load template
template = Template(open('cfn-template.yaml.j2').read())

# Render template
cfn_template = template.render(
    email=args.email,
    bucket=args.bucket
)

# CloudFormation client
client = boto3.client('cloudformation')

# Create CloudFormation stack
response = client.create_stack(
    StackName=args.stackname,
    TemplateBody=cfn_template,
    Capabilities=('CAPABILITY_NAMED_IAM', 'CAPABILITY_IAM'),
)

# Print response
print(response)
