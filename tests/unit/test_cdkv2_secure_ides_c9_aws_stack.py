import aws_cdk as core
import aws_cdk.assertions as assertions

from cdkv2_secure_ides_c9_aws.cdkv2_secure_ides_c9_aws_stack import Cdkv2SecureIdesC9AwsStack

# example tests. To run these tests, uncomment this file along with the example
# resource in src/cdkv2_secure_ides_c9_aws_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = Cdkv2SecureIdesC9AwsStack(app, "cdkv2-secure-ides-c9-aws")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
