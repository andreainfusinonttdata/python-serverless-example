#!/usr/bin/env python3
import os

import aws_cdk as cdk

from atm_exercise.atm_exercise_stack import ATMLambdaExerciseStack


environment = "test"

app = cdk.App()
ATMLambdaExerciseStack(app, f"ATMLambdaExerciseStack", environment,
    # If you don't specify 'env', this stack will be environment-agnostic.
    # Account/Region-dependent features and context lookups will not work,
    # but a single synthesized template can be deployed anywhere.

    # Uncomment the next line to specialize this stack for the AWS Account
    # and Region that are implied by the current CLI configuration.

    #env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),

    # Uncomment the next line if you know exactly what Account and Region you
    # want to deploy the stack to. */

    env=cdk.Environment(account='905075344790', region='eu-west-1'),

    # For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html
    )

app.synth()
