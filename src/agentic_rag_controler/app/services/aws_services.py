import boto3
from botocore.exceptions import BotoCoreError, ClientError
from app.schemas.auth_schemas import AWS_Keys


def load_aws_keys(qdrant_url: str, qdrant_api_key: str) -> AWS_Keys:
    ssm = boto3.client("ssm", region_name="eu-west-3")
    try:
        resp = ssm.get_parameters(
            Names=[qdrant_url, qdrant_api_key], WithDecryption=True
        )
    except (BotoCoreError, ClientError) as e:
        raise RuntimeError(f"Cannot read SSM parameters: {e}") from e

    if resp["InvalidParameters"]:
        raise RuntimeError(f"Missing SSM parameters: {resp['InvalidParameters']}")

    values = {p["Name"]: p["Value"] for p in resp["Parameters"]}
    return AWS_Keys(
        qdrant_url=values[qdrant_url], qdrant_api_key=values[qdrant_api_key]
    )
