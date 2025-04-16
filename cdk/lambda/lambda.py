import boto3
import json
import os
from datetime import datetime, timedelta
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ce_client = boto3.client('ce')
sns_client = boto3.client('sns')

def get_monthly_cost(start_date, end_date):
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

    logger.debug(response)

    total_cost = 0
    service_costs = {}
    for result in response['ResultsByTime']:
        for group in result['Groups']:
            service = group['Keys'][0]
            cost = float(group['Metrics']['UnblendedCost']['Amount'])
            if service not in service_costs:
                service_costs[service] = 0
            service_costs[service] += cost

            total_cost += cost


    return total_cost, service_costs


def publish_to_sns(last_month_total_cost, current_month_total_cost, current_month_service_costs, sns_topic_arn):
    service_costs_message = "\n".join([f"- {service}: {cost:.2f} USD" for service, cost in current_month_service_costs.items()])

    message = {
        'version': '1.0',
        'source': 'custom',
        'content': {
            'title': 'AWS Cost Notification',
            'description': (
                f"先月の利用料: {last_month_total_cost:.2f} USD\n"
                f"今月の利用料: {current_month_total_cost:.2f} USD\n"
                f"{service_costs_message}"
            )
        }
    }

    logger.info(message)

    response = sns_client.publish(
        TopicArn=sns_topic_arn,
        Subject="AWS Cost Report",
        Message=json.dumps(message)
    )


def lambda_handler(event, context):
    sns_topic_arn = os.environ['SNS_TOPIC_ARN']

    # Current month's period
    current_month_end_date = datetime.utcnow().date()
    current_month_start_date = current_month_end_date.replace(day=1)

    # Last month's period
    last_month_end_date = current_month_start_date - timedelta(days=1)
    last_month_start_date = last_month_end_date.replace(day=1)

    # Get current month's cost
    current_month_total_cost, current_month_service_costs = get_monthly_cost(current_month_start_date, current_month_end_date)

    # Get last month's cost
    last_month_total_cost, last_month_service_costs = get_monthly_cost(last_month_start_date, last_month_end_date)

    publish_to_sns(last_month_total_cost, current_month_total_cost, current_month_service_costs, sns_topic_arn)

    return {
        'status': 'success'
    }

