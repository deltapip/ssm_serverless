from datetime import datetime
import json
import os
import urllib3
import base64
import boto3
from botocore.exceptions import ClientError

SECRET_NAME = os.environ['SECRET_NAME']
SECRET_KEY = os.environ['SECRET_KEY']
ENDPOINT_KEY = os.environ['ENDPOINT_KEY']
USER_KEY = os.environ['USER_KEY']

def _get_github_secrets():
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager'
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=SECRET_NAME
        )
    except ClientError as e:
        raise e

    # Decrypts secret using the associated KMS key.
    secret = get_secret_value_response['SecretString']
    secret_o = json.loads(secret)
    
    return secret_o[SECRET_KEY], secret_o[ENDPOINT_KEY], secret_o[USER_KEY]


def _push_sync_commit(file, d_type):
    github_token, github_endpoint, github_user = _get_github_secrets()
    file_url = f"{github_endpoint}{file}"
    timestamp = str(datetime.now().timestamp())
    

    headers = {"Accept": "application/vnd.github+json",
               "Authorization": f"Bearer {github_token}",
               "User-Agent": github_user
               }

    http = urllib3.PoolManager()

    r = http.request('GET', file_url, headers=headers)

    output = json.loads(r.data.decode("utf-8"))
    sha = output["sha"]

    body = json.dumps({
        "message": f"SSM Application {d_type} have drifted, synchronizing",
        "content": base64.b64encode(timestamp.encode("utf-8")).decode("utf-8"),
        "sha": sha
    })

    r = http.request('PUT', file_url, headers=headers, body=body)
    if r.status != 200:
        raise Exception(r.data.decode("utf-8"))


def handler(event, context):
    function_name = event["detail"]["requestParameters"]["functionName"]
    event_name = event["detail"]["eventName"]
    user_name = event["detail"]["userIdentity"]["sessionContext"]["sessionIssuer"]["userName"]

    if function_name in ["ssm_version", "ssm_wrap", "ssm_unwrap"] and "cdk" not in user_name:
        print("SSM Application has drifted")
        print(event)
        if "UpdateFunctionConfiguration" in event_name:
            _push_sync_commit("ssm_serverless/timestamp", "configuration")
        elif "UpdateFunctionCode" in event_name:
            _push_sync_commit("lambda/timestamp", "code")
        else:
            print("Event name does not match supported events.")

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps({"message": "Got code change event"}, indent=2)
    }
