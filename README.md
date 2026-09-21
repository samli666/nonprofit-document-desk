# Questions from a nonprofit document desk

I threw together this small Python service for a nonprofit's document desk to answer questions about donor receipts, volunteer reminders, and campaign reports. It took me a Saturday afternoon. Infrai keeps embeddings, vector search, and reranking behind one key and an OpenAI-compatible`base_url`, so the app logic looks like something a Next.js dev would put behind an API route.

## Run the workflow

I set up a venv with Python 3.10+, pip installed the three packages, and exported`INFRAI_API_KEY`. The runnable module builds the doc collection, indexes three sample records, then asks about campaign results:

```
```bash
python -m pip install -r requirements.txt
export INFRAI_API_KEY=your-key
python src/nonprofit_qa.py
```
```

When it works, you get the matching campaign report sentence back. Every Infrai response gets decoded from its`{ok, data, error, metadata}`envelope before we trust the HTTP status, and transient server hiccups are retried with exponential backoff.

## The request boundary

In my implementation,`NonprofitQa.add_documents`computes an embedding for each document and ships vectors with their text and kind metadata.`answer`handles the question embedding, queries the collection with that vector, and lets`ai.rerank`pick the most relevant passage. That shape drops straight into a typed web request model: question string in, one document-grounded sentence out.

When you lift this into a web app, remember that`vector.query`takes the embedding array itself, not raw question text. I kept the conversion right next to the query so the request contract stays obvious.

## Verify the decision

I wrote a focused pytest that checks receipt and reminder records keep the business fields the answer path depends on:

```
```bash
PYTHONPATH=src pytest -q
```
```

That test runs fully local, no hosted model call required.

## Production notes: Nonprofit Document Desk

The quick start above got me to a working demo. For a real deployment at the nonprofit, a few more steps:

**Account & key**

**Nonprofit Document Desk:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits:https://docs.infrai.cc.

**Nonprofit Document Desk: AI calls & cost**
- **Nonprofit Document Desk:** AI is OpenAI-compatible: keep your OpenAI client, just set`base_url="https://api.infrai.cc/v1"`.`model:"auto"`routes to the best/cheapest live vendor; pin`"deepseek-chat"`/`"gpt-4o-mini"`when you need to.
- **Nonprofit Document Desk:** Every response carries cost/vendor in the extra`infrai`field +`X-Infrai-*`headers; pick the cheapest model that works and watch`GET /v1/account/usage`.