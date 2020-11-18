# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import sys
import boto3
import json
from botocore.exceptions import ClientError

'''
Get number of findings from Macie classification job. 

This proof of concept is used as part of a data pipeline workflow as part of
the data ingestion pipeline. 
'''

step_function_client = boto3.client('stepfunctions')

def lambda_handler(event, context):    
    if event['requestContext']['resourcePath'] == '/allow':
        next_action = 'allow'
    else:
        next_action = 'delete'

    task_token = event['queryStringParameters']['token']
    task_token_clean = task_token.replace(" ", "+")

    try:
        response = step_function_client.send_task_success(
            taskToken = task_token_clean,
            output = f'{{"action": "{next_action}"}}'
        )
    except Exception as e:
        print(f'Could not send task success with token {task_token_clean}')
        print(e)
        return

    return {
        'statusCode': 200,
        'body': json.dumps({'action': next_action}),
        'headers': {
            'Content-Type': 'application/json'
        }
    }
    