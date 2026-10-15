FUNCTION          ?= clinica-data-ingestion
SQS_NAME		  ?= clinica-sqs-queue
ECR_REPO          ?= clinica-lens/data-ingestion
REGION            ?= eu-west-3
ACCOUNT           := $(shell aws sts get-caller-identity --query Account --output text)
REGISTRY          := $(ACCOUNT).dkr.ecr.$(REGION).amazonaws.com
REPO              := $(REGISTRY)/$(ECR_REPO)
TAG               ?= v1.1
LAMBDA_ROLE_NAME  ?= clinica-data-ingestion-execution-role
ROLE_ARN          ?= arn:aws:iam::$(ACCOUNT):role/$(LAMBDA_ROLE_NAME)
SQS_ARN			  ?= arn:aws:sqs:$(REGION):$(ACCOUNT):$(SQS_NAME)
MEMORY            ?= 3008
TIMEOUT           ?= 300
export AWS_PAGER :=

build:
	docker build --platform linux/amd64 -t $(FUNCTION):local .

# Local dev with code mounted
run:
	docker run --rm -p 9000:8080 \
	  -v $(PWD)/src:/var/task \
	  -v $(HOME)/.aws:/root/.aws:ro -e AWS_PROFILE -e INGEST_AWS_REGION=$(REGION) \
	  --env-file .env.local \
	  $(FUNCTION):local

invoke-%:
	curl -s -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" \
	  -d @events/sqs_s3_event_$*.json

test:
	pytest -v

# make push TAG=v1.0
push:
	aws ecr get-login-password --region $(REGION) | docker login --username AWS --password-stdin $(REGISTRY)
	docker buildx build --platform linux/amd64 --provenance=false -t $(REPO):$(TAG) --push .

# make create TAG=v1.0
create:
	aws lambda create-function \
	  --function-name $(FUNCTION) \
	  --description "Ingestion pipeline" \
	  --package-type Image \
	  --code ImageUri=$(REPO):$(TAG) \
	  --role $(ROLE_ARN) \
	  --architectures x86_64 \
	  --memory-size $(MEMORY) \
	  --timeout $(TIMEOUT) \
	  --region $(REGION)
	aws lambda wait function-active-v2 --function-name $(FUNCTION) --region $(REGION)
	$(MAKE) trigger

trigger:
	aws lambda create-event-source-mapping \
	  --function-name $(FUNCTION) \
	  --event-source-arn $(SQS_ARN) \
	  --batch-size 1 \
	  --scaling-config MaximumConcurrency=4 \
	  --region $(REGION)

# make deploy TAG=v1.0
deploy: push
	aws lambda update-function-code --function-name $(FUNCTION) --image-uri $(REPO):$(TAG) --region $(REGION)
	aws lambda wait function-active-v2 --function-name $(FUNCTION) --region $(REGION)