# vmie-lambda [![Build Status](https://travis-ci.org/belminf/vmie-lambda.svg?branch=master)](https://travis-ci.org/belminf/vmie-lambda)
Leverages [boto3](https://boto3.readthedocs.io/en/latest/) and [CloudFormation](https://aws.amazon.com/cloudformation/) to create resources necessary to watch an S3 bucket to convert an OVA to an AMI. A Python Lambda script is triggered when a new OVA file is uploaded to the S3 bucket. Another Lambda Python script is used for reporting back status.

## Requirements
Python requirements:

    $ pip install -r requirements.txt

AWS credential via environment variables:

    $ export AWS_ACCESS_KEY_ID="KEY_ID_HERE"
    $ export AWS_SECRET_ACCESS_KEY="ACCES_KEY_HERE"

## Files
* `setup_vmie_lambda.py` - sets up necessary AWS resources
* `cfn-template.yaml.j2` - CloudFormation template using Jinja2
* `lambda-code/` - directory for Lambda function code
