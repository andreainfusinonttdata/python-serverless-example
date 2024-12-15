from aws_cdk import (
    aws_lambda as _lambda,
    aws_sqs as sqs,
    aws_sns as sns,
    aws_apigateway as apigateway,
    aws_dynamodb as dynamodb,
    aws_lambda_event_sources
)
import aws_cdk as core
from constructs import Construct


class ATMLambdaExerciseStack(core.Stack):

    def __init__(self, scope: Construct, id: str, environment: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Creating DynamoDB Table
        customers_balance_table = dynamodb.Table(self, "CustomersBalance",
                                                 partition_key=dynamodb.Attribute(name="client_id",
                                                                                  type=dynamodb.AttributeType.STRING),
                                                 billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
                                                 table_name=f"customer-balance-{environment}"
                                                 )

        # Creating SQS Queue
        process_requests_queue = sqs.Queue(self, "ProcessRequestsQueue",
                                           queue_name=f"process-requests-queue-{environment}")

        # Creating SNS Topic
        operation_result_topic = sns.Topic(self, "OperationResultSNS",
                                           topic_name=f"operation-result-{environment}")

        # Lambda Functions
        read_balance_lambda = _lambda.Function(self, "ReadBalanceLambda",
                                               runtime=_lambda.Runtime.PYTHON_3_11,
                                               handler="read_balance.handler",
                                               code=_lambda.Code.from_asset("lambda/read_balance"),
                                               environment={
                                                   "CUSTOMERS_BALANCE_TABLE": customers_balance_table.table_name
                                               },
                                               function_name=f"read-balance-{environment}"
                                               )
        customers_balance_table.grant_read_data(read_balance_lambda)

        deposit_lambda = _lambda.Function(self, "DepositLambda",
                                          runtime=_lambda.Runtime.PYTHON_3_11,
                                          handler="deposit.handler",
                                          code=_lambda.Code.from_asset("lambda/deposit"),
                                          environment={
                                              "PROCESS_REQUESTS_QUEUE_URL": process_requests_queue.queue_url
                                          },
                                          function_name=f"deposit-balance-{environment}"
                                          )
        process_requests_queue.grant_send_messages(deposit_lambda)

        withdraw_lambda = _lambda.Function(self, "WithdrawLambda",
                                           runtime=_lambda.Runtime.PYTHON_3_11,
                                           handler="withdraw.handler",
                                           code=_lambda.Code.from_asset("lambda/withdraw"),
                                           environment={
                                               "PROCESS_REQUESTS_QUEUE_URL": process_requests_queue.queue_url
                                           },
                                           function_name=f"withdraw-balance-{environment}"
                                           )
        process_requests_queue.grant_send_messages(withdraw_lambda)

        process_requests_lambda = _lambda.Function(self, "ProcessRequestsLambda",
                                                   runtime=_lambda.Runtime.PYTHON_3_11,
                                                   handler="process_requests.handler",
                                                   code=_lambda.Code.from_asset("lambda/process_requests"),
                                                   environment={
                                                       "CUSTOMERS_BALANCE_TABLE": customers_balance_table.table_name,
                                                       "OPERATION_RESULT_TOPIC": operation_result_topic.topic_arn
                                                   },
                                                   function_name=f"process-requests-{environment}",
                                                   layers=[_lambda.LayerVersion.from_layer_version_arn(
                                                       self,
                                                       "AWSLambdaPowertoolsPythonV2",
                                                       "arn:aws:lambda:eu-west-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:78"
                                                   )]
                                                   )

        # Grant permissions
        process_requests_queue.grant_consume_messages(process_requests_lambda)
        source = aws_lambda_event_sources.SqsEventSource(queue=process_requests_queue, report_batch_item_failures=True)
        process_requests_lambda.add_event_source(source)

        customers_balance_table.grant_read_write_data(process_requests_lambda)
        operation_result_topic.grant_publish(process_requests_lambda)

        # Create API Gateway
        api = apigateway.RestApi(self, "ATMExerciseAPI", rest_api_name=f"api-wateway-{environment}")

        read_integration = apigateway.LambdaIntegration(read_balance_lambda)
        deposit_integration = apigateway.LambdaIntegration(deposit_lambda)
        withdraw_integration = apigateway.LambdaIntegration(withdraw_lambda)

        api.root.add_resource("read").add_method("GET", read_integration)
        api.root.add_resource("deposit").add_method("POST", deposit_integration)
        api.root.add_resource("withdraw").add_method("POST", withdraw_integration)
