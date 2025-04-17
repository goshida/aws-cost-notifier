#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { MainStack } from '../lib/main-stack';
import { projectConfig } from '../config/config';

const app = new cdk.App();

const mainStack = new MainStack(app, `${projectConfig.name}-main`, {
  stackName: projectConfig.name,
});

cdk.Tags.of(mainStack).add('Project', projectConfig.name);

