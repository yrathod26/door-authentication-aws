import json
import boto3
from datetime import datetime
from datetime import timedelta
from decimal import Decimal
import random

def lambda_handler(event, context):
    # TODO implement
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1', endpoint_url="https://dynamodb.us-east-1.amazonaws.com")
    table = dynamodb.Table('visitors')
    body = json.loads(event['body'])
    client=boto3.client('rekognition')  
    # response=client.create_collection(CollectionId='Collection')

    table.put_item(
        Item = {
        'faceId' : body['uuid'],
        'phoneNumber': body['phoneNumber'],
        'name':body['name'],
        'photos':[{
            "objectKey":"download.jfif",
            "bucket":"face-images-cc",
            "createdTimestamp": Decimal(str(datetime.timestamp(datetime.now())))
        }]
        })
    otp = random.randrange(1000,9999)
    Table_passcodes = dynamodb.Table('passcodes')
    Table_passcodes.put_item(
      Item={
            'uuid': body['uuid'],
            'otp':otp,
            'expiryTime': Decimal(str(datetime.timestamp(datetime.now()+timedelta(minutes = 5))))
        }
        )
    message = "Hi, "+body['name']+". Enter the otp:"+ str(otp) +" here: https://cc-hw-2.s3.amazonaws.com/index.html?uuid="+str(body['uuid'])
    sns_client = boto3.client('sns')
    sns_client.publish(
        PhoneNumber=str(body['phoneNumber']),
        Message=message,
        MessageAttributes={
            'AWS.SNS.SMS.SMSType': {
                'DataType': 'String',
                'StringValue': 'Transactional'
            }
        }
        )
    print(message)
    return {
        "isBase64Encoded": True,
        "statusCode": 200,
        "headers": {'Access-Control-Allow-Origin':'*'},
        "multiValueHeaders": {},
        "body": "Successfully Added New Visitor."
    }