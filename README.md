## Use Macie to discover sensitive data as part of  automated data pipelines

This solution will integrate [Amazon Macie](https://aws.amazon.com/macie/) as part of the data ingestion step in your data pipeline. Amazon Macie is a fully managed data security and privacy service that uses machine learning and pattern matching to discover sensitive data in AWS. 

When Macie discovers sensitive data, the solution notifies an administrator to review the data and decide whether to allow the data pipeline to continue ingesting the objects. If allowed, the objects will be tagged with an Amazon Simple Storage Service (Amazon S3) object tag to identify that sensitive data was found in the object before progressing to the next stage of the pipeline.

This combination of automation and manual review helps reduce the risk that sensitive data—such as personally identifiable information—will be ingested into a data lake. This solution can be extended to fit your use case and workflows. For example, you can define custom data identifiers as part of your scans, add additional validation steps, create Macie suppression rules to archive findings automatically, or only request manual approvals for findings that meet certain criteria (such as high severity findings).

## Solution overview

Many of my customers are [building serverless data lakes](https://aws.amazon.com/blogs/big-data/build-and-automate-a-serverless-data-lake-using-an-aws-glue-trigger-for-the-data-catalog-and-etl-jobs/) with Amazon S3 as the primary data store. Their data pipelines commonly use different S3 buckets each stage of the pipeline. I refer to the S3 bucket for the first stage of ingestion as the raw data bucket. A typical pipeline might have [separate buckets for raw, curated, and processed data](https://aws.amazon.com/blogs/big-data/aws-serverless-data-analytics-pipeline-reference-architecture/) representing different stages as part of their data analytics pipeline.

Typically, customers will perform validate and clean their data before moving it to a raw data zone. This solution adds validation steps to that pipeline after preliminary quality checks and data cleaning is performed, noted in blue (in layer 3) of Figure 1. The layers outlined in the pipeline are:

1. **Ingestion** – Responsible for bringing data into the data lake.
1. Storage – Responsible for providing durable, scalable, and secure components to store the data—typically using S3 buckets.
1. Processing – Responsible for transforming data into a consumable state through data validation, cleanup, normalization, transformation, and enrichment. This processing layer is where the additional validation steps are added to identify instances of sensitive data that haven’t been appropriately redacted or tokenized prior to consumption.
1. **Consumption** – Responsible for providing tools to gain insights from the data in the data lake.

![Data pipeline with sensitive data scan](https://github.com/aws-samples/amazonmacie-datapipeline-scan/blob/master/images/macie-data-pipeline.png)

The application runs on a scheduled basis (four times a day, every 6 hours by default) to process data that is added to the raw data S3 bucket. You can customize the application to perform a sensitive data discovery scan during any stage of the pipeline. Because most customers do their extract, transform, and load (ETL) daily, the application scans for sensitive data on a scheduled basis before any crawler jobs run to catalog the data and after typical validation and data redaction or tokenization processes complete.

You can expect that this additional validation will add 5–10 minutes to your pipeline execution at a minimum. The validation processing time will scale linearly based on object size, but there is a start-up time per job that is constant.

If sensitive data is found in the objects, an email is sent to the designated administrator requesting an approval decision, which they indicate by selecting the link corresponding to their decision to approve or deny the next step. In most cases, the reviewer will choose to adjust the sensitive data cleanup processes to remove the sensitive data, deny the progression of the files, and re-ingest the files in the pipeline.

### Application components

The following resources are created as part of the solution:

* Identity and Access Management (IAM) managed policies grant the necessary permissions for the AWS Lambda functions to access AWS resources that are part of the application.
* S3 buckets store data in various stages of processing: A raw data bucket for uploading objects for the data pipeline, a scanning bucket where objects are scanned for sensitive data, a manual review bucket holding objects where sensitive data was discovered, and a scanned data bucket for starting the next ingestion step of the data pipeline.
* Lambda functions execute the logic to run the sensitive data scans and workflow.
* AWS Step Functions Standard Workflows orchestrate the Lambda functions for the business logic.
* Amazon Macie sensitive data discovery jobs scan the scanning stage S3 bucket for sensitive data.
* An Amazon EventBridge rule starts the Step Functions workflow execution on a recurring schedule.
* Amazon Simple Notification Service (Amazon SNS) topic sends notifications to review sensitive data discovered in the pipeline.
* Amazon API Gateway REST API with two resources receives the decisions of the sensitive data reviewer as part of a manual workflow.

The solution architecture is shown below.
![Application architecture and logic](https://github.com/aws-samples/amazonmacie-datapipeline-scan/blob/master/images/macie-data-pipeline.png)

### Application logic


1. Objects are uploaded to the raw data S3 bucket as part of the data ingestion process.
1. A scheduled EventBridge rule runs the sensitive data scan Step Functions workflow.
1. `triggerMacieScan` Lambda function moves objects from the raw data S3 bucket to the scan stage S3 bucket.
1. `triggerMacieScan` Lambda function creates a Macie sensitive data discovery job on the scan stage S3 bucket.
1. `checkMacieStatus` Lambda function checks the status of the Macie sensitive data discovery job.
1. `isMacieStatusCompleteChoice` Step Functions Choice state checks whether the Macie sensitive data discovery job is complete.
1.1 If yes, the `getMacieFindingsCount` Lambda function runs.
1.1 If no, the Step Functions Wait state waits 60 seconds and then restarts Step 5.
1. `getMacieFindingsCount` Lambda function counts all of the findings from the Macie sensitive data discovery job.
1. `isSensitiveDataFound` Step Functions Choice state checks whether sensitive data was found in the Macie sensitive data discovery job.
1.1 If there was sensitive data discovered, run the `triggerManualApproval` Lambda function.
1.1 If there was no sensitive data discovered, run the `moveAllScanStageS3Files` Lambda function.
1. `moveAllScanStageS3Files` Lambda function moves all of the objects from the scan stage S3 bucket to the scanned data S3 bucket.
1. `triggerManualApproval` Lambda function tags and moves objects with sensitive data discovered to the manual review S3 bucket, and moves objects with no sensitive data discovered to the scanned data S3 bucket. The function then sends a notification to the ApprovalRequestNotification Amazon SNS topic as a notification that manual review is required.
1. Email is sent to the email address that’s subscribed to the `ApprovalRequestNotification` Amazon SNS topic (from the application deployment template) for the manual review user with the option to *Approve* or *Deny* pipeline ingestion for these objects.
1. Manual review user assesses the objects with sensitive data in the manual review S3 bucket and selects the **Approve** or **Deny** links in the email.
1. The decision request is sent from the Amazon API Gateway to the `receiveApprovalDecision` Lambda function.
1. `manualApprovalChoice` Step Functions Choice state checks the decision from the manual review user.
1.1 If denied, run the `deleteManualReviewS3Files` Lambda function.
1.1 If approved, run the `moveToScannedDataS3Files` Lambda function.
1. `deleteManualReviewS3Files` Lambda function deletes the objects from the manual review S3 bucket.
1. `moveToScannedDataS3Files` Lambda function moves the objects from the manual review S3 bucket to the scanned data S3 bucket.
1. The next step of the automated data pipeline will begin with the objects in the scanned data S3 bucket.

## Prerequisites
For this application, you need the following prerequisites:

* The AWS Command Line Interface (AWS CLI) installed and configured for use.
* The AWS Serverless Application Model (AWS SAM) CLI installed and configured for use.
* An IAM role or user with permissions to publish serverless applications using the AWS SAM CLI.

You can use AWS Cloud9 to deploy the application. AWS Cloud9 includes the AWS CLI and AWS SAM CLI to simplify setting up your development environment. 

## Deploy the application with AWS SAM CLI
You can deploy this application using the AWS SAM CLI. AWS SAM uses AWS CloudFormation as the underlying deployment mechanism. AWS SAM is an open-source framework that you can use to build serverless applications on AWS.

### To deploy the application
For instrucitons for deployment, refer to the blog post walkthrough (here)[https://aws-preview.aka.amazon.com/blogs/security/use-macie-to-discover-sensitive-data-as-part-of-automated-data-pipelines/].

## Considerations for regular use
Before using this application in a production data pipeline, you will need to stop and consider some practical matters. First, the notification mechanism used when sensitive data is identified in the objects is email. Email doesn’t scale: you should expand this solution to integrate with your ticketing or workflow management system. If you choose to use email, subscribe a mailing list so that the work of reviewing and responding to alerts is shared across a team.

Second, the application is run on a scheduled basis (every 6 hours by default). You should consider starting the application when your preliminary validations have completed and are ready to perform a sensitive data scan on the data as part of your pipeline. You can modify the CloudWatch Event Rule to run in response to an Amazon EventBridge event instead of a scheduled basis.

Third, the application currently uses a 60 second Step Functions Wait state when polling for the Macie discovery job completion. In real world scenarios, the discovery scan will take 10 minutes at a minimum, likely several orders of magnitude longer. You should evaluate the typical execution times for your application execution and tune the polling period accordingly. This will help reduce costs related to running Lambda functions and log storage within CloudWatch Logs. The polling period is defined in the Step Functions state machine definition file (macie_pipeline_scan.asl.json)[https://github.com/aws-samples/amazonmacie-datapipeline-scan/blob/master/statemachine/macie_pipeline_scan.asl.json#L67] under the `pollForCompletionWait` state.

Fourth, the application currently doesn’t account for false positives in the sensitive data discovery job results. Also, the application will progress or delete all objects identified based on the decision by the reviewer. You should consider expanding the application to handle false positives through automation rather than manual review / intervention (such as deleting the files from the *manual review* bucket or removing the sensitive data tags applied).

Last, the solution will stop the ingestion of a subset of objects into your pipeline. This behavior is similar to other validation and data quality checks that most customers perform as part of the data pipeline. However, you should test to ensure that this will not cause unexpected outcomes and address them in your downstream application logic accordingly.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

