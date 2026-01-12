import os
import httpx
import logging
from typing import Dict, Any

logger = logging.getLogger("opensearch_client")
OPENSEARCH_URL = os.getenv("OPENSEARCH_URL", "http://localhost:9200")
INDEX = "documents"

_default_timeout = httpx.Timeout(10.0, connect=5.0)

def ensure_index():
    """
    Create the index with mappings if it does not exist.
    """
    url = f"{OPENSEARCH_URL}/{INDEX}"
    mapping = {
      "mappings": {
        "properties": {
          "tenant": {"type": "keyword"},
          "docId": {"type": "keyword"},
          "title": {"type": "text"},
          "content": {"type": "text"},
          "createdAt": {"type": "date"}
        }
      }
    }
    with httpx.Client(timeout=_default_timeout) as client:
        resp = client.head(url)
        if resp.status_code == 200:
            logger.info("Index '%s' already exists", INDEX)
            return True
        logger.info("Creating index '%s'", INDEX)
        resp = client.put(url, json=mapping)
        if resp.status_code in (200,201):
            logger.info("Index created")
            return True
        logger.error("Failed to create index: %s %s", resp.status_code, resp.text)
        return False

def index_document(tenant: str, docId: str, body: Dict[str, Any]):
    _id = f"{tenant}:{docId}"
    url = f"{OPENSEARCH_URL}/{INDEX}/_doc/{_id}"
    with httpx.Client(timeout=_default_timeout) as client:
        resp = client.put(url, json=body)
        return resp

def get_document(tenant: str, docId: str):
    _id = f"{tenant}:{docId}"
    url = f"{OPENSEARCH_URL}/{INDEX}/_doc/{_id}"
    with httpx.Client(timeout=_default_timeout) as client:
        resp = client.get(url)
        return resp

def delete_document(tenant: str, docId: str):
    _id = f"{tenant}:{docId}"
    url = f"{OPENSEARCH_URL}/{INDEX}/_doc/{_id}"
    with httpx.Client(timeout=_default_timeout) as client:
        resp = client.delete(url)
        return resp

def search_documents(tenant: str, q: str, size: int = 10):
    url = f"{OPENSEARCH_URL}/{INDEX}/_search"
    query = {
      "size": size,
      "query": {
        "bool": {
          "must": {
            "multi_match": {
              "query": q,
              "fields": ["title^3", "content"]
            }
          },
          "filter": {
            "term": {"tenant": tenant}
          }
        }
      }
    }
    with httpx.Client(timeout=_default_timeout) as client:
        resp = client.post(url, json=query)
        return resp

def ping():
    url = f"{OPENSEARCH_URL}/"
    try:
        with httpx.Client(timeout=_default_timeout) as client:
            resp = client.get(url)
            return resp
    except Exception as ex:
        logger.exception("Ping failed")
        raise
