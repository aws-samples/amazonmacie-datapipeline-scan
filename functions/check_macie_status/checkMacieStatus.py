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
Check status of Macie classification job. 

This proof of concept is used as part of a data pipeline workflow as part of
the data ingestion pipeline. 
'''

macie_client = boto3.client('macie2')

def lambda_handler(event, context):
    print(f'REQUEST RECEIVED: {json.dumps(event, default=str)}')

    job_id = event['Input']['jobId']['Payload']

    if job_id == 'NoKeysFound':
        return 'NoKeysFound'
    else:
        try:
            print(f'Checking Macie job ({job_id}) status')
            response = macie_client.describe_classification_job(jobId = job_id)
        except Exception as e:
            print(f'Could not get status of jobId {job_id}')
            print(e)
            return

    print('Execution complete...')
    return response['jobStatus']
