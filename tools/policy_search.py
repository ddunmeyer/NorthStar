"""search_policies: policy answers only from the Knowledge Base, with citations.

Uses the Bedrock Knowledge Base Retrieve API, which returns matching text and
its source without generating an answer. Each policy is split into its
numbered sections so the agent can cite, for example, "NS-HR-001, Section 2".
"""
import os
import re

import boto3
from strands import tool

REGION = os.getenv("AWS_REGION") or "us-east-1"
KB_ID = os.getenv("NORTHSTAR_KB_ID")
_client = boto3.client("bedrock-agent-runtime", region_name=REGION)

_DOC_ID = re.compile(r"Document ID:\s*(\S+)")
_SECTION = re.compile(r"##\s*(\d+)\.\s*")


def _split(text: str):
    """Return (title, document_id, [(section_number, section_text), ...])."""
    head, *rest = _SECTION.split(text)
    title = head.strip().lstrip("#").split("Document ID")[0].strip()
    match = _DOC_ID.search(head)
    sections = [(num, body.strip()) for num, body in zip(rest[0::2], rest[1::2])]
    if not sections:  # chunk started mid-document: keep the text, section unknown
        sections = [(None, head.strip())]
    return title, (match.group(1) if match else None), sections


@tool
def search_policies(question: str) -> dict:
    """Search North Star's company policies: HR, travel and expense, IT support, access requests,
    change management, and internal jobs.

    Returns policy text split into numbered sections, with each document's ID. Answer only from
    this text and cite the document and section, for example "Employee Handbook (NS-HR-001),
    Section 2". If none of the text answers the question, say no policy covers it.

    Args:
        question: The policy question in plain words.
    """
    if not KB_ID:
        return {"error": "NORTHSTAR_KB_ID is not set in .env."}

    response = _client.retrieve(
        knowledgeBaseId=KB_ID,
        retrievalQuery={"text": question},
        retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": 3}},
    )

    documents = []
    for result in response.get("retrievalResults", []):
        title, doc_id, sections = _split(result["content"]["text"])
        uri = result.get("location", {}).get("s3Location", {}).get("uri", "")
        documents.append({
            "document_id": doc_id or uri.rsplit("/", 1)[-1].removesuffix(".md"),
            "title": title,
            "score": round(result.get("score", 0), 3),
            "sections": [{"section": num, "text": body} for num, body in sections],
        })

    return {
        "question": question,
        "documents": documents,
        "instruction": "Answer only from these sections and cite the document and section. "
                       "If none of them answers the question, say no policy covers it.",
    }