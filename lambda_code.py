import boto3
import os


# Handles new OVA added to S3 bucket
def handle_new_images(event, context):
    s3_key = event[u'Records'][0][u's3'][u'object'][u'key']
    s3_bucket = event[u'Records'][0][u's3'][u'bucket'][u'name']

    # Begin importing image
    image_import = start_image_import(s3_bucket, s3_key)

    # Notify user
    task_id = image_import['ImportTaskId']
    send_notification(
        topic=os.environ['SNS_TOPIC'],
        subject=task_id,
        msg='\n'.join((
            'A VM import task has been initiated.',
            '',
            'Task ID: {}'.format(task_id),
            'Image: {}'.format(s3_key),
            '',
            'You will be notified when the task is completed.'
        ))
    )

    # Record task and enable checker
    record_task(task_id, s3_key)
    toggle_checker(True)


# Handles a scan of tasks
def handle_task_scans(event, context):
    task_ids = get_recorded_task_ids()
    task_descriptions = get_task_descriptions(task_ids)

    # Process task statuses
    for task_id in task_ids:
        description = task_descriptions.get(task_id)

        # Log error if we cannot find the description
        if not description:
            print('Error: Could not find description for task {}'.format(task_id))
            continue

        # If status not done, skip
        if description['status'] not in ('completed', 'deleted'):
            continue

        # ASSERT: task is done

        # Send notification
        send_notification(
            topic=os.environ['SNS_TOPIC'],
            subject=task_id,
            msg='\n'.join((
                'VM import task is complete.',
                '',
                'Task ID: {}'.format(task_id),
                'Image: {}'.format(description['image']),
                'Status: {} - {}'.format(description['status'], description['msg']),
            ))
        )

        # Delete item now
        delete_recorded_task(task_id)

    # Toggle checker based on number of tasks
    toggle_checker(len(task_ids) > 0)


def start_image_import(s3_bucket, s3_key):
    ec2 = boto3.client('ec2')

    return ec2.import_image(
        Description='Lambda_VMIE',
        DiskContainers=[{
            'Description': 'Import_OVA',
            'Format': 'ova',
            'UserBucket': {
                'S3Bucket': s3_bucket,
                'S3Key': s3_key
            },
        }],
        RoleName=os.environ['VMIE_IAM_ROLE'],
        LicenseType='BYOL'
    )


def send_notification(topic, subject, msg):
    sns = boto3.client('sns')

    sns.publish(TopicArn=topic, Message=msg, Subject=subject)

    print('Notification "{}" sent to "{}".'.format(subject, topic))


def toggle_checker(toggle=True):
    events = boto3.client('events')
    rule_name = os.environ['SCHEDULE_RULE']

    if toggle:
        events.enable_rule(Name=rule_name)
    else:
        events.disable_rule(Name=rule_name)

    print('Schedule rule toggled to {}'.format('ON' if toggle else 'OFF'))


def record_task(task_id, vm_name):
    ddb = boto3.client('dynamodb')

    ddb.put_item(
        TableName=os.environ['DYNAMO_TABLE'],
        Item={
            'task_id': {'S': task_id},
            'vm_name': {'S': vm_name},
        }
    )

    print('Recorded task in DynamoDB: {} ({})'.format(task_id, vm_name))


def get_recorded_task_ids():
    ddb = boto3.resource('dynamodb')
    status_table = ddb.Table(os.environ['DYNAMO_TABLE'])

    scan_items = status_table.scan(ConsistentRead=True)['Items']

    return [i['task_id'] for i in scan_items]


def delete_recorded_task(task_id):
    ddb = boto3.resource('dynamodb')
    status_table = ddb.Table(os.environ['DYNAMO_TABLE'])

    status_table.delete_item(Key={'task_id': task_id})

    print('Deleted task in DynamoDB: {}'.format(task_id))


def get_task_descriptions(task_ids):
    ec2 = boto3.client('ec2')

    descriptions = ec2.describe_import_image_tasks(ImportTaskIds=task_ids)

    task_descriptions = {}

    for task in descriptions:
        task_descriptions[task['ImportTaskId']] = {
            'status': task['Status'],
            'msg': task['StatusMessage'],
            'image': task['UserBucket'].get('S3Key'),
            'snapshot': task['SnapshotId'].get('SnapshotId'),
        }

    return task_descriptions
