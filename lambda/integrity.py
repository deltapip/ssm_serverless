import json
import os

SECRET_NAME = os.environ['SECRET_NAME']

SECRET_KEY = os.environ['SECRET_KEY']

def handler(event, context):
    function_name = event["detail"]["requestParameters"]["functionName"]
    userName = event["detail"]["userIdentity"]["sessionContext"]["sessionIssuer"]["userName"]

    if function_name in ["ssm_version", "ssm_wrap", "ssm_unwrap"] and "cdk" not in userName:
        print("SSM Application has drifted")
        print(event)
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps({"meesage": "Got code change event"}, indent=2)
    }