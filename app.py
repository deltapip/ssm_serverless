#!/usr/bin/env python3

import aws_cdk as cdk

from ssm_serverless.ssm_serverless_stack import SsmServerlessStack


app = cdk.App()
SsmServerlessStack(app, "ssm-serverless")

app.synth()
