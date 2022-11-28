#!/usr/bin/env python3
import os

import aws_cdk as cdk

from src.cdkv2_secure_ides_c9_aws_stack import Cdkv2SecureIdesC9AwsStack
from src.stacks.network.cdk_vpc_stack import CdkVPCStack
from project_configs.helpers.project_configs import props, env_devsecops_account, tags

from project_configs.helpers.helper import set_tags

app = cdk.App()

vpc_stack = CdkVPCStack(app, "CdkSecureIDEsVPCStack", props=props['network_definitions'],
                        stack_name= f"DevVPC-{props['project_name']}",
                        env=env_devsecops_account,
                        description="CoreDev Vpc Stack for secure IDEs")
set_tags(vpc_stack, tags)

sec_ides_stack = Cdkv2SecureIdesC9AwsStack(app, "Cdkv2SecureIDEsCloud9AWSStack", props=props,
                                           stack_name= props["project_name"],
                                           env=env_devsecops_account,
                                           vpc=vpc_stack.vpc,
                                           description= "Core stack for Cloud9 Secure Environments"
                                           )
set_tags(sec_ides_stack, tags)
app.synth()
