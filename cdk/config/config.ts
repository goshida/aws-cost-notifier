export interface ProjectConfig {
  name: string;
}

export const projectConfig: ProjectConfig = {
  name: 'aws-cost-notifier',
};

export interface MainStackConfig {
  slackWorkspaceIdParameterName: string;
  slackChannelIdParameterName: string;
}

export const mainStackConfig: MainStackConfig = {
  slackWorkspaceIdParameterName: `/goshida/${projectConfig.name}/slack-workspace-id`,
  slackChannelIdParameterName: `/goshida/${projectConfig.name}/slack-channel-id`,
};

