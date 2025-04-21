import boto3
import json
import os
import logging
from datetime import datetime, timedelta, timezone
from collections import defaultdict

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# サービスコストで 0.01 未満のものは Other として集計
COST_THRESHOLD = 0.01
# 当月に加えて過去 1 ヶ月分のデータを取得
PAST_MONTHS = 1

ce_client = boto3.client('ce')
sns_client = boto3.client('sns')

def get_monthly_costs(start_date, end_date):
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

    logger.debug(f"Cost Explorer のレスポンス: {response}")

    monthly_costs = {}
    for result in response['ResultsByTime']:
        month = result['TimePeriod']['Start'][:7]  # YYYY-MM
        monthly_costs[month] = {
            'total_cost': 0,
            'service_costs': {}
        }
        for group in result['Groups']:
            service = group['Keys'][0]
            cost = float(group['Metrics']['UnblendedCost']['Amount'])
            monthly_costs[month]['service_costs'][service] = cost
            monthly_costs[month]['total_cost'] += cost

    logger.debug(f"月別のコスト: {monthly_costs}")

    return monthly_costs

def format_service_costs(service_costs):
    # Taxを分離
    tax_cost = service_costs.pop('Tax', 0)
    
    # その他のサービスを集計
    other_services = defaultdict(float)
    for service, cost in list(service_costs.items()):
        if cost < COST_THRESHOLD:
            other_services['Other'] += cost
            service_costs.pop(service)
    
    # コストの高い順にソート
    sorted_services = sorted(
        service_costs.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    # Otherのコストを追加
    if other_services['Other'] > 0:
        sorted_services.append(('Other', other_services['Other']))
    
    # Taxを最後に追加
    if tax_cost > 0:
        sorted_services.append(('Tax', tax_cost))
    
    return sorted_services

def publish_to_sns(monthly_costs, sns_topic_arn):
    months = sorted(monthly_costs.keys(), reverse=True)[:PAST_MONTHS + 1]

    # PAST_MONTHS + 1 ヶ月分のデータがあるか確認
    if len(months) < PAST_MONTHS + 1:
        logger.error(f"{PAST_MONTHS + 1}ヶ月分のデータがありません")
        return

    current_month = months[0]
    current_month_data = monthly_costs[current_month]

    # サービス別のコストを整形
    formatted_services = format_service_costs(current_month_data['service_costs'])
    
    # 過去 PAST_MONTHS ヶ月分のコストを表示
    monthly_costs_message = "\n".join([
        f"{month[:4]}年{month[5:7]}月の利用料 : {monthly_costs[month]['total_cost']:.2f} USD"
        for month in months
    ])

    service_costs_message = "\n".join([
        f"- {service} : {cost:.2f} USD"
        for service, cost in formatted_services
    ])

    message = {
        'version': '1.0',
        'source': 'custom',
        'content': {
            'title': 'AWS Cost Notification',
            'description': (
                f"{monthly_costs_message}\n"
                f"{service_costs_message}"
            )
        }
    }

    logger.info(f"SNS に通知するメッセージ: {message}")

    response = sns_client.publish(
        TopicArn=sns_topic_arn,
        Subject="AWS Cost Report",
        Message=json.dumps(message)
    )

def lambda_handler(event, context):
    sns_topic_arn = os.environ['SNS_TOPIC_ARN']

    # 集計期間の計算 ( 当月 + 過去 PAST_MONTHS ヶ月 )
    term_end = datetime.now(timezone.utc).date()
    term_start = term_end.replace(day=1)
    for _ in range(PAST_MONTHS):
        term_start = (term_start - timedelta(days=1)).replace(day=1)

    logger.info(f"集計期間: {term_start} から {term_end}")

    # 集計期間のコストを取得
    monthly_costs = get_monthly_costs(term_start, term_end)

    # SNS に通知
    publish_to_sns(monthly_costs, sns_topic_arn)

    return {
        'status': 'success'
    }

