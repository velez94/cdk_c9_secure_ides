from __future__ import print_function
import logging
from time import sleep
import boto3

from crhelper import CfnResource

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
helper = CfnResource(json_logging=True, log_level='DEBUG', boto_level='CRITICAL')

try:
    ssm_client = boto3.client('ssm')
    ec2_client = boto3.client('ec2')
except Exception as e:
    logger.info(e)


def get_command_output(instance_id, command_id):
    response = ssm_client.get_command_invocation(CommandId=command_id, InstanceId=instance_id)
    if response['Status'] in ['Failed', 'Canceled', 'Undeliverable', 'Terminated', 'Success']:
        logger.debug(f"The  run command's status is {response['Status']}")
        return response
    return response


def send_command(instance_id, commands):
    logger.debug("Sending command to %s : %s" % (instance_id, commands))
    try:
        return ssm_client.send_command(InstanceIds=[instance_id], DocumentName='AWS-RunShellScript',
                                       Parameters={'commands': commands})
    except ssm_client.exceptions.InvalidInstanceId:
        logger.debug("Failed to execute SSM command", exc_info=True)
        return


def stop_instance(instance_id):
    logger.debug("Stop instance %s" % (instance_id))
    try:
        return ec2_client.stop_instances(InstanceIds=[instance_id, ])
    except:
        logger.debug("Failed to stop instance", exc_info=True)
        return


def start_instance(instance_id):
    logger.debug("Status instance %s" % (instance_id))
    retry = 0
    while True:
        logger.debug("Test %s stopped instaNce" % (retry))
        instance = \
            ec2_client.describe_instances(Filters=[{'Name': 'instance-id', 'Values': [instance_id]}])['Reservations'][
                0][
                'Instances'][0]
        if instance['State']['Name'] in ['stopped']:
            try:
                logger.debug("Instance %s stopped, start it.." % (instance_id))
                ec2_client.start_instances(InstanceIds=[instance_id, ])
                break
            except:
                logger.debug("Failed to start instance", exc_info=True)
                return
        else:
            retry += 1
            if retry >= 20:
                logger.debug("Too many attempts to restart instance %s" % (instance_id))
                break
            sleep(15)

    retry = 0
    while True:
        logger.debug("Test %s running instance" % (retry))
        instance = \
            ec2_client.describe_instances(Filters=[{'Name': 'instance-id', 'Values': [instance_id]}])['Reservations'][
                0][
                'Instances'][0]
        if instance['State']['Name'] in ['running']:
            try:
                logger.debug("Instance %s running.." % (instance_id))
                break
            except:
                logger.debug("Failed to detect instance status", exc_info=True)
                return
        else:
            retry += 1
            if retry >= 20:
                logger.debug("Too many attempts to detect instance status %s" % (instance_id))
                break
            sleep(15)


def get_instance_id(event):
    response = ec2_client.describe_instances(Filters=[{
        'Name': 'tag:EnvironmentName', 'Values': [event['ResourceProperties']['StackCloud9Environment']],
        #'Name': 'instance-state-name', 'Values': ['running', 'shutting-down', 'stopped', 'stopping', 'pending'],

    }])
    logger.info(response)
    instance_id = response['Reservations'][0]['Instances'][0]['InstanceId']
    return instance_id


@helper.create
def create(event, context):
    logger.debug("Creating... ")
    logger.info(event)
    instance_id = get_instance_id(event)

    # bootstrap_path = event['ResourceProperties']['BootstrapPath']
    arguments = event['ResourceProperties']['BootstrapArguments']
    while True:
        commands = arguments
        send_response = send_command(instance_id, commands)
        if send_response:
            command_id = send_response['Command']['CommandId']
            # Get response before restart instance
            #update helper Data
            helper.Data.update({"CommandId": command_id})

            break
        if context.get_remaining_time_in_millis() < 20000:
            raise Exception("Timed out attempting to send command to SSM")
        sleep(30)

    instance_id = get_instance_id(event)
    while True:
        try:
            sleep(60)
            cmd_output_response = get_command_output(instance_id, command_id)
            logger.info(f"Got cmd output {cmd_output_response}")
            if cmd_output_response:
                logger.info("Restarting Instance! ... ")
                stop_instance(instance_id)
                start_instance(instance_id)
                break
        except ssm_client.exceptions.InvocationDoesNotExist:
            logger.debug('Invocation not available in SSM yet', exc_info=True)
        if context.get_remaining_time_in_millis() < 20000:
            return
        sleep(15)

    if cmd_output_response['StandardErrorContent']:
        # raise Exception("ssm command failed: " + cmd_output_response['StandardErrorContent'][:235])
        logger.info(cmd_output_response['StandardErrorContent'][:235])

    return instance_id


@helper.poll_create
def poll_create(event, context):
    logger.info("Got create poll")
    instance_id = get_instance_id(event)
    while True:
        try:
            sleep(60)
            cmd_output_response = get_command_output(instance_id, helper.Data.get("CommandId"))
            if cmd_output_response:
                break
        except ssm_client.exceptions.InvocationDoesNotExist:
            logger.debug('Invocation not available in SSM yet', exc_info=True)
        if context.get_remaining_time_in_millis() < 20000:
            return
        sleep(15)
    if cmd_output_response["Status"]== 'Success':
        logging.info(cmd_output_response)
    elif cmd_output_response['StandardErrorContent'] and cmd_output_response['Status'] in ['Failed', 'Canceled', 'Undeliverable', 'Terminated']:
        raise Exception("ssm command failed: " + cmd_output_response['StandardErrorContent'][:235])
    return instance_id


@helper.update
@helper.delete
def no_op(_, __):
    return


def handler(event, context):
    helper(event, context)
