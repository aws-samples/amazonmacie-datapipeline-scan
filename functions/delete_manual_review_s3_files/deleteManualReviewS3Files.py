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
import os
from botocore.exceptions import ClientError

'''
Delete files from S3 manual review bucket.

This proof of concept is used as part of a data pipeline workflow as part of
the data ingestion pipeline. 
'''

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    print(f'REQUEST RECEIVED: {json.dumps(event, default=str)}')

    src_bucket_name = os.environ['sourceS3Bucket']
    s3_key_names = event['Input']['macieFindingsInfo']['Payload']

    try:
        for s3_key_name in s3_key_names:
            print(f'Deleting object: {s3_key_name}')
            response = s3_client.delete_object(
                Bucket=src_bucket_name,
                Key = s3_key_name
            )
    except Exception as e:
        print(f'Could not delete S3 object')
        print(e)
        return

    print('Execution complete...')
    return 

