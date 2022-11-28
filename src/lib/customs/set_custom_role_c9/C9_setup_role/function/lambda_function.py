from __future__ import print_function
import logging
from time import sleep
from crhelper import CfnResource
import boto3

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
helper = CfnResource(json_logging=True, log_level='DEBUG', boto_level='CRITICAL')

try:
    ec2_client = boto3.client('ec2')
    ssm_client = boto3.client('ssm')
    iam_client = boto3.client('iam')

except Exception as e:
    logger.info(e)


def ssm_ready(instance_id):
    try:
        response = ssm_client.describe_instance_information(Filters=[
            {'Key': 'InstanceIds', 'Values': [instance_id]}
        ])
        logger.debug(response)
        return True
    except ssm_client.exceptions.InvalidInstanceId:
        return False


def set_role(event, context):
    response = ec2_client.describe_instances(Filters=[{
        'Name': 'tag:EnvironmentName', 'Values': [event['ResourceProperties']['StackCloud9Environment']],
        'Name': 'instance-state-name', 'Values': ['running', 'shutting-down', 'stopped', 'stopping', 'pending'],

    }])
    logger.info(response)
    instance_id = response['Reservations'][0]['Instances'][0]['InstanceId']

    describe = ec2_client.describe_iam_instance_profile_associations(
        Filters=[
            {
                'Name': 'instance-id',
                'Values': [
                    instance_id,
                ]
            },
        ],

    )

    association_id = describe['IamInstanceProfileAssociations'][0]['AssociationId']
    if len(association_id) > 0:
        logger.info(association_id)
        remove = ec2_client.disassociate_iam_instance_profile(
            AssociationId=association_id
        )
        logger.info(f"Removing Profile - {remove}")
    else:
        logger.info("no Association Id Found")

    ec2_client.associate_iam_instance_profile(
        IamInstanceProfile={
            # 'Arn': 'string',
            'Name': event['ResourceProperties']['InstanceProfile']
        },
        InstanceId=instance_id
    )
    while not ssm_ready(instance_id):
        if context.get_remaining_time_in_millis() < 20000:
            raise Exception("Timed out waiting for instance to register with SSM")
        sleep(15)


@helper.create
def create(event, context):
    logger.info(event, )
    logger.info("Got Create")
    instance_id = set_role(event=event, context=context)
    return instance_id


@helper.update
@helper.delete
def no_op(_, __):
    return


def handler(event, context):
    logger.info(event)

    helper(event, context)
