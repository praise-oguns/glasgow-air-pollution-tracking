# ============================================================
# GLASGOW AIR QUALITY PROJECT — reader_function.py
#
# This is a separate Lambda function that reads the latest
# air quality result from DynamoDB and returns it as JSON.
# The website calls this via API Gateway to get live data.
# ============================================================

import boto3
import json
from datetime import datetime, timezone
from decimal import Decimal


def decimal_to_float(obj):
    """DynamoDB stores numbers as Decimal — convert back to float for JSON."""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


def lambda_handler(event, context):
    """Reads today's air quality reading from DynamoDB and returns it."""
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table    = dynamodb.Table("glasgow-air-quality")

    # Get today's date — this matches the partition key we save in the main Lambda
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    response = table.get_item(Key={"date": today})
    item     = response.get("Item")  # returns None if no reading exists for today yet

    if not item:
        return {
            "statusCode": 404,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"error": "No data for today yet"})
        }

    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*"
            # This header allows the website to call this API from the browser
            # Without it the browser blocks the request for security reasons
        },
        "body": json.dumps(item, default=decimal_to_float)
    }