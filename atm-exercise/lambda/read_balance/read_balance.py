import json
import boto3
import os
import decimal

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['CUSTOMERS_BALANCE_TABLE'])


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        return super().default(o)


def handler(event, context):
    client_id = event["queryStringParameters"]["client_id"]

    response = table.get_item(Key={'client_id': client_id})
    balance = response.get('Item', {}).get('balance', 0)

    return {
        'statusCode': 200,
        'body': json.dumps({'client_id': client_id, 'balance': balance}, cls=DecimalEncoder)
    }