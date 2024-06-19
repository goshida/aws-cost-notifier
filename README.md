# aws-cost-notifier

## Requirements

- AWS CLI
- Node.js
  - TypeScript
- Python (3.12>)

Setup

```bash
mise install

npm install
```


## Usage

Add `AWS Chatbot` App to Slack Workspace. (The link is available in the AWS Management Console.)

invite `@aws` to slack channel

set parameter to ParameterStore

```bash
aws ssm put-parameter --name "/project/aws-cost-notifier/slack-workspace-id" --value "TXXXXXXXXXX" --type String
aws ssm put-parameter --name "/project/aws-cost-notifier/slack-channel-id" --value "CXXXXXXXXXX" --type String
```

deploy

```bash
cdk deploy
```

