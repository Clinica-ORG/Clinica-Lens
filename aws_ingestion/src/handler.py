import json
import logging
from urllib.parse import unquote_plus
from processing import process_pdf, remove_pdf
from config import get_settings

log = logging.getLogger()
log.setLevel(logging.INFO)


def lambda_handler(event, context):
    failures = []
    for record in event["Records"]:
        try:
            process_message(record)
        except Exception:
            log.exception("Failed message %s", record["messageId"])
            failures.append({"itemIdentifier": record["messageId"]})
    # return {"batchItemFailures": failures}


def process_message(sqs_record):
    log.info(f"Processing message {sqs_record['messageId']}")
    body = json.loads(sqs_record["body"])

    # first notification from s3 is a test event
    if body.get("Event") == "s3:TestEvent":
        return

    settings = get_settings()

    for s3_record in body.get("Records", []):
        event_name = s3_record["eventName"]
        bucket = s3_record["s3"]["bucket"]["name"]
        key = unquote_plus(s3_record["s3"]["object"]["key"])
        try:
            if event_name.startswith("ObjectCreated"):
                log.info(f"Ingest/re-ingest s3://{bucket}/{key}")
                process_pdf(bucket, key, settings.vlm_toc)
            elif event_name.startswith("ObjectRemoved"):
                log.info(f"Delete vectors for s3://{bucket}/{key}")
                remove_pdf(bucket, key)
        except Exception as e:
            raise e  # I define only 1 document for message so safe to raise here
        log.info(f"Process done for: s3://{bucket}/{key}")
