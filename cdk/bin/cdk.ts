#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { MainStack } from '../lib/main-stack';

const app = new cdk.App();

const mainStack = new MainStack(app, 'aws-cost-notifier-main', {
  stackName: 'aws-cost-notifier',
});

cdk.Tags.of(mainStack).add("Project","aws-cost-notifier");

