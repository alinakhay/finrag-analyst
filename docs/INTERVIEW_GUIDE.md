# FinRAG Analyst — interview guide

## The 90-second version

“I built FinRAG Analyst to show the full AI engineering lifecycle around a financial use case. A user asks a question over a 10-K, the FastAPI service retrieves relevant disclosures, and the response contains both a concise answer and the evidence behind every claim. I started with an offline BM25 baseline because it is cheap and measurable, then designed a provider boundary for dense retrieval and a LoRA-adapted generator. The project includes a synthetic training set, parameter-efficient fine-tuning, retrieval evaluation, typed API validation, structured logs, health and metrics endpoints, Docker, CI, and a static React demo. I deliberately did not add Kubernetes: one managed container is the right operational scale here.”

## Demo flow

1. Open on Meridian National Bank and point out the risk categories.
2. Ask “What changed in credit risk?”
3. Show that the answer quantifies the movement from 1.8% to 2.6%.
4. Open the two evidence cards and explain source-level traceability.
5. Switch to Retrieval trace and describe where latency and quality are measured.
6. Change to Helix Payments to show that the dominant risk moves from credit to operations.

## Design decisions to defend

### Why RAG and fine-tuning?

They solve different problems. Retrieval supplies current, document-specific facts. Fine-tuning teaches stable behavior and style: use evidence, quantify changes, cite sources, and abstain when evidence is weak. Fine-tuning is not used as a knowledge database.

### Why a baseline before embeddings?

A lexical baseline is deterministic, fast, and gives the evaluation suite a floor. Financial filings contain exact phrases, ratios, and section names where BM25 performs surprisingly well. Dense retrieval is justified only if it improves held-out metrics enough to pay for model latency and operational complexity.

### Why LoRA?

LoRA freezes the base model and trains small low-rank updates. That reduces trainable parameters and produces a portable adapter. It is appropriate for a portfolio experiment because it demonstrates real adaptation without pretending a tiny dataset warrants full fine-tuning.

### Why separate web and API hosting?

The web build is static and cheap to host on GitHub Pages. The Python service needs a long-running process, so it belongs on a managed container host. This is a simpler and more honest design than trying to force the whole system into static hosting.

### Why no Kubernetes?

There is one stateless API, no demonstrated scale problem, and no multi-service scheduling need. Docker proves portability. Kubernetes would be a future operational choice triggered by traffic, availability, or organizational requirements—not a portfolio checkbox.

## Evaluation story

Start with retrieval metrics because generation quality cannot recover missing context:

- Recall@3: did the correct evidence appear in the top three?
- Mean reciprocal rank: how high did the first correct passage rank?
- Groundedness proxy: how strongly do returned citations match the query?

For the next iteration, add a held-out issuer split and compare:

1. BM25 baseline.
2. Dense bi-encoder retrieval.
3. Hybrid retrieval.
4. Hybrid plus cross-encoder reranking.
5. Base generator versus LoRA adapter on citation and abstention behavior.

## Failure modes

- **Wrong evidence retrieved:** improve chunking, metadata filters, hybrid retrieval, or reranking.
- **Correct evidence, wrong answer:** improve prompt, decoding, training data, or generator choice.
- **Unsupported claim:** block or flag sentences that cannot be linked to a citation.
- **Slow tail latency:** cache embeddings, reduce candidate count, batch rer, and measure each trace step.
- **Distribution shift:** monitor query categories and evaluate new industries and filing formats.

## Good next steps

- Ingest SEC filings through the official submissions/data APIs with rate limiting and a clear user agent.
- Add a Sentence Transformers/Qdrant backend behind the existing retriever interface.
- Track experiments with MLflow or Weights & Biases.
- Add adversarial tests for prompt injection inside documents.
- Deploy the adapter behind vLLM or a managed inference endpoint when traffic justifies it.
