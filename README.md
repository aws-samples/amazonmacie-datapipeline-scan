## Use Macie to discover sensitive data as part of  automated data pipelines

This solution will integrate  Amazon Macie (https://aws.amazon.com/macie/) as part of the data ingestion step in your data pipeline. Amazon Macie is a fully managed data security and privacy service that uses machine learning and pattern matching to discover sensitive data in AWS. 

If sensitive data is discovered by Amazon Macie, the solution triggers a manual review step notifying an administrator to review the data and decide whether to allow the data pipeline to continue ingesting the objects. If allowed, the objects will be tagged with an Amazon S3 object tag (https://docs.aws.amazon.com/AmazonS3/latest/dev/object-tagging.html) to identify that sensitive data was found in the object prior to progressing to the next stage of the pipeline.

This helps reduce the risk that sensitive data, such as personally identifiable information, will be inadvertently ingested into a data lake using automation and manual review, where required. This solution can be extended to use custom identifiers to expand your sensitive data discovery (https://aws.amazon.com/blogs/security/discover-sensitive-data-by-using-custom-data-identifiers-with-amazon-macie/), take additional automated action, or add additional validation steps as part of the ingestion phase, and use.


## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

