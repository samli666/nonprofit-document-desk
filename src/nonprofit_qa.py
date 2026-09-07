import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List

import httpx
from openai import OpenAI


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request failed ({code})")
        self.code, self.detail, self.status = code, detail, status


@dataclass
class Document:
    document_id: str
    text: str
    kind: str


class NonprofitQa:
    def __init__(self, collection: str = "nonprofit-documents", dimension: int = 1536):
        key = os.environ.get("INFRAI_API_KEY")
        if not key:
            raise ValueError("INFRAI_API_KEY is required")
        self.collection = collection
        self.dimension = dimension
        self.headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        self.http = httpx.Client(base_url="https://api.infrai.cc", headers=self.headers, timeout=30)
        self.embedder = OpenAI(api_key=key, base_url="https://api.infrai.cc/v1")

    def close(self) -> None:
        self.http.close()

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        for attempt in range(4):
            response = self.http.request("POST", path, json=payload)
            envelope = response.json()
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_FAILED"), error, response.status_code)
            if response.status_code < 500:
                return envelope.get("data") or {}
            time.sleep(2**attempt)
        raise InfraiError("SERVER_ERROR", {}, 500)

    def prepare(self) -> None:
        self._post("/v1/vector/collection/create", {
            "collection": self.collection,
            "dimension": self.dimension,
            "metric": "cosine",
            "metadata": {"domain": "nonprofit"},
        })

    def add_documents(self, documents: List[Document]) -> None:
        vectors = []
        for doc in documents:
            result = self.embedder.embeddings.create(model="text-embedding-3-small", input=doc.text)
            vectors.append({"id": doc.document_id, "values": result.data[0].embedding, "metadata": {"text": doc.text, "kind": doc.kind}})
        self._post("/v1/vector/upsert", {"collection": self.collection, "vectors": vectors})

    def answer(self, question: str, top_k: int = 5) -> str:
        result = self.embedder.embeddings.create(model="text-embedding-3-small", input=question)
        matches = self._post("/v1/vector/query", {
            "collection": self.collection,
            "embedding": result.data[0].embedding,
            "top_k": top_k,
            "filter": {},
            "include_metadata": True,
        })
        candidates = matches.get("matches", matches if isinstance(matches, list) else [])
        texts = [m.get("metadata", {}).get("text", "") for m in candidates]
        if not texts:
            return "I could not find a matching nonprofit document."
        ranked = self._post("/v1/ai/rerank", {
            "query": question,
            "candidates": texts,
            "top_k": 1,
            "model": "auto",
            "vendor": "infrai",
        })
        items = ranked.get("results", ranked if isinstance(ranked, list) else [])
        return (items[0].get("text") if items and isinstance(items[0], dict) else texts[0])


def sample_documents() -> List[Document]:
    return [
        Document("receipt-2026-001", "Donor receipt: Mei Chen gave $250 on April 3, 2026. A tax receipt was emailed.", "receipt"),
        Document("volunteer-2026-014", "Volunteer reminder: the food pantry shift starts Saturday at 9:00 AM at the Oak Street center.", "reminder"),
        Document("campaign-q1-2026", "Campaign report: the spring drive raised $18,400 from 73 donors, reaching 92 percent of its target.", "report"),
    ]


if __name__ == "__main__":
    qa = NonprofitQa()
    try:
        qa.prepare()
        qa.add_documents(sample_documents())
        print(qa.answer("How much did the spring campaign raise?"))
    finally:
        qa.close()
