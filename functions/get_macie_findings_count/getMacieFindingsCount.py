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
from pip._internal import main

main(['install', '-I', '-q', 'boto3', '--target', '/tmp/', '--no-cache-dir', '--disable-pip-version-check'])
sys.path.insert(0,'/tmp/')
import boto3
import json
import os
from botocore.exceptions import ClientError

'''
Get number of findings from Macie classification job. Tag all objects
and move to the manual review S3 bucket if sensitive data found.
Move files to the scanned data S3 bucket if no sensitive data found. 

This proof of concept is used as part of a data pipeline workflow as part of
the data ingestion pipeline. 
'''

def lambda_handler(event, context):
    print(f'REQUEST RECEIVED: {json.dumps(event, default=str)}')
    
    macie_client = boto3.client('macie2')

    job_id = event['Input']['jobId']['Payload']
    file_keys = set()
    return_info = []

    try:
        print(f'Getting findings from Macie job ({job_id})')
        paginator = macie_client.get_paginator('list_findings')
        
        page_iterator = paginator.paginate(
            findingCriteria = {
                'criterion': {
                    'classificationDetails.jobId': {
                        'eq': [job_id]
                    }
                }
            }
        )
    except Exception as e:
        print(f'Could not get findings from job {job_id}')
        print(e)
        return

    try:
        print('Getting findings details')
        for page in page_iterator:
            findings_list = page['findingIds']
            findings = macie_client.get_findings(findingIds=findings_list)
            for finding in findings['findings']:
                if 's3Object' in finding['resourcesAffected']:
                    file_keys.add(finding['resourcesAffected']['s3Object']['key'])
                    print(finding['resourcesAffected']['s3Object']['key'])
    except Exception as e:
        print('Error reteiving findings details')
        print(e)
        return

    
    return_info = list(file_keys)

    print(f"Return Info: {return_info}")

    print('Execution complete...')
    return return_info
