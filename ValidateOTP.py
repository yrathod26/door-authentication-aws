import json
import boto3
from datetime import datetime
from datetime import timedelta
from decimal import Decimal

def lambda_handler(event, context):
    # TODO implement
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1', endpoint_url="https://dynamodb.us-east-1.amazonaws.com")
    table = dynamodb.Table('passcodes') 
    response = table.get_item(
                Key={
                    'uuid': event['pathParameters']['uuid']
                }
            )
    print(event['pathParameters']['uuid'])
    print(event['pathParameters']['otp'])
    # print(response['Item']['otp'])
    # print(str(Decimal(str(datetime.timestamp(datetime.now())))))
    # print(response['Item']['expiryTime'])
    if str(response['Item']['expiryTime'])<str(Decimal(str(datetime.timestamp(datetime.now())))):
        return {
            "isBase64Encoded": True,
            "statusCode": 400,
            "headers": {'Access-Control-Allow-Origin':'*'},
            "multiValueHeaders": {},
            "body": "OTP Expired!"
        }
    if str(response['Item']['otp']) == str(event['pathParameters']['otp']):
        return {
            "isBase64Encoded": True,
            "statusCode": 200,
            "headers": {'Access-Control-Allow-Origin':'*'},
            "multiValueHeaders": {},
            "body": "Welcome!"
        }
    else:
        return {
            "isBase64Encoded": True,
            "statusCode": 400,
            "headers": {'Access-Control-Allow-Origin':'*'},
            "multiValueHeaders": {},
            "body": "Permission Denied!"
        }