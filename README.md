# CSE520-real-time-system

## Code
- text_detect.py 

  including text recognition, data processing, and data transfer from AWS to Raspberry PI

- ui.py

  including UI logic, motor control logic, camera control logic and configuration of Raspberry PI
  
  
## How to run

- Replace your own AWS certificate in the code in ui.py
- Replace your own DynamoDB key, S3 Bucket key in text_detect.py
- Generate your own AWS DynamoDB, IOT, S3 Bucket and Lambda service
- Create table in DynamoDB according to the report

## Install

- Deploy text_detect.py on AWS Lambda function
- Deploy ui.py on the Raspberry PI
- Deploy configurations for AWS services
