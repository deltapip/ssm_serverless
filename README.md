
# Welcome to Serverless SSM Project!

The Serverless Software Security Module (SSM) project is a sample application that aims to demonstrate one way the GitOps model can be implemented using the AWS serverless stack. The application will use API Gateway, Lambda, Secret Manager, and Event Bridge. Resources provisioned under these services work together to provide a simple microservice that implements a symmetric encryption/decryption API. 

This project is inspired by the way gitops is implemented in Kubernetes via [ArgoCD](https://argo-cd.readthedocs.io/en/stable/). There are two main gitops principles at work with ArgoCD. First, every commit to a git repository containing K8 resources will result in a deployment of resources modified to a target Kubernetes cluster. Second, every change to K8 resources in the target cluster triggers a re-deployment of those resources in git repository. These principles guarantee the git repository is the sources of truth.

With the AWS Serverless stack there is no such thing as K8 resources but rather we are working with serverless cloud resources. If we apply the same gitops principles in this context, the following constraints apply: 
* Every commit that changes the code or the configuration of cloud resources results in an automated deployment of the application to target AWS account and region.
* Every change to application code or cloud resources configuration not coming from a git repo deployment flow results in the re-deployment of the application.

[CDK](https://aws.amazon.com/cdk/) is used to deploy the application. A github workflow will detect new commits and trigger the cdk deploy. One of the resources deployed in the application is an EventBridge rule that will trigger if the application code or application configuration changes outside the CDK deploy flow. The trigger will execute a lambda function that will invoke the same cdk deploy flow to make sure resource in github are synchronized with those running in AWS account.

Enjoy!
