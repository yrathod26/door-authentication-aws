import json
import boto3
import base64
import time
import random
import cv2
from decimal import Decimal
from datetime import datetime  
from datetime import timedelta   
from boto3.dynamodb.conditions import Key, Attr

def lambda_handler(event, context):
    # TODO implement
    # print(event)
    #event['Records'][0]['kinesis']['data']
    decoded_json = base64.decodestring(bytes(event['Records'][0]['kinesis']['data'],'utf-8'))
    
    #decoded_json = base64.decodestring(bytes(event['data'],'utf-8'))   
    decoded_json = json.loads(decoded_json)
    print(decoded_json['FaceSearchResponse'])
    
    if len(decoded_json['FaceSearchResponse'])>0 :
        kvs_client = boto3.client('kinesisvideo')
        kvs_data_pt = kvs_client.get_data_endpoint(
            StreamARN="arn:aws:kinesisvideo:us-east-1:636938905002:stream/kds_test/1586731923208", # kinesis stream arn
            APIName='GET_HLS_STREAMING_SESSION_URL'
        )
        end_pt = kvs_data_pt['DataEndpoint']
    
##        kvs_video_client = boto3.client('kinesis-video-media', endpoint_url=end_pt, region_name='us-east-1') # provide your region
##        kvs_stream = kvs_video_client.get_media(
##            StreamARN="arn:aws:kinesisvideo:us-east-1:636938905002:stream/kds_test/1586731923208", # kinesis stream arn
##            StartSelector={'StartSelectorType': 'FRAGMENT_NUMBER',
##                'AfterFragmentNumber': decoded_json['InputInformation']['KinesisVideo']['FragmentNumber']
##            } # to keep getting latest available chunk on the stream
##        )
##        streamBody = kvs_stream['Payload'].read(1024*16384)
        if len(decoded_json['FaceSearchResponse'][0]['MatchedFaces']) == 0:
            client=boto3.client('rekognition')  
            # response=client.create_collection(CollectionId='Collection')
            kvam = boto3.client("kinesis-video-archived-media", endpoint_url=end_pt)
            url = kvam.get_hls_streaming_session_url(
                StreamName="kds_test",
                PlaybackMode="LIVE"
            )['HLSStreamingSessionURL']
            print("URL MILA")
            print(url)
            vcap = cv2.VideoCapture(url)
            ret, frame = vcap.read()
            t = str(time.time())
            cv2.imwrite('/tmp/frame-'+t+'.jpg', frame)
            s3_client = boto3.client('s3')
            s3_client.upload_file(
                '/tmp/frame-'+t+'.jpg',
                'face-images-cc', # replace with your bucket name
                'frame-'+t+'.jpg',
                ExtraArgs={'ACL': 'public-read'}
                )
            image_name = 'frame-'+t+'.jpg'
            image_url = "https://face-images-cc.s3.amazonaws.com/"+image_name
            print("Hi, Some unknown visitor is in front of the door")
            response1=client.index_faces(CollectionId='Collection',
                                        Image={'S3Object':{'Bucket':'face-images-cc','Name':image_name}},
                                        ExternalImageId=image_name,
                                        MaxFaces=1,
                                        QualityFilter="AUTO",
                                        DetectionAttributes=['ALL'])
            face_id = ""
            s3_url = "https://cc-hw-2-create-visitor.s3.amazonaws.com/index.html"
            for faceRecord in response1['FaceRecords']:
                face_id = faceRecord['Face']['FaceId']
            sns_client = boto3.client('sns')
            message = "Hi, there is an unknown visitor. Here is the photo : " + image_url + " . To add this user click here : " + s3_url + "?uuid=" + face_id
            print(message)
            sns_client.publish(
                PhoneNumber='+13476106330',
                Message=message,
                MessageAttributes={
                    'AWS.SNS.SMS.SMSType': {
                        'DataType': 'String',
                        'StringValue': 'Transactional'
                    }
                })
        else:
            print("known face")
            knownfaceId = decoded_json['FaceSearchResponse'][0]['MatchedFaces'][0]['Face']['FaceId']
            dynamodb = boto3.resource('dynamodb', region_name='us-east-1', endpoint_url="https://dynamodb.us-east-1.amazonaws.com")
            Table_passcodes = dynamodb.Table('passcodes')
            responseFace = Table_passcodes.query(KeyConditionExpression=Key('uuid').eq(knownfaceId))
            if len(responseFace['Items'])==0:
                otp = random.randrange(1000,9999)
                Table_passcodes.put_item(
                  Item={
                        'uuid': knownfaceId,
                        'otp':otp,
                        'expiryTime': Decimal(str(datetime.timestamp(datetime.now()+timedelta(minutes = 5))))
                    }
                    )
            else:
                print('face already processed')
                print(responseFace)
                if str(responseFace['Items'][0]['expiryTime'])<str(Decimal(str(datetime.timestamp(datetime.now())))):
                        otp = random.randrange(1000,9999)
                        Table_passcodes.put_item(
                          Item={
                                'uuid': knownfaceId,
                                'otp':otp,
                                'expiryTime': Decimal(str(datetime.timestamp(datetime.now()+timedelta(minutes = 5))))
                            }
                            )
            
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
