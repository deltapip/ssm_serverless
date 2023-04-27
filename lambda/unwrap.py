#!/usr/bin/env python

import base64
import sys
from Crypto import Random
from Crypto.Cipher import AES
import json
import boto3
from botocore.exceptions import ClientError
import os

SECRET_NAME = os.environ['SECRET_NAME']

SECRET_KEY = os.environ['SECRET_KEY']

def _get_key():
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
    
    return secret_o[SECRET_KEY]


def _decrypt(string_key, cipher):
    key = bytes(string_key, 'utf-8')
    cipher_bytes = base64.b64decode(cipher)
    iv = cipher_bytes[:AES.block_size]
    cipher = AES.new(key, AES.MODE_CFB, iv)
    final_msg= cipher.decrypt(cipher_bytes[AES.block_size:])
    return final_msg.decode("utf8")


def handler(event, context):
    # Some Random Comment
    body = event['body']
    cipher = json.loads(body)['cipher']
    key = _get_key()
    text = _decrypt(key, cipher)
    body = {}
    body["text"] = text
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body, indent=2)
    }
