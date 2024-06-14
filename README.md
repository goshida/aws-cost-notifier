# aws-cost-notifier

```bash
aws ssm put-parameter --name "/my-app/slack-webhook-url" --value "https://hooks.slack.com/services/XXXXX/YYYYY/ZZZZZ" --type SecureString
```

## Useful commands

* `npm run build`   compile typescript to js
* `npm run watch`   watch for changes and compile
* `npm run test`    perform the jest unit tests
* `npx cdk deploy`  deploy this stack to your default AWS account/region
* `npx cdk diff`    compare deployed stack with current state
* `npx cdk synth`   emits the synthesized CloudFormation template
