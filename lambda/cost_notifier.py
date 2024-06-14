import boto3
import json
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import tempfile
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ce_client = boto3.client('ce')
sns_client = boto3.client('sns')

def get_cost_data(start_date, end_date):
    try:
        response = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start_date.strftime('%Y-%m-%d'),
                'End': end_date.strftime('%Y-%m-%d')
            },
            Granularity='DAILY',
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

def plot_cost_data(cost_data, start_date, end_date):
    try:
        dates = [start_date + timedelta(days=i) for i in range((end_date - start_date).days)]
        services = {group['Keys'][0]: [0] * len(dates) for group in cost_data['ResultsByTime'][0]['Groups']}

        for day_index, result in enumerate(cost_data['ResultsByTime']):
            for group in result['Groups']:
                service = group['Keys'][0]
                amount = float(group['Metrics']['UnblendedCost']['Amount'])
                services[service][day_index] = amount

        plt.figure(figsize=(10, 6))
        bottom = [0] * len(dates)

        for service, amounts in services.items():
            plt.bar(dates, amounts, bottom=bottom, label=service)
            bottom = [sum(x) for x in zip(bottom, amounts)]

        plt.xlabel('Date')
        plt.ylabel('Cost ($)')
        plt.title('AWS Cost by Service for Last 7 Days')
        plt.legend(loc='upper left')
        plt.xticks(rotation=45)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.tight_layout()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
            plt.savefig(tmpfile.name)
            plt.close()
            return tmpfile.name
    except Exception as e:
        logger.error("Error plotting cost data: %s", str(e))
        raise

def publish_to_sns(file_path, sns_topic_arn):
    try:
        with open(file_path, 'rb') as file:
            file_content = file.read()

        message = {
            'default': 'AWS Cost by Service',
            'file_content': file_content.decode('latin1')
        }

        response = sns_client.publish(
            TopicArn=sns_topic_arn,
            Message=json.dumps(message),
            MessageStructure='json'
        )

        return response
    except Exception as e:
        logger.error("Error publishing to SNS: %s", str(e))
        raise

def lambda_handler(event, context):
    try:
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=7)

        cost_data = get_cost_data(start_date, end_date)
        file_path = plot_cost_data(cost_data, start_date, end_date)

        sns_topic_arn = os.environ['SNS_TOPIC_ARN']
        response = publish_to_sns(file_path, sns_topic_arn)

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

