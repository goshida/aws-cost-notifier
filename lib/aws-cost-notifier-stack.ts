import * as cdk from 'aws-cdk-lib';
import { aws_lambda as lambda,
         aws_sns as sns,
         aws_sns_subscriptions as sns_subscriptions,
         aws_iam as iam,
         aws_events as events,
         aws_events_targets as targets,
         aws_ssm as ssm,
         aws_chatbot as chatbot } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as path from 'path';
import { settings } from '../config';

export class AwsCostNotifierStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // SNS
    const snsTopic = new sns.Topic(this, 'CostNotificationTopic', {
      displayName: 'AWS Cost Notification Topic',
    });

    new chatbot.SlackChannelConfiguration(this, 'SlackChannel', {
      slackChannelConfigurationName: 'CostNotifierChannel',
      slackWorkspaceId: ssm.StringParameter.valueForStringParameter(this, settings.slack_workspace_id_key),
      slackChannelId: ssm.StringParameter.valueForStringParameter(this, settings.slack_channel_id_key),
      notificationTopics: [snsTopic],
    });

    // Lambda
    const costNotifierLambda = new lambda.Function(this, 'CostNotifierLambda', {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'cost_notifier.lambda_handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambda')),
      environment: {
        SNS_TOPIC_ARN: snsTopic.topicArn,
      },
      timeout: cdk.Duration.minutes(5),
    });

    costNotifierLambda.addToRolePolicy(new iam.PolicyStatement({
      actions: ['ce:GetCostAndUsage'],
      resources: ['*'],
    }));

    costNotifierLambda.addToRolePolicy(new iam.PolicyStatement({
      actions: ['sns:Publish'],
      resources: [snsTopic.topicArn],
    }));

    // EventBridge
    const rule = new events.Rule(this, 'Rule', {
      schedule: events.Schedule.cron({ minute: '0', hour: '0', day: '5,10,15,20,25,30', month: '*', year: '*' }),
    });

    rule.addTarget(new targets.LambdaFunction(costNotifierLambda));
  }
}

