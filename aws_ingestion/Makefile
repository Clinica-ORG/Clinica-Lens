FUNCTION   ?= clinica-data-ingestion
ECR_REPO   ?= clinica-lens/data-ingestion
REGION     ?= eu-west-3
ACCOUNT    := $(shell aws sts get-caller-identity --query Account --output text)
REGISTRY   := $(ACCOUNT).dkr.ecr.$(REGION).amazonaws.com
REPO       := $(REGISTRY)/$(ECR_REPO)
TAG        ?= $(shell git rev-parse --short HEAD)

build:
	docker build --platform linux/amd64 -t $(FUNCTION):local .

# Local run with code mounted
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
	pytest tests/

push:
	aws ecr get-login-password --region $(REGION) | docker login --username AWS --password-stdin $(REGISTRY)
	docker buildx build --platform linux/amd64 --provenance=false -t $(REPO):$(TAG) --push .

deploy: push
	aws lambda update-function-code --function-name $(FUNCTION) --image-uri $(REPO):$(TAG) --region $(REGION)
	aws lambda wait function-updated --function-name $(FUNCTION) --region $(REGION)