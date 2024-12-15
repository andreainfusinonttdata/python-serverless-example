import json
import boto3
import os
import decimal


sqs = boto3.client('sqs')


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        return super().default(o)


def handler(event, context):
    body = json.loads(event["body"])
    client_id = body["client_id"]
    amount = body["amount"]

    message = {
        'operation': 'withdraw',
        'client_id': client_id,
        'amount': amount
    }

    # Send message to SQS
    sqs.send_message(
        QueueUrl=os.environ['PROCESS_REQUESTS_QUEUE_URL'],
        MessageBody=json.dumps(message)
    )

    return {
        'statusCode': 200,
        'body': json.dumps({'status': 'Withdrawal request sent', 'client_id': client_id, 'amount': amount},
                           cls=DecimalEncoder)
    }