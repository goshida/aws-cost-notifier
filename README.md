# aws-cost-notifier

Add `AWS Chatbot` App to Slack Workspace. (The link is available in the AWS Management Console.)

invite `@aws` in slack channel

```bash
aws ssm put-parameter --name "/project/aws-cost-notifier/slack-workspace-id" --value "TXXXXXXXXXX" --type String
aws ssm put-parameter --name "/project/aws-cost-notifier/slack-channel-id" --value "CXXXXXXXXXX" --type String
```

## Useful commands

* `npm run build`   compile typescript to js
* `npm run watch`   watch for changes and compile
* `npm run test`    perform the jest unit tests
* `npx cdk deploy`  deploy this stack to your default AWS account/region
* `npx cdk diff`    compare deployed stack with current state
* `npx cdk synth`   emits the synthesized CloudFormation template
