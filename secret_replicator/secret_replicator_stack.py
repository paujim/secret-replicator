import constants
from os import path
from aws_cdk import (
    core,
    aws_iam as iam,
    aws_logs as logs,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
)


class SecretReplicatorStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        replicator_role = iam.Role(
            scope=self,
            role_name='SecretsManagerRegionReplicatorRole',
            id='region-replicator-role',
            assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
            inline_policies={'ReplicatorPermissions': iam.PolicyDocument(
                statements=[
                      iam.PolicyStatement(
                          resources=['*'],
                          actions=[
                              'kms:Decrypt',
                              'kms:Encrypt',
                              'kms:GenerateDataKey',
                          ]),
                      iam.PolicyStatement(
                          resources=['arn:aws:secretsmanager:{region}:{account}:secret:*'.format(
                              region=constants.ACCOUNT_REGION,
                              account=constants.ACCOUNT_ID)],
                          actions=[
                              'secretsmanager:DescribeSecret',
                              'secretsmanager:GetSecretValue'
                          ]),
                      iam.PolicyStatement(
                          resources=['arn:aws:secretsmanager:{region}:{account}:secret:*'.format(
                              region=constants.TARGET_REGION_1,
                              account=constants.ACCOUNT_ID)],
                          actions=[
                              'secretsmanager:CreateSecret',
                              'secretsmanager:UpdateSecretVersionStage',
                              'secretsmanager:PutSecretValue',
                              'secretsmanager:DescribeSecret'
                          ]),
                      iam.PolicyStatement(
                          resources=['arn:aws:secretsmanager:{region}:{account}:secret:*'.format(
                              region=constants.TARGET_REGION_2,
                              account=constants.ACCOUNT_ID)],
                          actions=[
                              'secretsmanager:CreateSecret',
                              'secretsmanager:UpdateSecretVersionStage',
                              'secretsmanager:PutSecretValue',
                              'secretsmanager:DescribeSecret'
                          ]),
                ]
            )},
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    managed_policy_name='service-role/AWSLambdaBasicExecutionRole'),
            ]
        )

        fn = _lambda.Function(
            scope=self,
            id='replicator-lambda',
            runtime=_lambda.Runtime.PYTHON_3_8,
            role=replicator_role,
            handler='index.handler',
            code=_lambda.Code.from_asset(path=path.join(
                'lambda')),
            log_retention=logs.RetentionDays.ONE_WEEK,
            retry_attempts=0,
            environment={
                'TargetRegions': constants.TARGET_REGION_1 + ";" + constants.TARGET_REGION_2,
            },
        )

        rule = events.Rule(
            scope=self,
            id='event-rule',
        )

        rule.add_target(target=targets.LambdaFunction(handler=fn))
        rule.add_event_pattern(
            source=['aws.secretsmanager'],
            detail_type=['AWS API Call via CloudTrail'],
            region=[constants.ACCOUNT_REGION],
            detail={
                "eventSource": ['secretsmanager.amazonaws.com'],
                "eventName": ['CreateSecret', 'PutSecretValue']
            }
        )
