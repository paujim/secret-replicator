#!/usr/bin/env python3
import constants
from aws_cdk import core
from secret_replicator.secret_replicator_stack import SecretReplicatorStack

env_oregon = core.Environment(
    account=constants.ACCOUNT_ID,
    region=constants.ACCOUNT_REGION,
)

app = core.App()
SecretReplicatorStack(
    scope=app,
    id="secret-replicator",
    env=env_oregon,
)

app.synth()
