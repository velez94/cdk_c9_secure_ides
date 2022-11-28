import aws_cdk as cdk
# For consistency with other languages, `cdk` is the preferred import name for
# the CDK's src module.  The following line also imports it as `src` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.
from aws_cdk import (
    aws_ec2 as ec2
)

from .lib.ides.cdk_cloud9_custom_env_stack import CdkCloud9CustomEnvConstruct
from constructs import Construct


class Cdkv2SecureIdesC9AwsStack(cdk.Stack):

    def __init__(self, scope: Construct, construct_id: str, props: dict = None, vpc: ec2.IVpc = None,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        for env in props['environment_props']:
            self.env = CdkCloud9CustomEnvConstruct(self, f"SecEnv-{env['environment_name']}", props=env, vpc=vpc)
