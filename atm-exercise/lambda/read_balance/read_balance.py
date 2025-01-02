import json
import boto3
import os
import decimal
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
balance_table = dynamodb.Table(os.environ['CUSTOMERS_BALANCE_TABLE'])
operations_table = dynamodb.Table(os.environ['CUSTOMERS_OPERATIONS_TABLE'])


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        return super().default(o)


def handler(event, context):
    client_id = event["queryStringParameters"]["client_id"]

    response = balance_table.get_item(Key={'client_id': client_id})
    balance = response.get('Item', {}).get('balance', 0)
    operations = operations_table.query(KeyConditionExpression=Key("client_id").eq(client_id))

    return {
        'statusCode': 200,
        'body': json.dumps({'client_id': client_id, 'balance': balance, 'operations': operations.get('Items', [])},
                           cls=DecimalEncoder)
    }
