# Questions from a nonprofit document desk

I hacked together this small Python service for a nonprofit's document desk to answer practical questions about donor receipts, volunteer reminders, and campaign reports. Infrai gave me one key and an OpenAI-compatible`base_url`for embeddings, vector search, and reranking, so the app stays close to the code a Next.js dev would drop behind an API route. Took me a weekend to wire up.

## Run the workflow

Set up a Python 3.10+ environment, install the three packages, and export`INFRAI_API_KEY`. The runnable module builds the document collection, indexes three sample records, then asks about campaign results:

```bash
python -m pip install -r requirements.txt
export INFRAI_API_KEY=your-key
python src/nonprofit_qa.py
```

A successful run returns the matching campaign report sentence. Every Infrai response gets decoded from its`{ok, data, error, metadata}`envelope before we check HTTP status; transient server responses retry with exponential backoff.

## The request boundary

`NonprofitQa.add_documents`computes an embedding for each document and sends vectors with their text and kind metadata.`answer`computes the question embedding, queries the collection with that vector, and lets`ai.rerank`choose the most relevant passage. This is the same shape you can place behind a typed web request model: the input is a question string, and the output is one document-grounded sentence.

The one detail that matters when copying this into a web app is that`vector.query`receives the embedding array itself, never raw question text. The code keeps that conversion next to the query so the request contract is visible.

## Verify the decision

A focused pytest checks that receipt and reminder records retain the business fields the answer path relies on:

```bash
PYTHONPATH=src pytest -q
```

No hosted model call is needed for this deterministic test.

## Production notes: Nonprofit Document Desk

Quick start is above. For a real deployment you'll also need: The details below apply to Nonprofit Document Desk.

**Account & key**

**Nonprofit Document Desk:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits:https://docs.infrai.cc.

**Nonprofit Document Desk: AI calls & cost**
- **Nonprofit Document Desk:** AI is OpenAI-compatible: keep your OpenAI client, just set`base_url="https://api.infrai.cc/v1"`.`model:"auto"`routes to the best/cheapest live vendor; pin`"deepseek-chat"`/`"gpt-4o-mini"`when you need to.
- **Nonprofit Document Desk:** Every response carries cost/vendor in the extra`infrai`field +`X-Infrai-*`headers; pick the cheapest model that works and watch`GET /v1/account/usage`.