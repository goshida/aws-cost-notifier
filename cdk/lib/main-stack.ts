import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import {
  aws_ssm as ssm,
  aws_sns as sns,
  aws_chatbot as chatbot,
  aws_logs as logs,
  aws_iam as iam,
  aws_lambda as lambda,
  aws_events as events,
  aws_events_targets as events_targets,
} from 'aws-cdk-lib';
import * as path from 'path';
import { projectConfig, mainStackConfig } from '../config/config';

export class MainStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Notifier
    const topic = new sns.Topic(this, 'topic', {
      topicName: `${projectConfig.name}-topic`,
    });

    const chatbotRole = new iam.Role(this, 'chatbot-role', {
      roleName: `${projectConfig.name}-chatbot-role`,
      assumedBy: new iam.ServicePrincipal('chatbot.amazonaws.com'),
    });

    const slackWorkspaceId = ssm.StringParameter.valueForStringParameter(
      this,
      mainStackConfig.slackWorkspaceIdParameterName
    );

    const slackChannelId = ssm.StringParameter.valueForStringParameter(
      this,
      mainStackConfig.slackChannelIdParameterName
    );

    const slackChannelConfiguration = new chatbot.SlackChannelConfiguration(this, 'slack-channel-configuration', {
      slackChannelConfigurationName: `${projectConfig.name}-slack-channel-configuration`,
      slackWorkspaceId: slackWorkspaceId,
      slackChannelId: slackChannelId,
      notificationTopics: [topic],
      role: chatbotRole,
    });

    // Processor
    const logGroup = new logs.LogGroup(this, 'lambda-log-group', {
      logGroupName: `/aws/lambda/${projectConfig.name}-lambda`,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      retention: logs.RetentionDays.THREE_MONTHS,
    });

    const lambdaRole = new iam.Role(this, 'lambda-role', {
      roleName: `${projectConfig.name}-lambda-role`,
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
    });

    lambdaRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['ce:GetCostAndUsage'],
      resources: ['*'],
    }));

    lambdaRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ['sns:Publish'],
      resources: [topic.topicArn],
    }));

    const lambdaFunction = new lambda.Function(this, 'lambda', {
      runtime: lambda.Runtime.PYTHON_3_12,
      functionName: `${projectConfig.name}-lambda`,
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambda')),
      handler: 'lambda.lambda_handler',
      environment: {
        SNS_TOPIC_ARN: topic.topicArn,
      },
      timeout: cdk.Duration.minutes(5),
      reservedConcurrentExecutions: 1,
      logGroup: logGroup,
      role: lambdaRole,
    });

    // Trigger
    const rule = new events.Rule(this, 'trigger', {
      ruleName: `${projectConfig.name}-trigger`,
      schedule: events.Schedule.cron({
        minute: '0',
        hour: '0',
        day: '5,10,15,20,25,30',
      }),
    });

    rule.addTarget(
      new events_targets.LambdaFunction(lambdaFunction)
    );

  }
}

