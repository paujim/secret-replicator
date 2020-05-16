import boto3
import logging
from os import environ

targetRegions = environ.get('TargetRegions')
if targetRegions == None:
    raise Exception('Environment variable TargetRegions must be set')

target = targetRegions.split(";")

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sm_source = boto3.client('secretsmanager')

sm_targets = []

for targetRegion in target:
    sm_targets.append(boto3.client('secretsmanager', region_name=targetRegion))


def handler(event, context):
    logger.info('REQUEST:\n %s', event)
    detail = event['detail']
    event_name = detail['eventName']

    try:
        if event_name == 'CreateSecret':
            logger.info('New secret')
            secretId = detail['requestParameters']['name']
            response = sm_source.get_secret_value(SecretId=secretId)
            secretValue = response['SecretString']
            for target in sm_targets:
                target.create_secret(
                    Name=secretId,
                    SecretString=secretValue,
                    Description='Replicated Secret - Do not modify',
                )
                logger.info('Replicating secret [{0}]'.format(
                    secretId))

        elif event_name == 'PutSecretValue':
            logger.info('Update secret')
            secretId = detail['requestParameters']['secretId']

            response = sm_source.get_secret_value(SecretId=secretId)
            secretValue = response['SecretString']

            for target in sm_targets:
                try:
                    target.put_secret_value(
                        SecretId=secretId,
                        SecretString=secretValue,
                    )
                    logger.info('Updating secret [{0}]'.format(
                        secretId))
                except target.exceptions.ResourceNotFoundException:
                    target.create_secret(
                        Name=secretId,
                        SecretString=secretValue,
                        Description='Replicated Secret - Do not modify',
                    )
                    logger.info('Creating secret [{0}]'.format(
                        secretId))

        else:
            logger.info('Nothing to do')
        logger.info('Event Processed')

    except Exception as error:
        logger.info(str(error))
