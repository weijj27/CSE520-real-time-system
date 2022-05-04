from datetime import datetime
import json
import time
import boto3
import re
from boto3.dynamodb.conditions import Key


def detect_text(photo, bucket):
    tmpCarCount = 2 # setting temporary car number
    client=boto3.client('rekognition')
    pattern = re.compile('^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{4,23}$')
    start = time.time()
    response=client.detect_text(Image={'S3Object':{'Bucket':bucket,'Name':photo}})
    end = time.time()
    txtRcgTime = end - start
    print("Text detection time: ", txtRcgTime)
    #print(response)  
    textDetections=response['TextDetections']
    print ('Detected text\n----------')
    for text in textDetections:
            '''
            print ('Detected text:' + text['DetectedText'])
            print ('Confidence: ' + "{:.2f}".format(text['Confidence']) + "%")
            print ('Id: {}'.format(text['Id']))
            if 'ParentId' in text:
                print ('Parent Id: {}'.format(text['ParentId']))
            print ('Type:' + text['Type'])
            '''
            if getCarPlate(text['DetectedText'], pattern) :
                detectedText = text['DetectedText']
                my_print(detectedText, "detectedText")

                start = time.time()
                fee, pos = process_car(detectedText, tmpCarCount)
                end = time.time()
                dtProTime = end - start
                print("Text detection time: ",dtProTime)

                print(pos)
                if (pos == "FULL"):
                    break

                print("=========== publish to iot=======================")
                dict = gnrtMsg(fee, detectedText, txtRcgTime, dtProTime)                
                push_info_iot(dict)

                break
            print()
    return len(textDetections)


def pre_process(tmpCarCount):
    tmpCar = query_tmpCar()
    #print(tmpCar)
    if len(tmpCar) >= tmpCarCount:
        return "FULL"
    return "Not Full"


def gnrtMsg(fee, detectedText, txtRcgTime, dtProTime):
    dict = {}
    dict["car_plate"] = detectedText
    dict["fee"] = fee
    info_in_db = query_car_plate(detectedText)
    if len(info_in_db) == 0:
        # tmp car out
        dict["status"] = "tmp"
        dict["in_and_out"] = "out"
    else:
        if info_in_db[0]["status"] == "perminent":
            # perminent car in and out
            dict["status"] = "perminent"
            dict["car_position"] = info_in_db[0]["car_position"]
            if info_in_db[0]["in_time"] == "":
                dict["in_and_out"] = "out"
            else:
                dict["in_and_out"] = "in"
        else:
            # tmp car in
            dict["status"] = "tmp"
            dict["in_and_out"] = "in"
        
    dict['send_time'] = time.time()
    dict['text_recog_time'] = txtRcgTime
    dict['data_process_time'] = dtProTime
    return dict


# https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GettingStarted.Python.html
def process_car(detectedText, tmpCarCount):
    info_in_db = query_car_plate(detectedText)
    fee = 0
    pos = "Not Full"
    if len(info_in_db) == 0:
        # tmp car in
        status = "temp"
        pos = pre_process(tmpCarCount)
        if (pos == "Not Full"): 
            push_info_db(detectedText, status, str(datetime.now()))
    else:
        if info_in_db[0]["status"] == "perminent":
            if info_in_db[0]["in_time"] == "":
                # perminent car in
                updatePerminent(info_in_db[0], str(datetime.now()))
            else: 
                # perminent car out
                updatePerminent(info_in_db[0], "")
        else:
            # temp car out
            fee = calculateFee(info_in_db[0])
            deleteTmpCar(detectedText)
    print(fee)      
    return fee, pos


def deleteTmpCar(detectedText):
    aws_key, aws_secret = getKeySecret()
    dynamodb = boto3.resource('dynamodb',aws_access_key_id=aws_key, aws_secret_access_key=aws_secret,region_name="us-east-1")
    table = dynamodb.Table('car_plate')

    response = table.delete_item(
        Key={
             'plate_Number': detectedText,
        },
    )
    return 


def calculateFee(info_in_db):
    prev = datetime.strptime(info_in_db["in_time"],"%Y-%m-%d %H:%M:%S.%f")
    cur = datetime.now()
    diff = (cur - prev).seconds
    return round(diff)


def updatePerminent(info_in_db, updateVal):
    aws_key, aws_secret = getKeySecret()
    dynamodb = boto3.resource('dynamodb',aws_access_key_id=aws_key, aws_secret_access_key=aws_secret,region_name="us-east-1")
    table = dynamodb.Table('car_plate')
    response = table.update_item(
        Key={
            'plate_Number': info_in_db["plate_Number"],
        },
        UpdateExpression="set in_time = :r",
        ExpressionAttributeValues={
            ':r': updateVal
        },
        ReturnValues="UPDATED_NEW"
    )
    return


def my_print(contxt, descripiton):
    print("==========Query %s =============" %(descripiton))
    print(contxt)
    print("==========Query %s =============" %(descripiton))
    return


def getCarPlate(detectedText, pattern):
    matched = pattern.match(detectedText)
    if matched is not None:
        return True
    else:
        return False


def getKeySecret():
    aws_key = "AKIA3CPRYB4EAIHAFDUT"# 【你的 aws_access_key】 
    aws_secret = "+7hoL+U1MemwXHamrzNm5c99zvONFyQ5uwZuRDEu" # 【你的 aws_secret_key】 
    return aws_key, aws_secret


def push_info_db(detectedText, status, time):
    aws_key, aws_secret = getKeySecret()
    dynamodb = boto3.resource('dynamodb',aws_access_key_id=aws_key, aws_secret_access_key=aws_secret,region_name="us-east-1")

    table = dynamodb.Table('car_plate')
    response = table.put_item(
       Item={
            'plate_Number': detectedText,
            'in_time': time,
            'status': status,
        }
    )
    #print(response)
    return


def push_info_iot(info):
    #https://iotespresso.com/publishing-from-lambda-to-an-aws-iot-topic/
    mytopic = '$aws/things/car_iot/shadow/name/car_shadow/update'
    client = boto3.client('iot-data', region_name='us-east-1')
    response = client.publish(topic=mytopic, qos=1, payload=json.dumps(info))  
    print(response)
    return


def query_car_plate(detectedText, dynamodb=None):
    if not dynamodb:
        aws_key, aws_secret = getKeySecret()
        dynamodb = boto3.resource('dynamodb',aws_access_key_id=aws_key, aws_secret_access_key=aws_secret,region_name="us-east-1")

    table = dynamodb.Table('car_plate')
    response = table.query(
        KeyConditionExpression=Key('plate_Number').eq(detectedText)
    )
    return response['Items']


def query_tmpCar(dynamodb=None):
    if not dynamodb:
        aws_key, aws_secret = getKeySecret()
        dynamodb = boto3.resource('dynamodb',aws_access_key_id=aws_key, aws_secret_access_key=aws_secret,region_name="us-east-1")

    table = dynamodb.Table('car_plate')
    scan_kwargs = {
        'FilterExpression': Key('status').eq("temp")
    }
    response = table.scan(**scan_kwargs)
    return response['Items']


def lambda_handler(event, context):
    # TODO implement
    bucket='smartpark'
    #photo='images/car_plate.jpg'
    photo='images/test.jpg'
    text_count=detect_text(photo,bucket)
    print("Text detected: " + str(text_count))
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
