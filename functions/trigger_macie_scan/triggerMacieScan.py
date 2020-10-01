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
import datetime
import os
from botocore.exceptions import ClientError

'''
Perform a sensitive data discovery scan using Amazon Macie based on scheduled
execution of Amazon EventBridge event. 

This proof of concept is used as part of a data pipeline workflow as part of
the data ingestion pipeline. 
'''

def lambda_handler(event, context):
    print(f'REQUEST RECEIVED: {json.dumps(event, default=str)}')

    macie_client = boto3.client('macie2')
    s3_client = boto3.client('s3')
    paginator = s3_client.get_paginator('list_objects_v2')


    acct_id = os.environ['accountId']
    upload_bucket_name = os.environ['rawS3Bucket']
    scan_bucket_name = os.environ['scanS3Bucket']

    date_time = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S%Z")
    keys_found = False

    try:
        print('Getting Event id')
        prefix = event['Input']['id']
    except Exception as e:
        print('Could not retrieve Event id')
        print(e)
        return  

    try:
        # Check if upload bucket contains objects
        page_iterator = paginator.paginate(
            Bucket=upload_bucket_name
        )

        for page in page_iterator:
            # Move objects to scan bucket
            for key_data in page['Contents']:
                keys_found = True

                print(f"Moving object: {key_data['Key']}")
                response = s3_client.copy_object(
                    Bucket = scan_bucket_name,
                    CopySource = {
                        'Bucket': upload_bucket_name,
                        'Key': key_data['Key']
                    },
                    Key = key_data['Key']
                )

                print('Deleting object')
                response = s3_client.delete_object(
                    Bucket=upload_bucket_name,
                    Key = key_data['Key']
                )

                print(f"Tag object post move: {key_data['Key']}")
                response = s3_client.put_object_tagging(
                    Bucket = scan_bucket_name,
                    Key = key_data['Key'],
                    Tagging = {
                        'TagSet': [
                            {
                                'Key': 'WorkflowId',
                                'Value': prefix
                            }
                        ]
                    }
                )
    except Exception as e:
        print('Could not retrieve S3 contents')
        print(e)
        return    

    # Create sensitive data discovery job if upload bucket is not empty
    try:
        if keys_found == True:
            print(f'Scanning bucket {scan_bucket_name} in account {acct_id}')
            response = macie_client.create_classification_job(
                description = 'File upload scan',
                initialRun = True,
                jobType = 'ONE_TIME',
                name = f'PipelineScan-{date_time}',
                s3JobDefinition = {
                    'bucketDefinitions': [{
                        'accountId': acct_id, 
                        'buckets': [scan_bucket_name]
                    }],
                    'scoping': {
                        'includes': {
                            'and': [{
                                'tagScopeTerm': {
                                    'comparator': 'EQ',
                                    'key': 'TAG',
                                    'tagValues': [{
                                            'key': 'WorkflowId',
                                            'value': prefix
                                    }],
                                    'target': 'S3_OBJECT'
                                }
                            }]
                        }
                    }
                }
            )
    except Exception as e:
        print(f'Could not scan bucket {scan_bucket_name}')
        print(e)
        return

    print('Execution complete...')
    return response['jobId']
