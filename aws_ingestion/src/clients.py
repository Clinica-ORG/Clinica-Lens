import boto3
from datalab_sdk import DatalabClient, ConvertOptions
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from qdrant_client import QdrantClient, models
from qdrant_client.models import Distance, VectorParams

from config import get_settings

OPENAI_EMBEDDING_MODEL_DIMENSION = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
}


class SecretManager:
    def __init__(self, region_name: str):
        self.ssm = boto3.client("ssm", region_name=region_name)

    def get_secret(self, secret_name: str) -> str:
        """
        Retrieve a secret value from AWS Systems Manager Parameter Store.
        Args:
            secret_name (str): The name of the secret to retrieve.
        Returns:
            str: The secret value as a string.
        """
        response = self.ssm.get_parameter(Name=secret_name)
        return response["Parameter"]["Value"]


class S3Client:
    def __init__(self, region_name: str):
        self.s3 = boto3.client("s3", region_name=region_name)

    def download_file(
        self, bucket_name: str, object_key: str, local_file_path: str
    ) -> None:
        """
        Download a file from an S3 bucket to a local path.
        Args:
            bucket_name (str): The name of the S3 bucket.
            object_key (str): The key of the object in the S3 bucket.
            local_file_path (str): The local file path to save the downloaded file.
        """
        self.s3.download_file(bucket_name, object_key, local_file_path)

    def read_file(self, bucket_name: str, object_key: str) -> bytes:
        """
        Read a file from an S3 bucket into memory.
        Args:
            bucket_name (str): The name of the S3 bucket.
            object_key (str): The key of the object in the S3 bucket.
        Returns:
            bytes: The content of the file as bytes.
        """
        response = self.s3.get_object(Bucket=bucket_name, Key=object_key)
        return response["Body"].read()


class EmbeddingsClient:
    def __init__(self, api_key: str, model_name: str):
        self.embeddings = OpenAIEmbeddings(openai_api_key=api_key, model=model_name)
        self.model_name = model_name
        self.embedding_dimension = OPENAI_EMBEDDING_MODEL_DIMENSION[model_name]

    def get_embeddings(self, splits: list) -> list[list[float]]:
        """
        Get embeddings for a list of text splits using OpenAIEmbeddings.
        Args:
            splits (list): A list of text splits to generate embeddings for.
        Returns:
            list[list[float]]: A list of embedding vectors for the document splits.
        """
        texts = [split.page_content for split in splits]
        return self.embeddings.embed_documents(texts)

    @property
    def get_embedding_dimension(self) -> int:
        """
        Get the embedding dimension for the used model.
        Returns:
            int: The embedding dimension for the model.
        """
        return self.embedding_dimension


class DatalabClientWrapper:
    def __init__(self, api_key: str):
        self.client = DatalabClient(api_key=api_key)

    def convert(self, file_path: str, page: str) -> str | list[str]:
        """
        Convert a PDF file to markdown using the DatalabClient.
        Args:
            file_path (str): The path to the PDF file.
            page (str): The page(s) number to convert.
        Returns:
            str | list[str]: The converted markdown text as a string or a list of strings.
        """
        options = ConvertOptions(
            output_format="markdown",  # Output format
            mode="balanced",  # Processing mode
            paginate=False,  # Add page delimiters
            page_range=page,  # Specific pages (0-indexed); do not combine with max_pages
            additional_config={
                "keep_pageheader_in_output": False,
                "keep_pagefooter_in_output": False,
                "disable_html_prettify": True,
            },
        )
        result = self.client.convert(file_path, options=options)
        return result.markdown.splitlines()


class LLMClient:
    def __init__(self, model_name: str, api_key: str):
        self.llm = ChatOpenAI(
            temperature=0,
            model_name=model_name,
            api_key=api_key,
            max_tokens=4000,
        )

    @property
    def get_llm(self):
        return self.llm


class VectorDBClient:
    def __init__(self, endpoint: str, api_key: str, **kwargs):
        self.endpoint = endpoint
        self.client = QdrantClient(
            url=endpoint,
            api_key=api_key,
            cloud_inference=False,
            check_compatibility=False,
        )
        self.kwargs = kwargs

    def ensure_collection(self):
        needed_keys = ["collection_name", "vector_size", "distance"]
        for key in needed_keys:
            if key not in self.kwargs:
                raise ValueError(f"Missing required argument: {key}")
        if not self.client.collection_exists(self.kwargs["collection_name"]):
            self.client.create_collection(
                collection_name=self.kwargs["collection_name"],
                vectors_config=VectorParams(
                    size=self.kwargs["vector_size"], distance=self.kwargs["distance"]
                ),
            )
        for field in ("doc_id", "s3_key"):
            self.client.create_payload_index(
                self.kwargs["collection_name"], field, models.PayloadSchemaType.KEYWORD
            )

    def upload_collection(
        self, vectors: list[list[float]], payload: list[dict], ids: list[str]
    ):
        """
        Upload a collection of vectors to the vector database.
        Args:
            vectors (list[list[float]]): A list of embedding vectors.
            payload (list[dict]): A list of metadata dictionaries corresponding to each vector.
            ids (list[str]): A list of unique identifiers for each vector.
        """
        self.client.upload_collection(
            collection_name=self.kwargs["collection_name"],
            vectors=vectors,
            payload=payload,
            ids=ids,
            parallel=4,
            max_retries=3,
        )

    def delete_points(self, key: str) -> None:
        """
        Delete vectors from vector DB using s3 file key
        Args:
            key (str): key of the file on S3
        """
        self.client.delete(
            collection_name=self.kwargs["collection_name"],
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="s3_key",
                            match=models.MatchValue(value=key),
                        ),
                    ],
                )
            ),
        )


settings = get_settings()
sm = SecretManager(region_name=settings.aws_region)
s3 = S3Client(region_name=settings.aws_region)
datalab_client = DatalabClientWrapper(
    api_key=sm.get_secret(settings.datalab_api_key_secret_name)
)
embeddings_client = EmbeddingsClient(
    api_key=sm.get_secret(settings.openai_api_key_secret_name),
    model_name=settings.openai_emb_model_name,
)
llm_client = LLMClient(
    model_name=settings.openai_llm_model_name,
    api_key=sm.get_secret(settings.openai_api_key_secret_name),
)
vectordb_client = VectorDBClient(
    endpoint=settings.vectordb_endpoint,
    api_key=sm.get_secret(settings.vectordb_api_key_secret_name),
    collection_name="clinica_lens_collection",
    vector_size=embeddings_client.get_embedding_dimension,
    distance=Distance.COSINE,
)
vectordb_client.ensure_collection()
