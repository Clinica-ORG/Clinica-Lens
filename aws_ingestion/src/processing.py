import hashlib
import uuid
import logging
import pymupdf
import pymupdf4llm
from langchain_community.document_loaders import PyPDFLoader
from clients import s3, datalab_client, embeddings_client, llm_client, vectordb_client
from splitters import get_splitter
from utils import (
    get_toc_num_page,
    fix_toc,
    fix_doc_header_using_toc,
    extract_pdf_title_llm,
    add_metadata_to_docs,
)

COLLECTION = "clinica-lens"
NAMESPACE = uuid.UUID("12345678-1234-5678-1234-567812345678")


def file_sha256(path_or_bytes) -> str:
    h = hashlib.sha256()
    h.update(
        path_or_bytes
        if isinstance(path_or_bytes, bytes)
        else open(path_or_bytes, "rb").read()
    )
    return h.hexdigest()


def point_id(doc_id: str, chunk_index: int) -> str:
    return str(uuid.uuid5(NAMESPACE, f"{doc_id}:{chunk_index}"))


def process_pdf(bucket: str, key: str, vlm_toc: bool) -> None:
    """
    Process a pdf file from s3, chunk and upload/update to vectorDB
    Args:
        bucket (str): name of s3 bucket
        key (str): key of the file in s3 bucket
        vlm_toc (bool): use VLM Chandra v2 to get table of contents (more precise)
    """
    logging.info("Init splitters")
    splitter = get_splitter()

    logging.info(f"Downloading s3://{bucket}/{key}")
    local_file_path = f"/tmp/{key.split('/')[-1]}"
    try:
        s3.download_file(
            bucket_name=bucket, object_key=key, local_file_path=local_file_path
        )
    except Exception as e:
        raise e

    logging.info("Read PDF to documents:")
    docs = PyPDFLoader(local_file_path).load()
    logging.info(f"Loaded {len(docs)} pages from the PDF")

    logging.info("Extracting document title using LLM")
    title = extract_pdf_title_llm(llm=llm_client.get_llm, docs=docs, max_page_check=5)

    logging.info("Retrieving table of contents from PDF.")
    toc = None
    if vlm_toc:
        toc_page = get_toc_num_page(docs)
        logging.info(f"Table of contents found on page {toc_page} (1-indexed).")
        toc = datalab_client.convert(file_path=local_file_path, page=str(toc_page - 1))
        toc = fix_toc(toc)
    else:
        toc = pymupdf.open(local_file_path).get_toc()

    logging.info("Read PDF as markdown")
    markdown_text = pymupdf4llm.to_markdown(
        local_file_path, page_chunks=True, footer=False, header=False
    )

    logging.info("Fix document header using table of contents")
    doc_fixed = fix_doc_header_using_toc(
        toc=toc, markdown_text=markdown_text, docs=docs
    )
    first_strategy = "header"
    second_strategy = "recursive"

    logging.info(f"Split document into chunks using {first_strategy} splitter:")
    sections = splitter.split_text(text=doc_fixed, strategy=first_strategy)
    sections = add_metadata_to_docs(metadata={"source": title}, docs=sections)

    logging.info(f"Split document into chunks using {second_strategy} splitter:")
    sub_sections = splitter.split_documents(
        documents=sections, strategy=second_strategy
    )

    logging.info(f"Generated embeddings for {len(sub_sections)} document chunks")
    embeddings = embeddings_client.get_embeddings(splits=sub_sections)

    logging.info("Generated metadata for vector of VectorDB")
    doc_id = file_sha256(local_file_path)
    point_ids = [
        point_id(doc_id=doc_id, chunk_index=i) for i in range(len(sub_sections))
    ]
    payload_points = [
        {"doc_id": doc_id, "s3_key": key, **d.metadata} for d in sub_sections
    ]

    logging.info("Upload to VectorDB")
    vectordb_client.upload_collection(
        vectors=embeddings, payload=payload_points, ids=point_ids
    )


def remove_pdf(bucket: str, key: str) -> None:
    """
    Get the information of the file and removed their vectors in vectorDB
    Args:
        bucket (str): name of s3 bucket
        key (str): key of the file in s3 bucket
    """
    logging.info(f"Downloading s3://{bucket}/{key}")
    local_file_path = f"/tmp/{key.split('/')[-1]}"
    s3.download_file(
        bucket_name=bucket, object_key=key, local_file_path=local_file_path
    )
    vectordb_client.delete_points(key=key)
