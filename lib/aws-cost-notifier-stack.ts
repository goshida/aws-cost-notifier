import * as cdk from 'aws-cdk-lib';
import { aws_lambda as lambda,
         aws_sns as sns,
         aws_sns_subscriptions as sns_subscriptions,
         aws_iam as iam,
         aws_events as events,
         aws_events_targets as targets,
         aws_ssm as ssm } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as path from 'path';
import { SLACK_WEBHOOK_URL_KEY } from '../config';

export class AwsCostNotifierStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // SNS
    const snsTopic = new sns.Topic(this, 'CostNotificationTopic', {
      displayName: 'AWS Cost Notification Topic',
    });

    const slackWebhookUrl = ssm.StringParameter.valueForStringParameter(this, SLACK_WEBHOOK_URL_KEY);

    snsTopic.addSubscription(new sns_subscriptions.UrlSubscription(slackWebhookUrl, {
      protocol: sns.SubscriptionProtocol.HTTPS
    }));

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
      schedule: events.Schedule.cron({ minute: '0', hour: '0', day: 'SUN', month: '*', year: '*' }),
    });

    rule.addTarget(new targets.LambdaFunction(costNotifierLambda));
  }
}

