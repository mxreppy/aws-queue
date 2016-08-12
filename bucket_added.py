import boto3
import json

SNS_NAME = 'code-kata-object-created'
queue_name = 'AARON_queue'

queue_policy_statement = {
        "Sid": "auto-transcode",
        "Effect": "Allow",
        "Principal": {
            "AWS": "*"
        },
        "Action": "SQS:SendMessage",
        "Resource": "<SQS QUEUE ARN>",
        "Condition": {
            "StringLike": {
                "aws:SourceArn": "<SNS TOPIC ARN>"
            }
        }
    }

sns = boto3.resource('sns', 'us-east-1')
sqs = boto3.resource('sqs', 'us-east-1')

topic = sns.create_topic(Name=SNS_NAME)

# Creating a queue is idempotent, so if it already exists
# then we will just get the queue returned.
queue = sqs.create_queue(QueueName=queue_name)
queue_arn = queue.attributes['QueueArn']

# Ensure that we are subscribed to the SNS topic
subscribed = False
# topic = sns.Topic(topic_arn)
for subscription in topic.subscriptions.all():
    if subscription.attributes['Endpoint'] == queue_arn:
        subscribed = True
        print("[{}] already subscribed to sns:[{}]".format(queue.url, topic.arn))
        break

if not subscribed:
    topic.subscribe(Protocol='sqs', Endpoint=queue_arn)
    print("subscribed [{}] to sns:[{}]".format(queue.arn, topic.arn))

# Set up a policy to allow SNS access to the queue
if 'Policy' in queue.attributes:
    policy = json.loads(queue.attributes['Policy'])
else:
    policy = {'Version': '2008-10-17'}

if 'Statement' not in policy:
    statement = queue_policy_statement
    statement['Resource'] = queue_arn
    statement['Condition']['StringLike']['aws:SourceArn'] = \
        topic.arn
    policy['Statement'] = [statement]

    queue.set_attributes(Attributes={
        'Policy': json.dumps(policy)
    })


from pprint import pprint

for m in queue.receive_messages(WaitTimeSeconds=20):
    print("\n************\nSQS Message Envelope:")
    pprint(m)
    
    body = json.loads(m.body)
    try:
        message = json.loads(body['Message'])
    except:
        message = body['Message']
        
    print('\n************\ninner message')
    pprint(message)
