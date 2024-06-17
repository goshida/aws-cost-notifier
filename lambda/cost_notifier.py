import boto3
import json
import os
from datetime import datetime, timedelta
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ce_client = boto3.client('ce')
sns_client = boto3.client('sns')

def get_monthly_cost_data(start_date, end_date):
    try:
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }
            ]
        )
        return response
    except Exception as e:
        logger.error("Error getting cost data: %s", str(e))
        raise

def get_total_monthly_cost_data(start_date, end_date):
    try:
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='MONTHLY',
            Metrics=['UnblendedCost']
        )
        return response
    except Exception as e:
        logger.error("Error getting total monthly cost data: %s", str(e))
        raise

def process_monthly_cost_data(cost_data):
    total_cost = 0
    service_costs = {}

    for result in cost_data['ResultsByTime']:
        for group in result['Groups']:
            service = group['Keys'][0]
            amount = float(group['Metrics']['UnblendedCost']['Amount'])
            total_cost += amount
            if service not in service_costs:
                service_costs[service] = 0
            service_costs[service] += amount

    return total_cost, service_costs

def publish_to_sns(last_month_cost, total_cost, service_costs, sns_topic_arn):
    try:
        service_costs_message = "\n".join([f"- {service}: {cost:.2f} USD" for service, cost in service_costs.items()])

        description = (
            f"先月の利用料: {last_month_cost:.2f} USD\n"
            f"今月の利用料: {total_cost:.2f} USD\n"
            f"{service_costs_message}"
        )

        # Custom notifications for AWS Chatbot
        message = {
            "version" : "1.0",
            "source" : "custom",
            "content" : {
                "title" : "AWS Cost Notification",
                "description" : description
            }
        }
        print(json.dumps(message))

        response = sns_client.publish(
            TopicArn=sns_topic_arn,
            Message=json.dumps(message),
            Subject="AWS Cost Report"
        )

        return response
    except Exception as e:
        logger.error("Error publishing to SNS: %s", str(e))
        raise

def lambda_handler(event, context):
    try:
        end_date = datetime.utcnow().date()
        start_date = end_date.replace(day=1)

        # Get current month's cost data
        current_cost_data = get_monthly_cost_data(start_date, end_date)
        total_cost, service_costs = process_monthly_cost_data(current_cost_data)

        # Get last month's total cost data
        first_day_of_current_month = end_date.replace(day=1)
        last_day_of_last_month = first_day_of_current_month - timedelta(days=1)
        first_day_of_last_month = last_day_of_last_month.replace(day=1)
        last_month_cost_data = get_total_monthly_cost_data(first_day_of_last_month, first_day_of_current_month)
        last_month_cost = float(last_month_cost_data['ResultsByTime'][0]['Total']['UnblendedCost']['Amount'])

        sns_topic_arn = os.environ['SNS_TOPIC_ARN']
        response = publish_to_sns(last_month_cost, total_cost, service_costs, sns_topic_arn)

        return {
            'statusCode': response['ResponseMetadata']['HTTPStatusCode'],
            'body': json.dumps('SNS notification sent')
        }
    except Exception as e:
        logger.error("Error in lambda_handler: %s", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps('Internal server error')
        }
