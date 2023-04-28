
# Welcome to Serverless SSM Project!

The Serverless Software Security Module (SSM) project is a sample application that aims to demonstrate one way the GitOps model can be implemented using the AWS serverless stack. The application will use API Gateway, Lambda, Secret Manager, and Event Bridge. Resources provisioned under these services work together to provide a simple microservice that implements a symmetric encryption/decryption API. 

This project is inspired by the way gitops is implemented in Kubernetes via [ArgoCD](https://argo-cd.readthedocs.io/en/stable/). There are two main gitops principles at work with ArgoCD. First, every commit to a git repository containing K8 resources will result in a deployment of resources modified to a target Kubernetes cluster. Second, every change to K8 resources in the target cluster triggers a re-deployment of those resources in git repository. These principles guarantee the git repository is the source of truth.

With the AWS Serverless stack there is no such thing as K8 resources but rather we are working with serverless cloud resources. If we apply the same gitops principles in this context, the following constraints apply: 
* Every commit that changes the code or the configuration of cloud resources results in an automated deployment of the application to target AWS account and region.
* Every change to application code or cloud resources configuration not coming from a git repo deployment flow results in the re-deployment of the application.

[CDK](https://aws.amazon.com/cdk/) is used to deploy the application. A github workflow will detect new commits and trigger the cdk deploy. One of the resources deployed in the application is an EventBridge rule that will trigger if the application code or application configuration changes outside the CDK deploy flow. The trigger will execute a lambda function that will invoke the same cdk deploy flow to make sure resource in github are synchronized with those running in AWS account.

To start using locally make sure you have python3 and cdk installed and do the following
```
git clone git@github.com:deltapip/ssm_serverless.git
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If it is the first time running CDK on a specific AWS account make sure you run:
```
cdk bootstrap
```

Start making your changes. To test against your AWS account do this:
```
cdk synth
cdk deploy
```

Once you do the first deploy calling `cdk diff` will tell you what is different between your stack and the one deployed on the target aws account.

## Event Driven GitOps

This repository is already configured to implement GitOps. When a commit changing the code or the cdk stack is pushed, a github workflow is triggered to deploy the new cdk stack. In addition, when the code or the configuration of the application is modified outside a cdk stack deploy, a lambda function (ssm_integrity) will be triggered to execute the gihub workflow remotely.

To enable GitOps two things need to happen, we need to provide github workflow with the aws credentials via github secrets to be able to deploy the cdk stack. We also need to provide the ssm_integrity lambda with the github credentials to be able to trigger the github workflow.

In github repository do the following:

* Create two secrets (AWS_ACCESS_KEY, AWS_SECRET_KEY) by going to settings -> secrets -> actions

In your github user settings do the following:

* Create an Personal Access Token by going to Developer Settings
* Make a note of the token

In your AWS account target region do the following:
* Go to Secrets Manager Service
* Create a secret named github_secret
* Create an object in the github_secret with the following fields:

```
github_token: <your personal access token>
github_endpoint: https://api.github.com/repos/<your github user>/ssm_serverless/contents/
github_user: <your github user>
```
* Update secret permission to add a Resource Policy:

```
{
  "Version" : "2012-10-17",
  "Statement" : [ {
    "Effect" : "Allow",
    "Principal" : {
      "AWS" : "<arn of the execution role of the ssm_integrity lambda>"
    },
    "Action" : "secretsmanager:GetSecretValue",
    "Resource" : "*"
  } ]
}
```
 Notice that to be able to get the arn of the ssm_integrity lambda, the cdk stack needs to be deployed at least once so that the lambda and its execution role exist. 

 Once the credentials exchange between gihub and aws is done, your AWS event driven GitOps is life 

Enjoy!
