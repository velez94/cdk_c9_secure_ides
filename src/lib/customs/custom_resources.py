import os

# For consistency with other languages, `cdk` is the preferred import name for
# the CDK's src module.  The following line also imports it as `src` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.
import aws_cdk as cdk
from aws_cdk import (
    CustomResource,
    aws_lambda as _lambda,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as sfn_task,
    aws_iam as iam,
    aws_cloud9 as cloud9,
    aws_logs as logs)
from constructs import Construct


class CustomEnvConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str, props: dict = None, c9env: cloud9.CfnEnvironmentEC2 = None,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        dirname = os.path.dirname(__file__)

        # Create policies for lambda Role
        st = iam.PolicyStatement(actions=[
            "cloudformation:DescribeStackResources",
            "ec2:AssociateIamInstanceProfile",
            "ec2:DisassociateIamInstanceProfile",
            "ec2:AssociateIamInstanceProfile",
            "ec2:ReplaceIamInstanceProfileAssociation",
            "ec2:AuthorizeSecurityGroupIngress",
            "ec2:DescribeInstances",
            "ec2:DescribeInstanceStatus",
            "ec2:DescribeInstanceAttribute",
            "ec2:DescribeIamInstanceProfileAssociations",
            "ec2:DescribeVolumes",
            "ec2:DesctibeVolumeAttribute",
            "ec2:DescribeVolumesModifications",
            "ec2:DescribeVolumeStatus",
            "ec2:StartInstances",
            "ec2:StopInstances",
            "ssm:DescribeInstanceInformation",
            "ec2:ModifyVolume",
            "ec2:ReplaceIamInstanceProfileAssociation",
            "ec2:ReportInstanceStatus",
            "ssm:SendCommand",
            "ssm:GetCommandInvocation",
            "s3:GetObject",

        ],
            resources=["*"],
            effect=iam.Effect.ALLOW)

        st3 = iam.PolicyStatement(actions=['lambda:AddPermission',
                                           'lambda:RemovePermission'],
                                  resources=['*'],
                                  effect=iam.Effect.ALLOW)
        st4 = iam.PolicyStatement(actions=[
            'events:PutRule',
            'events:DeleteRule',
            'events:PutTargets',
            'events:RemoveTargets',
        ],
            resources=['*'], effect=iam.Effect.ALLOW
        )

        lambda_role = iam.Role(self, "LambdaCloud9Role", role_name=f"LambdaCloud9Role-{props['environment_name']}",
                               assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),

                               )
        lambda_role.add_to_policy(st)
        #
        lambda_role.add_to_policy(st3)
        lambda_role.add_to_policy(st4)
        lambda_role.add_managed_policy(
            iam.ManagedPolicy.from_managed_policy_arn(self,
                                                      id="lambdaPol",
                                                      managed_policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole")
        )

        # Extend permissions for custom resource
        st_p1 = iam.PolicyStatement(actions=[
            "events:ListRules",
            "events:RemovePermission",
            "events:PutPermission",
            "events:PutRule",
            "events:PutTargets",
            "events:RemoveTargets",
            "events:DeleteRule"
        ],
            resources=['*'],
            effect=iam.Effect.ALLOW
        )
        st_p2 = iam.PolicyStatement(actions=[
            "lambda:AddPermission",
            "lambda:RemovePermission",
            "lambda:GetFunction"
        ],
            resources=['*'],
            effect=iam.Effect.ALLOW
        )
        lambda_role.add_to_policy(st_p2)
        lambda_role.add_to_policy(st_p1)
        # Create Instance profile name

        c9_role = iam.Role(self, f"Cloud9Role-{props['environment_name']}",
                           role_name=f"Cloud9Role-{props['environment_name']}",
                           description=f"Role for {props['environment_name']}", path="/service-role/",
                           assumed_by=iam.ServicePrincipal(service="ec2.amazonaws.com",
                                                           ),
                           managed_policies=[
                               iam.ManagedPolicy.from_managed_policy_arn(self,
                                                                         id="CorePol",
                                                                         managed_policy_arn="arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore")
                           ]

                           )

        c9_role.grant_assume_role(iam.ServicePrincipal("cloud9.amazonaws.com"))

        st2 = iam.PolicyStatement(actions=["iam:PassRole"],
                                  resources=[c9_role.role_arn],
                                  effect=iam.Effect.ALLOW)
        lambda_role.add_to_policy(st2)
        c9_instance_profile = iam.CfnInstanceProfile(self, f"Cloud9InstanceProfile-{props['environment_name']}",
                                                     instance_profile_name=f"C9InstanceProfile-{props['environment_name']}",
                                                     path="/cloud9/",
                                                     roles=[c9_role.role_name])

        setup_role = _lambda.Function(self, f'C9SetupRoleLambda',
                                      runtime=_lambda.Runtime.PYTHON_3_8,
                                      code=_lambda.Code.from_asset(
                                          os.path.join(dirname, "set_custom_role_c9/C9_setup_role/function")),
                                      handler='lambda_function.handler',
                                      function_name=f"C9InstanceRole-{props['environment_name']}",
                                      timeout=cdk.Duration.seconds(120),
                                      role=lambda_role,
                                      log_retention=logs.RetentionDays.TWO_WEEKS

                                      )
        c1 = CustomResource(self, f"Setup-Role-{props['environment_name']}", service_token=setup_role.function_arn,
                            properties=dict(StackCloud9Environment=props["environment_name"],
                                            InstanceProfile=c9_instance_profile.instance_profile_name))

        # Create resize Disk Function
        if props["resize_volume"] == "True":
            resize_disk = _lambda.Function(self, f'ResizeDiskLambda',
                                           runtime=_lambda.Runtime.PYTHON_3_8,
                                           code=_lambda.Code.from_asset(
                                               os.path.join(dirname, "resize_disk_function/resize_disk/function")),
                                           handler='lambda_function.handler',
                                           function_name=f"ResizeDiskLambda-{props['environment_name']}",
                                           timeout=cdk.Duration.seconds(600),
                                           role=lambda_role,
                                           log_retention=logs.RetentionDays.TWO_WEEKS

                                           )
            resize_disk.node.add_dependency(lambda_role)

            c2 = CustomResource(self, f"Resize-Disk-{props['environment_name']}",
                                service_token=resize_disk.function_arn,
                                properties=dict(EBSVolumeSize=props["ebs_volume_size"],
                                                StackCloud9Environment=props["environment_name"],
                                                InstanceId=c1.ref,
                                                Region=cdk.Aws.REGION),
                                )
            c2.node.add_dependency(c1)
        # Create lambda to setup Role

        # Bootstrapping Function
        if props["bootstrap_environment"] == "True":
            boots_env = _lambda.Function(self, f"BootStrapEnv-{props['environment_name']}",
                                         runtime=_lambda.Runtime.PYTHON_3_8,
                                         code=_lambda.Code.from_asset(
                                             os.path.join(dirname, "bootstrap_env_function/bootstrap_env/function")),
                                         handler='lambda_function.handler',
                                         function_name=f"BootStrapEnv-{props['environment_name']}",
                                         timeout=cdk.Duration.seconds(900),
                                         role=lambda_role,
                                         log_retention=logs.RetentionDays.TWO_WEEKS

                                         )

            boots_env.node.add_dependency(resize_disk)

            c3 = CustomResource(self, f"Bootstrap-{props['environment_name']}", service_token=boots_env.function_arn,
                                properties=dict(StackCloud9Environment=props["environment_name"],
                                                BootstrapArguments=props["bootstrap_commands"],
                                                ),
                                )
            c3.node.add_dependency(c2)
