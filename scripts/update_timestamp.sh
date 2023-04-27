#!/usr/bin/env bash

timestamp=$(python -c 'from datetime import datetime; print(datetime.now().timestamp())')
echo $timestamp > ./lambda/timestamp
echo $timestamp > ./ssm_serverless/timestamp