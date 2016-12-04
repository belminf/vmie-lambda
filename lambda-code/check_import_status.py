import boto3
import time
import os

# Globally Defined Items
ec2 = boto3.client('ec2')
ddb = boto3.resource('dynamodb')
sns = boto3.client('sns')
events = boto3.client('events')

status_table = ddb.Table(os.environ('DYNAMO_TABLE'))
event_info = []


# Function to Disable Event to Trigger Check Status Lambda Function
def disable_check():
    rule_status = events.describe_rule(
        Name=os.environ('SCHEDULE_RULE'))

    if rule_status[u'State'] == 'ENABLED':
        events.disable_rule(
            Name=os.environ('SCHEDULE_RULE')
        )
        print 'Status Check Disabled'
    else:
        print 'Status Check already disabled, Nothing to Check'


# Function  to Update Status of Each Import Task in DynamoDB Table
def update_status():

    ddb_task_list = []
    ddb_tasks = status_table.scan(ConsistentRead=True)

    for items in ddb_tasks[u'Items']:
        ddb_task_list.append(items[u'ImportTaskId'])

    current_stat = ec2.describe_import_image_tasks(ImportTaskIds=ddb_task_list)

    for task in current_stat[u'ImportImageTasks']:
        if task[u'Status'] == 'completed':
            status_table.update_item(
                Key={'ImportTaskId': task[u'ImportTaskId']},
                UpdateExpression="set JobStatus=:js, StatusMessage=:sm",
                ExpressionAttributeValues={
                    ':js': task[u'Status'],
                    ':sm': 'Completed Successfully'
                },
                ReturnValues="UPDATED_NEW"
            )
            print 'Going to Send Notification for {}'.format(task[u'ImportTaskId'])
            send_notification()

        elif task[u'Status'] == 'deleted':
            status_table.update_item(
                Key={'ImportTaskId': task[u'ImportTaskId']},
                UpdateExpression="set JobStatus=:js, StatusMessage=:sm",
                ExpressionAttributeValues={
                    ':js': task[u'Status'],
                    ':sm': task[u'StatusMessage']
                },
                ReturnValues="UPDATED_NEW"
            )
            print 'Going to Send Notification for {}'.format(task[u'ImportTaskId'])
            send_notification()

        else:
            status_table.update_item(
                Key={'ImportTaskId': task[u'ImportTaskId']},
                UpdateExpression="set JobStatus=:js, StatusMessage=:sm",
                ExpressionAttributeValues={
                    ':js': task[u'Status'],
                    ':sm': task[u'StatusMessage']
                },
                ReturnValues="UPDATED_NEW"
            )
            print '{} is still {}.'.format(task[u'ImportTaskId'], task[u'Status'])


# Function to Send Notification on Updates and deletes Key from DDB Table.
def send_notification():
    time.sleep(5)

    ddb_tasks = status_table.scan(ConsistentRead=True)
    for items in ddb_tasks[u'Items']:
        if items[u'JobStatus'] in ('completed', 'deleted', 'deleting'):
            sns.publish(
                TopicArn=os.environ['SNS_TOPIC_END'],
                Message='''VM import task with Task ID of {} has ended with status of:\n{}
This task was importing the following file:{}'''.format(items[u'ImportTaskId'], items[u'StatusMessage'], items[u'ObjectName']),
                Subject='{} Ended'.format(items[u'ImportTaskId']),
            )

            print 'Notification Sent for {}'.format(items[u'ImportTaskId'])

            status_table.delete_item(
                Key={'ImportTaskId': items[u'ImportTaskId']},
            )


def lambda_handler(event, context):
    event_info.insert(0, event[u'account'])
    event_info.insert(1, event[u'region'])

    ddb_task_list = []
    ddb_tasks = status_table.scan(ConsistentRead=True)

    for items in ddb_tasks[u'Items']:
        ddb_task_list.append(items[u'ImportTaskId'])

    if ddb_task_list == []:
        disable_check()

    else:
        update_status()
