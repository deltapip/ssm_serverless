import os
import base64
from datetime import datetime
from constructs import Construct
from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_signer as signer,
    aws_secretsmanager as secretsmanager,
    aws_iam as iam,
    aws_events as events,
    aws_events_targets as targets
)

def _read_time_stamp():
    timestamp = datetime.now().timestamp()
    with open('./ssm_serverless/timestamp') as f:
        timestamp = f.readline().strip()
    return timestamp

class SsmServerlessStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        signing_profile = signer.SigningProfile(self, "SigningProfile", 
            platform=signer.Platform.AWS_LAMBDA_SHA384_ECDSA
        )

        code_signing_config = _lambda.CodeSigningConfig(self, "CodeSigningConfig", 
            signing_profiles=[signing_profile]
        )

        secret_generator = secretsmanager.SecretStringGenerator(
            secret_string_template='{}',
            generate_string_key="aes_key",
            exclude_characters="\'\""
        )

        ssm_secret = secretsmanager.Secret(self, "ssm-secret",
            secret_name="ssm_secret",
            generate_secret_string=secret_generator
        )

        secret_policy = iam.PolicyStatement(
            actions=["secretsmanager:GetResourcePolicy",
                     "secretsmanager:GetSecretValue",
                     "secretsmanager:DescribeSecret",
                     "secretsmanager:ListSecretVersionIds"],
            resources=[ssm_secret.secret_arn]
        )

        crypto_layer = _lambda.LayerVersion(self, "pycrypto",
            removal_policy=RemovalPolicy.RETAIN,
            code=_lambda.Code.from_asset("layers/pycrypto.zip"),
            compatible_architectures=[_lambda.Architecture.X86_64]
        )

        environment = {"SSM_VERSION": "0.0.1", "SSM_LOCATION": "usa"}
        timestamp = _read_time_stamp()

        version_lambda = _lambda.Function(
            self, 'ssm-version',
            code_signing_config=code_signing_config,
            runtime=_lambda.Runtime.PYTHON_3_10,
            code=_lambda.Code.from_asset('lambda'),
            handler='version.handler',
            memory_size=1024,
            architecture=_lambda.Architecture.X86_64,
            function_name="ssm_version",
            environment=environment,
            timeout=Duration.seconds(300),
            description=f"Version Resource Handler {timestamp}"
        )

        environment = {"SECRET_NAME": "ssm_secret", "SECRET_KEY": "aes_key"}

        wrap_lambda = _lambda.Function(
            self, 'ssm-wrap',
            code_signing_config=code_signing_config,
            runtime=_lambda.Runtime.PYTHON_3_10,
            code=_lambda.Code.from_asset('lambda'),
            handler='wrap.handler',
            memory_size=1024,
            architecture=_lambda.Architecture.X86_64,
            function_name="ssm_wrap",
            timeout=Duration.seconds(300),
            environment=environment,
            layers = [crypto_layer],
            description=f"Wrap Resource Handler {timestamp}"
        )

        wrap_lambda.add_to_role_policy(secret_policy)

        unwrap_lambda = _lambda.Function(
            self, 'ssm-unwrap',
            code_signing_config=code_signing_config,
            runtime=_lambda.Runtime.PYTHON_3_10,
            code=_lambda.Code.from_asset('lambda'),
            handler='unwrap.handler',
            memory_size=1024,
            architecture=_lambda.Architecture.X86_64,
            function_name="ssm_unwrap",
            timeout=Duration.seconds(300),
            environment=environment,
            layers = [crypto_layer],
            description=f"Unwrap Resource Handler {timestamp}"
        )

        unwrap_lambda.add_to_role_policy(secret_policy)

        ssm_agw = apigw.LambdaRestApi(
            self, 'ssm-endpoint',
            handler=version_lambda,
            rest_api_name="ssm_endpoint"
        )

        version_r = ssm_agw.root.add_resource("version")
        version_r.add_method("GET") # GET /version

        wrap_r = ssm_agw.root.add_resource("wrap")
        wrap_r.add_method("POST", apigw.LambdaIntegration(wrap_lambda))

        unwrap_r = ssm_agw.root.add_resource("unwrap")
        unwrap_r.add_method("POST", apigw.LambdaIntegration(unwrap_lambda))

        environment = {"SECRET_NAME": "github_secret",
                       "SECRET_KEY": "github_token",
                       "ENDPOINT_KEY": "github_endpoint",
                       "USER_KEY": "github_user"}

        integrity_lambda = _lambda.Function(
            self, 'ssm-integrity',
            code_signing_config=code_signing_config,
            runtime=_lambda.Runtime.PYTHON_3_10,
            code=_lambda.Code.from_asset('lambda'),
            handler='integrity.handler',
            memory_size=1024,
            architecture=_lambda.Architecture.X86_64,
            function_name="ssm_integrity",
            timeout=Duration.seconds(60),
            environment=environment,
            description=f"SSM Integrity Handler"
        )

        integrity_target = targets.LambdaFunction(integrity_lambda,
            retry_attempts=3
        )

        rule = events.Rule(self, "integrity-rule",
            rule_name="ssm_integrity_rule",
            event_pattern=events.EventPattern(
                source=["aws.lambda"],
                detail_type=["AWS API Call via CloudTrail"],
                detail={"eventSource": ["lambda.amazonaws.com"],
                        "eventName": ["UpdateFunctionConfiguration20150331v2", "UpdateFunctionCode20150331v2"]}
            ),
            targets=[integrity_target]

        )
