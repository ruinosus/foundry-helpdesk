"""Phase 1 ingestion: build the Foundry IQ knowledge base.

Run once (and again whenever the corpus changes), after `azd up`:

    cd backend
    uv run python -m app.knowledge.ingest

Steps:
  1. Upload every markdown in corpus/ to the blob container.
  2. Create a blob *knowledge source* (Azure AI Search auto-chunks + embeds it
     using the Foundry embedding deployment, via the search managed identity).
  3. Create the *knowledge base* that orchestrates agentic retrieval over that
     source, using gpt-4.1-mini for query planning + answer synthesis.

Auth is DefaultAzureCredential throughout (no keys). The deploying user needs
Search Service Contributor + Storage Blob Data Contributor (granted by the
Bicep); the search managed identity reaches the model + blobs via its own roles.

SDK surface verified against azure-search-documents 11.7.0b2.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from azure.core.credentials import TokenCredential
from azure.identity import DefaultAzureCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    AzureBlobKnowledgeSource,
    AzureBlobKnowledgeSourceParameters,
    AzureOpenAIVectorizerParameters,
    KnowledgeBase,
    KnowledgeBaseAzureOpenAIModel,
    KnowledgeRetrievalLowReasoningEffort,
    KnowledgeSourceAzureOpenAIVectorizer,
    KnowledgeSourceIngestionParameters,
    KnowledgeSourceReference,
)
from azure.storage.blob import BlobServiceClient

from app.settings import settings

CORPUS_DIR = Path(__file__).parent / "corpus"
KNOWLEDGE_SOURCE_NAME = "helpdesk-runbooks-ks"


def _require(name: str, value: str) -> str:
    if not value:
        sys.exit(
            f"Missing {name}. Populate backend/.env from `azd env get-values` "
            f"(see the README Phase 1 steps)."
        )
    return value


def upload_corpus(credential: TokenCredential) -> int:
    account = _require("AZURE_STORAGE_ACCOUNT", settings.azure_storage_account)
    container = settings.azure_storage_container
    blob_service = BlobServiceClient(
        account_url=f"https://{account}.blob.core.windows.net",
        credential=credential,
    )
    container_client = blob_service.get_container_client(container)

    files = sorted(CORPUS_DIR.glob("*.md"))
    if not files:
        sys.exit(f"No markdown found in {CORPUS_DIR}")

    for path in files:
        with path.open("rb") as fh:
            container_client.upload_blob(name=path.name, data=fh, overwrite=True)
        print(f"  uploaded {path.name}")
    print(f"Uploaded {len(files)} documents to {account}/{container}.")
    return len(files)


def create_knowledge_source(index_client: SearchIndexClient) -> None:
    openai_endpoint = _require("AZURE_AI_OPENAI_ENDPOINT", settings.azure_ai_openai_endpoint)
    storage_id = _require("AZURE_STORAGE_RESOURCE_ID", settings.azure_storage_resource_id)

    # ResourceId=<...>; tells Search to read blobs via its managed identity (keyless).
    knowledge_source = AzureBlobKnowledgeSource(
        name=KNOWLEDGE_SOURCE_NAME,
        description="Internal engineering runbooks and policies (helpdesk corpus).",
        azure_blob_parameters=AzureBlobKnowledgeSourceParameters(
            connection_string=f"ResourceId={storage_id};",
            container_name=settings.azure_storage_container,
            ingestion_parameters=KnowledgeSourceIngestionParameters(
                embedding_model=KnowledgeSourceAzureOpenAIVectorizer(
                    azure_open_ai_parameters=AzureOpenAIVectorizerParameters(
                        resource_url=openai_endpoint,
                        deployment_name=settings.foundry_embedding_model,
                        model_name=settings.foundry_embedding_model,
                        # auth_identity omitted -> search service managed identity
                    )
                ),
            ),
        ),
    )
    index_client.create_or_update_knowledge_source(knowledge_source)
    print(f"Knowledge source '{KNOWLEDGE_SOURCE_NAME}' created/updated.")


def create_knowledge_base(index_client: SearchIndexClient) -> None:
    openai_endpoint = settings.azure_ai_openai_endpoint
    kb_name = settings.azure_search_knowledge_base

    knowledge_base = KnowledgeBase(
        name=kb_name,
        description="Helpdesk runbooks and policies for internal engineering support.",
        knowledge_sources=[KnowledgeSourceReference(name=KNOWLEDGE_SOURCE_NAME)],
        models=[
            KnowledgeBaseAzureOpenAIModel(
                azure_open_ai_parameters=AzureOpenAIVectorizerParameters(
                    resource_url=openai_endpoint,
                    deployment_name=settings.foundry_model,
                    model_name=settings.foundry_model,
                )
            )
        ],
        output_mode="answerSynthesis",
        answer_instructions=(
            "Answer only from the retrieved runbooks. Cite the source document for "
            "every claim. If the answer is not in the knowledge base, say you don't know."
        ),
        retrieval_reasoning_effort=KnowledgeRetrievalLowReasoningEffort(),
    )
    index_client.create_or_update_knowledge_base(knowledge_base)
    print(f"Knowledge base '{kb_name}' created/updated.")


def wait_for_ingestion(index_client: SearchIndexClient, timeout_s: int = 600) -> None:
    """Poll the knowledge source status until indexing settles (best-effort)."""
    print("Waiting for indexing to complete (this can take a few minutes)...")
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            status = index_client.get_knowledge_source_status(KNOWLEDGE_SOURCE_NAME)
        except Exception as exc:  # noqa: BLE001 - status API is preview; tolerate gaps
            print(f"  (status check unavailable: {exc}); skipping wait.")
            return
        text = str(getattr(status, "status", status)).lower()
        print(f"  status: {text}")
        if any(s in text for s in ("success", "ready", "completed", "idle")):
            print("Ingestion looks complete.")
            return
        if "error" in text or "failed" in text:
            print("Ingestion reported an error — check the Azure portal.")
            return
        time.sleep(15)
    print("Timed out waiting; check the knowledge source status in the portal.")


def main() -> None:
    _require("AZURE_SEARCH_ENDPOINT", settings.azure_search_endpoint)
    credential = DefaultAzureCredential()
    index_client = SearchIndexClient(
        endpoint=settings.azure_search_endpoint, credential=credential
    )

    print("== Step 1/3: upload corpus ==")
    upload_corpus(credential)
    print("== Step 2/3: create knowledge source ==")
    create_knowledge_source(index_client)
    print("== Step 3/3: create knowledge base ==")
    create_knowledge_base(index_client)

    wait_for_ingestion(index_client)
    print("\nDone. The knowledge base is ready for agentic retrieval.")


if __name__ == "__main__":
    main()
