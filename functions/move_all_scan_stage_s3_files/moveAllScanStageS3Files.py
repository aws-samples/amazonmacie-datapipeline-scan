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
Move all files from scan stage bucket to the scanned data bucket. This function 
is called when there are no sensitive data discovery findings from the Macie
job.

This proof of concept is used as part of a data pipeline workflow as part of
the data ingestion pipeline. 
'''

def lambda_handler(event, context):
    print(f'REQUEST RECEIVED: {json.dumps(event, default=str)}')

    target_bucket_name = os.environ['targetS3Bucket']
    src_bucket_name = os.environ['sourceS3Bucket']

    s3_client = boto3.client('s3')
    
    prefix = event['Input']['id']
    check_key = ''

    try:
        print('Moving files without sensitive data')
        paginator = s3_client.get_paginator('list_objects_v2')
        
        page_iterator = paginator.paginate(
            Bucket=src_bucket_name)
        for page in page_iterator:
            if ('Contents' in page):
                s3_keys_remaining = page['Contents']
            else:
                s3_keys_remaining = []
                
            for s3_key_info in s3_keys_remaining:
                print(f"Checking for tag on: {s3_key_info['Key']}")
                object_tags = s3_client.get_object_tagging(
                    Bucket=src_bucket_name,
                    Key=s3_key_info['Key']
                )
                for tag_set in object_tags['TagSet']:
                    if tag_set['Key'] == 'WorkflowId':
                        check_key = tag_set['Value']
                if check_key == prefix:
                    print(f"Moving: {s3_key_info['Key']}")
                    response = s3_client.copy_object(
                        Bucket = target_bucket_name,
                        CopySource = {
                            'Bucket': src_bucket_name,
                            'Key': s3_key_info['Key']
                        },
                        Key = s3_key_info['Key']
                    )
                    print('Deleting object')
                    response = s3_client.delete_object(
                        Bucket=src_bucket_name,
                        Key = s3_key_info['Key']
                    )
                else:
                    print(f"Object tag not matching for {s3_key_info['Key']}")

    except Exception as e:
        print(f'Could not complete S3 object move')
        print(e)
        return

    print('Execution complete...')
    return 

