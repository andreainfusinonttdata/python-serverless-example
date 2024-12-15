import json
import boto3
import os
import decimal
from aws_lambda_powertools.utilities.batch import (
    BatchProcessor,
    EventType,
    process_partial_response,
)
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools import Logger, Tracer


logger = Logger()
tracer = Tracer()


dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')
table = dynamodb.Table(os.environ['CUSTOMERS_BALANCE_TABLE'])
processor = BatchProcessor(event_type=EventType.SQS)


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        return super().default(o)


@tracer.capture_method(capture_response=True)
def handler(event, context: LambdaContext):
    return process_partial_response(
        event=event, record_handler=lambda_handler, processor=processor, context=context
    )


def lambda_handler(record: SQSRecord):
    logger.info("Started process_requests execution", incoming_record=record)
    payload = json.loads(record['body'])
    client_id = payload['client_id']
    operation = payload['operation']
    amount = payload.get('amount', 0)

    response_message = {}

    response = table.get_item(Key={'client_id': client_id})
    balance = response.get('Item', {}).get('balance', 0)

    if amount < 0:
        response_message = {
            'outcome': 'FAIL-incorrect amount',
            'client_id': client_id,
            'balance': balance
        }

    elif operation == "read":
        response_message = {
            'outcome': 'SUCCESS',
            'client_id': client_id,
            'balance': balance
        }

    elif operation == "deposit":
        new_balance = balance + amount
        table.update_item(
            Key={'client_id': client_id},
            UpdateExpression='SET balance = :val1',
            ExpressionAttributeValues={':val1': new_balance}
        )

        response_message = {
            'outcome': 'SUCCESS',
            'client_id': client_id,
            'balance': new_balance
        }

    elif operation == "withdraw":
        if balance >= amount:
            # Update balance if sufficient funds
            new_balance = balance - amount
            table.update_item(
                Key={'client_id': client_id},
                UpdateExpression='SET balance = :val1',
                ExpressionAttributeValues={':val1': new_balance}
            )

            response_message = {
                'outcome': 'SUCCESS',
                'client_id': client_id,
                'balance': new_balance
            }
        else:
            response_message = {
                'outcome': 'FAIL-insufficient balance',
                'client_id': client_id,
                'balance': balance
            }

    logger.info("Publishing operation result", response_message=response_message)
    sns.publish(
        TopicArn=os.environ['OPERATION_RESULT_TOPIC'],
        Message=json.dumps(response_message, cls=DecimalEncoder)
    )

    return {
        'statusCode': 200,
        'body': json.dumps(response_message, cls=DecimalEncoder)
    }