import json
import os

SSM_VERSION = os.environ['SSM_VERSION']

SSM_LOCATION = os.environ['SSM_LOCATION']

def handler(event, context):
    # Some Random Comment
    body = {}
    body["version"] = SSM_VERSION
    body["location"] = SSM_LOCATION
    body["path"] = event['path']
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body, indent=2)
    }