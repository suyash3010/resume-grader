from aws_lambda_powertools.utilities.data_classes.api_gateway_event import APIGatewayProxyEvent
from aws_lambda_powertools.utilities.data_classes.common import BaseProxyEvent
from aws_lambda_powertools.utilities.typing import LambdaContext
from awsgi import response
import app

def lambda_handler(event: dict, context: LambdaContext) -> dict:
    """AWS Lambda entry point for the Flask application."""
    return response(app.app, event, context)
