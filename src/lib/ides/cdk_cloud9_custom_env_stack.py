import os

import aws_cdk as cdk
from aws_cdk import (
    aws_cloud9 as cloud9,
    aws_ec2 as ec2,
    aws_codecommit as codecommit)
from constructs import Construct
from ..customs.custom_resources import CustomEnvConstruct


class CdkCloud9CustomEnvConstruct(cdk.NestedStack):

    def __init__(self, scope: Construct, construct_id: str, props: dict = None, vpc: ec2.IVpc = None,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        dirname = os.path.dirname(__file__)

        # The code that defines your stack goes here
        # create a cloud9 ec2 environment in import VPC
        # import Repositories
        repos = []

        if "codecommit_repos" in props.keys() and len(props["codecommit_repos"]) > 0:

            for r in props["codecommit_repos"]:
                repo = codecommit.Repository.from_repository_name(self, f"Repo{r}", repository_name=r)
                repos.append(
                    cloud9.CfnEnvironmentEC2.RepositoryProperty(
                        path_component=repo.repository_name,
                        repository_url=repo.repository_clone_url_http
                    )
                )
        else:
            repos = None

        if props['subnet_type'] == "private":
            subnet_selection = vpc.select_subnets(one_per_az=True, subnet_type=ec2.SubnetType.PRIVATE_WITH_NAT)
        elif props['subnet_type'] == "public":
            subnet_selection = vpc.select_subnets(one_per_az=True, subnet_type=ec2.SubnetType.PUBLIC)

        # Create Environment
        c9env = cloud9.CfnEnvironmentEC2(self, f"Cloud9Env-{props['environment_name']}",
                                         automatic_stop_time_minutes=props['automatic_stop_time_minutes'],

                                         instance_type=props['instance_size'],
                                         name=props['environment_name'],
                                         connection_type='CONNECT_SSM',
                                         # image_id="amazonlinux-2-x86_64",
                                         owner_arn=props["owner_arn"] if "owner_arn" in props else None,

                                         description=props['description'],

                                         subnet_id=subnet_selection.subnet_ids[0],
                                         repositories=repos,
                                         tags=[cdk.CfnTag(
                                             key="EnvironmentName",
                                             value=props['environment_name']

                                         )]

                                         )

        # print the Cloud9 IDE URL in the output
        # CdkStepFunctionCustomEnvConstruct(self, "CSFN", props=props)
        custom=CustomEnvConstruct(self, "CRC9", props=props, c9env=c9env)
        custom.node.add_dependency(c9env)

        # Create outputs
        cdk.CfnOutput(self, "URL", value=c9env.node.id)
        cdk.CfnOutput(self, "Name", value=c9env.name)
