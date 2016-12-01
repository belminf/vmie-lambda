# vmie-lambda
This is a AWS Lambda function that works off of a S3 Create Object Event that will import a OVA file to an AMI. This is a simple Lambda function that will take the ova file and import it to a AMI using the VM Import\Export Service. The accompanying script will continually check that status of the import jobs until they have finished and report back status.

## Requirements
Python requirements:

    $ pip install -r requirements.txt

AWS credential via environment variables:

    $ export AWS_ACCESS_KEY_ID="KEY_ID_HERE"
    $ export AWS_SECRET_ACCESS_KEY="ACCES_KEY_HERE"

## Files
* `cfn-template.yaml` - CloudFormation template
