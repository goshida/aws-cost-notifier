# aws-cost-notifier

AWSの利用料金をSlackに通知する

## セットアップ

### パラメータストアの設定

通知先の Slack の設定をパラメータストアに保存

```bash
aws ssm put-parameter \
  --type "String" \
  --name "/goshida/aws-cost-notifier/slack-workspace-id" \
  --value "T0000000000" \
  --tags "Key=Project,Value=aws-cost-notifier"

aws ssm put-parameter \
  --type "String" \
  --name "/goshida/aws-cost-notifier/slack-channel-id" \
  --value "C0000000000" \
  --tags "Key=Project,Value=aws-cost-notifier"
```

### CDK のデプロイ

```bash
cd cdk
npx cdk deploy
```

