import aws_cdk as cdk
from aws_cdk import (aws_ec2 as ec2, Stack)
from constructs import Construct


class CdkVPCStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, props: dict = None, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # Create Flow logs Options
        flow_logs_opts = ec2.FlowLogOptions(destination=ec2.FlowLogDestination.to_cloud_watch_logs(),
                                            traffic_type=ec2.FlowLogTrafficType.ALL)

        # Create subnet configurations
        subnet_configuration = []

        # Create a dict for subnets types
        subnet_type = {"public": ec2.SubnetType.PUBLIC,
                       "private": ec2.SubnetType.PRIVATE_WITH_NAT,
                       "isolate": ec2.SubnetType.PRIVATE_ISOLATED
                       }
        for c in props['subnet_configuration']:
            subnet_configuration.append(ec2.SubnetConfiguration(name=c['name'], cidr_mask=c['cidr_mask'],
                                                                subnet_type=subnet_type[c['subnet_type'].lower()]))
        # Creating VPC
        self.vpc = ec2.Vpc(self, "VPC", cidr=props['vpc_cidr'], enable_dns_support=True, enable_dns_hostnames=True,
                           flow_logs=dict(flow_logs=flow_logs_opts), max_azs=props['max_azs'],
                           nat_gateways=props['nat_gateways'],
                           subnet_configuration=subnet_configuration,
                           )

        # Add Gateway Endpoint
        self.vpc.add_gateway_endpoint("S3GwEndpoint", service=ec2.GatewayVpcEndpointAwsService.S3)
        # Add Interface Endpoints
        #self.vpc.add_interface_endpoint("CwlogsEndpoint", private_dns_enabled=True,
         #                               subnets=ec2.SubnetSelection(one_per_az=True, subnet_group_name="ides"),
          #                              service=ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS)

        # self.vpc.add_interface_endpoint("ECREndpoint",subnets= ec2.SubnetSelection(one_per_az=True,subnet_group_name="ides"),
        #                              service= ec2.InterfaceVpcEndpointAwsService.ECR )
        # self.vpc.add_interface_endpoint("ECREndpointDocker",subnets= ec2.SubnetSelection(one_per_az=True,subnet_group_name="ides"),
        #                               service= ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER )
        # Create Outputs
        cdk.CfnOutput(self, id=f"VPCID",
                      value=self.vpc.vpc_id,
                      description=f"VPC ID")
