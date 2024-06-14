#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { AwsCostNotifierStack } from '../lib/aws-cost-notifier-stack';

const app = new cdk.App();
new AwsCostNotifierStack(app, 'AwsCostNotifierStack', {
  env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION },
});

