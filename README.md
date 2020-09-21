## Use Macie to discover sensitive data as part of  automated data pipelines

This solution will integrate  Amazon Macie (https://aws.amazon.com/macie/) as part of the data ingestion step in your data pipeline. Amazon Macie is a fully managed data security and privacy service that uses machine learning and pattern matching to discover sensitive data in AWS. 

If sensitive data is discovered by Amazon Macie, the solution triggers a manual review step notifying an administrator to review the data and decide whether to allow the data pipeline to continue ingesting the objects. If allowed, the objects will be tagged with an Amazon S3 object tag (https://docs.aws.amazon.com/AmazonS3/latest/dev/object-tagging.html) to identify that sensitive data was found in the object prior to progressing to the next stage of the pipeline.

This helps reduce the risk that sensitive data, such as personally identifiable information, will be inadvertently ingested into a data lake using automation and manual review, where required. This solution can be extended to use custom identifiers to expand your sensitive data discovery (https://aws.amazon.com/blogs/security/discover-sensitive-data-by-using-custom-data-identifiers-with-amazon-macie/), take additional automated action, or add additional validation steps as part of the ingestion phase, and use.

## Solution overview

Many of my customers are building a serverless data lake (https://aws.amazon.com/blogs/big-data/build-and-automate-a-serverless-data-lake-using-an-aws-glue-trigger-for-the-data-catalog-and-etl-jobs/) with Amazon Simple Storage Service (Amazon S3) (https://aws.amazon.com/s3/) as the primary data store. When building pipelines for their data lakes, customers commonly use several Amazon S3 buckets to represent different stages of their pipeline. I will refer to the Amazon S3 bucket for the first stage of ingestion as the raw data bucket. For example, some customers may create separate raw data, curated data, and processed data buckets. 

This solution will add additional validation steps to the pipeline on the raw data Amazon S3 bucket. However, you can customize this solution to perform the sensitive data discovery scan during any stage of the pipeline. As the majority of customers do their extract, transform, and load (ETL) daily, this solution will perform the sensitive data discovery scan on a scheduled (every 60 minute) basis prior to any crawler jobs for cataloguing the data. 

### Solution components

The following resources are created as part of the solution:

* Identity and Access Management (IAM) managed policies (https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_managed-vs-inline.html) to grant necessary permissions for the AWS Lambda functions to access AWS resources part of this solution
* Amazon Simple Storage Service (Amazon S3) buckets (https://docs.aws.amazon.com/AmazonS3/latest/dev/UsingBucket.html) to serve as the raw data bucket for uploading objects for the data pipeline, scan stage for objects to perform the sensitive data scan on, manual review bucket for objects where sensitive data was discovered, and a scanned data bucket for triggering the next ingestion step of the data pipeline
* AWS Lambda functions (https://docs.aws.amazon.com/lambda/latest/dg/welcome.html) to provide loosely coupled components used to execute the sensitive data scan logic and workflow
* AWS Step Functions Standard Workflow (https://docs.aws.amazon.com/step-functions/latest/dg/concepts-standard-vs-express.html) to orchestrate the AWS Lambda functions for the business logic
* Amazon Macie sensitive data discovery jobs (https://docs.aws.amazon.com/macie/latest/user/discovery-jobs.html) to scan the scan stage Amazon S3 bucket for sensitive data 
* Amazon EventBridge rule (https://docs.aws.amazon.com/eventbridge/latest/userguide/create-eventbridge-scheduled-rule.html) to start the AWS Step Function workflow execution on a recurring schedule
* Amazon Simple Notification Service (SNS) Topic (https://docs.aws.amazon.com/sns/latest/dg/sns-tutorial-create-topic.html) to send notification to review sensitive data discovered in the pipeline
* Amazon API Gateway REST API with two resources (https://docs.aws.amazon.com/apigateway/latest/developerguide/how-to-create-api.html) to receive the decision of the sensitive data reviewer as part of a manual workflow

*Important:* the application uses various AWS services, and there are costs associated with these resources after the Free Tier usage. Please see the AWS pricing page (https://aws.amazon.com/pricing/) for details.

The solution architecture is shown below.
![Architecture Diagram](https://github.com/aws-samples/amazonmacie-datapipeline-scan/blob/master/Macie%20Data%20Pipeline.png)

### Solution logic

1. Objects are uploaded to raw data Amazon S3 bucket as part of data ingestion process.
2. Scheduled Amazon EventBridge rule executes the Sensitive Data Scan AWS Step Function workflow.
3. triggerMacieScan AWS Lambda function moves objects from the raw data Amazon S3 bucket to the scan stage Amazon S3 bucket.
4. triggerMacieScan AWS Lambda function creates an Amazon Macie sensitive data discovery job on the  scan stage Amazon S3 bucket.
5. checkMacieStatus AWS Lambda function checks the status of the Amazon Macie sensitive data discovery job.
6. isMacieSTatusCompleteChoice AWS Step Function Choice Rule checks whether the Amazon Macie sensitive data discovery job is complete.
    1. If yes, execute the getMacieFindingsCount AWS Lambda function.
    2. If no, the AWS Step Function will wait 60 seconds and restarts step 6.
7. getMacieFindingsCount AWS Lambda function enumerates all of the findings from the Amazon Macie sensitive data discovery job.
8. isSensitiveDataFound AWS Step Function Choice Rule checks whether sensitive data was found in the Amazon Macie sensitive data discovery job.
    1. If there was sensitive data discovered, execute the triggerManualApproval AWS Lambda function.
    2. If there was no sensitive data discovered, execute the moveAllScanStageS3Files AWS Lambda function.
9. moveAllScanStageS3Files AWS Lambda function moves all of the objects from the scan stage Amazon S3 bucket to the data scanned Amazon S3 bucket.
10. triggerManualApproval AWS Lambda function tags and moves objects them with sensitive data discovered to the manual review Amazon S3 bucket, and moves objects with no sensitive data discovered to the data scanned Amazon S3 bucket. The function then sends a notification to the ApprovalRequestNotification Amazon SNS Topic as a notification that manual review is required.
11. Email is sent to the email subscribed to the ApprovalRequestNotification Amazon SNS Topic (from the solution deployment template) for the manual review user with the option to ‘Approve’ or ‘Deny’ pipeline ingestion for these objects.
12. Manual review user assesses the objects with sensitive data in the manual review Amazon S3 bucket and selects the ‘Approve’ or ‘Deny’ links in the email.
13. The decision decision request is proxied from the Amazon API Gateway to the receiveApprovalDecision AWS Lambda function.
14. manualApprovalChoice AWS Step Function Choice Rule checks the decision from the manual review user.
    1. If denied, execute the deleteManualReviewS3Files AWS Lambda function.
    2. If approved, execute the moveToScannedDataS3Files AWS Lambda function.
15. deleteManualReviewS3Files AWS Lambda function deletes the objects from the manual review Amazon S3 bucket.
16. moveToScannedDataS3Files AWS Lambda function moves the objects from the manual review Amazon S3 bucket to the data scanned Amazon S3 bucket.
17. The next step of the automated data pipeline will begin with the objects in the data scanned Amazon S3 bucket


## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

