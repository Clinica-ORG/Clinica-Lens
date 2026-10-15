# Data ingestion pipeline
## Description
The data ingestion pipeline is orchestrated on AWS. The documents are stored in s3, each event (created, deleted) will trigger
an event to SQS, which processed by Lambda function. The made choice is decided based on:
- Ability to scale: with the combination of SQS and Lambda, we could achieve good scaling when large number of documents
in s3, with control from SQS to prevent rate limit of external services (embedding, vectorDB)
- We use external services for embedding, vectorDB: the CPU comsumption is low, and there is no GPU usage, which suitable with lambda function
Downside:
- Efforts for monitoring: even though there are built-in functionalities (X-ray, Cloudwatch, ect) for monitoring, but we need to put some efforts to pull them to
our centrailized Grafana dashboard

## Pre-requirements
User role: the user must have needed roles in policy, such as: push to ECR, create/update Lambda function, pass role to Lambda function
### SQS
Go to [Amazon SQS console](https://console.aws.amazon.com/sqs), `Visibility timeout` should longer the `Lambda` timeout, leave every options at defaut and create the queue.
The only option we concern is Dead-letter queue, which put failed messages back to queue.
For the policy, we need to add the policy that allows s3 to send message to the queue, follow these 2 steps
1. Modify policy at creation, add these statement
```json
{
    "Sid": "AllowS3SendMessage",
    "Effect": "Allow",
    "Principal": {
        "Service": "s3.amazonaws.com"
        },
        "Action": "sqs:SendMessage",
        "Resource": "arn:aws:sqs:<REGION>:<ACCOUNT>:<SQS_NAME>",
        "Condition": {
        "StringEquals": {
            "aws:SourceAccount": "<ACCOUNT>"
        },
        "ArnLike": {
            "aws:SourceArn": "<S3_ARN>"
        }
    }
}
```
2. Add in s3 UI
Access `Properties` tab
![](images/s3_prop_tab.png)
Create an event notification in Event notifications section
![](images/s3_noti_creation.png)
- Leave `suffix`: .pdf
- Choose `All object create events`, `All object removal events`
- In `Destination`, choose `SQS queue`, and pick the created SQS queue


### Lambda role:
- To be able to read items from SQS (AWSLambdaSQSQueueExecutionRole)
- Read S3 object, read parameter from System Manager (or secrets if use Secrets Manager - more expensive!!)

The policy to for the role
```json
{
	"Version": "2012-10-17",
	"Statement": [
		{
			"Sid": "ReadSqsQueue",
			"Effect": "Allow",
			"Action": [
				"sqs:ReceiveMessage",
				"sqs:DeleteMessage",
				"sqs:GetQueueAttributes"
			],
			"Resource": "<ARN_SQS_QUEUE>"
		},
		{
			"Sid": "CreateLogGroup",
			"Effect": "Allow",
			"Action": "logs:CreateLogGroup",
			"Resource": "arn:aws:logs:<REGION>:<ACCOUNT>:log-group:/aws/lambda/clinica-data-ingestion"
		},
		{
			"Sid": "WriteLogs",
			"Effect": "Allow",
			"Action": [
				"logs:CreateLogStream",
				"logs:PutLogEvents"
			],
			"Resource": "arn:aws:logs:<REGION>:<ACCOUNT>:log-group:/aws/lambda/clinica-data-ingestion:*"
		},
		{
			"Sid": "ReadSsmParameters",
			"Effect": "Allow",
			"Action": "ssm:GetParameter",
			"Resource": "arn:aws:ssm:<REGION>:<ACCOUNT>:parameter/clinica-lens/*"
		},
		{
			"Sid": "ReadPdfFromS3",
			"Effect": "Allow",
			"Action": "s3:GetObject",
			"Resource": "<ARN_S3>/*"
		}
	]
}
```

## Developpment and Deployment
I use Makefile to avoid repeating command
```bash
# Build the image for local test
make build
# Local dev with code mounted
make run
# testing with sqs message locally
# simulate Object created event
make invoke-created
# simulate Object delete event
make invoke-delete
# testing (unit tests, integration tests)
make test
# push image to ECR
make push TAG=<tag>
# create the lambda function (1st run), chain with trigger creation
# link lambda function to sqs
make create TAG=<tag>
# update the lambda function
# auto push image and update lambda function
make deploy TAG=<tag>
```
