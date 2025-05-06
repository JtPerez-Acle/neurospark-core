# NeuroSpark Core — **PROMPT v2.1**
*Last updated: 2025‑05‑05*

> **Single source of truth.**
> Check this file into the repo root as `PROMPT.md`.
> Every Agent, script, and contributor must read it **before committing code**.
> Follow Test Driven Development FOR ANY NEW FEATURE.

---

## 1. Mission

Build an **autonomous agentic learning platform**—a "school" of specialised Agents that continuously scout trusted sources, vectorise fresh knowledge, teach humans (or downstream AIs), and *never contaminate themselves with hallucinations*.

---

## 2. Stack Snapshot (⭐⭐ = easy to swap later)

| Layer | Choice | Why / Escape Hatch |
|-------|--------|--------------------|
| **API Surface** | FastAPI + gRPC (`grpclib`) | Python ecosystem, language‑agnostic micro‑services |
| **Vector Search** | **Llama‑Index router** → Qdrant (ANN) *+* ElasticLite (BM25) | Hybrid recall; swap ElasticLite for OpenSearch if needed |
| **Metadata DB** | Postgres 16 (🪶) | ACID, easy local dev |
| **Blob Store** | MinIO (S3‑compat) | Single‑binary, Docker‑friendly |
| **Message Bus** | Redis Streams → migrate to NATS when clustered | Zero config on day 0 |
| **Scraping** | trafilatura (HTML) • pdfminer‑s (PDF) | Stable, Unicode‑safe |
| **LLM Provider** | OpenAI `gpt‑4o` (env `OPENAI_API_KEY`) ⭐ | Can switch to local Llama‑3‑GGUF |
| **Paper / Web APIs** | OpenAlex (scholarly) • NewsAPI • SerpAPI ⭐ | All have Python SDKs |

All services live in `docker-compose.yaml`.
`make dev` = spin everything locally.

---

## 3. Agent Zoo (🧩 = new since v2.0)

| Agent | Core Responsibility | Consumes | Emits |
|-------|--------------------|----------|-------|
| **Curator** | Discover docs (OpenAlex, NewsAPI, SerpAPI) | keywords, RSS | raw docs |
| **Vectoriser** | Clean ➜ chunk ➜ embed | raw docs | vectors (Qdrant) |
| **Professor** | Draft lessons / answers with citations | vectors | markdown drafts |
| **Reviewer** | **Inline grounding**: validates each draft's citations via RAG similarity & factuality | drafts | `approve` / `regenerate` |
| **Tutor** | Converse with users, track mastery | approved lessons | chat msgs |
| **Auditor** | Spot‑check global metrics: relevance, cost, latency | any outputs | audit reports |
| **🧩 Custodian** | **Nightly janitor**: de‑dupe vectors, prune stale/low‑score chunks, rebuild indexes | Qdrant metadata | pruned IDs |
| **Governor** | Enforce MCP rate‑limits, per‑Agent budgets | cost events | throttle cmds |

---

## 4. Grounded‑RAG Pipeline

```
Curator ─┐
├─ Vectoriser ──┐
│ ├─ Professor ──▶ Reviewer ──▶ Tutor
│ │ ▲
Custodian ◀──────────────┘ │
│
Auditor ◀────────────────────────┘
```

* **Reviewer Rules**
  *For each draft paragraph*
  1. Retrieve cited vector chunks by `vector_ids[]`.
  2. Compute
     ```
     faith = rougeL(candidate, source) *
             bertscoreF1(candidate, source)
     ```
  3. `faith ≥ 0.75` → **approve**
     else emit `regenerate` with critique.

* **Custodian Rules**
  *Runs daily 02:00 UTC*
  1. Flag vectors with `last_access > 90 days` **or** `global_relevance < 0.5`.
  2. Soft‑delete duplicates (`cos_sim > 0.97`).
  3. Vacuum Qdrant collections, rebuild HNSW index.

---

## 5. MCP (Modular Capability Pack)

`/mcp/registry.yaml`
```yaml
tools:
  - name: openalex.search
    cost_usd_per_call: 0
    rate_limit_per_min: 60
    auth: none

  - name: openai.chat
    cost_usd_per_1k_tokens: 0.01
    rate_limit_per_min: 3
    auth_env: OPENAI_API_KEY

  - name: grounding.rouge
    cost_usd_per_call: 0
    rate_limit_per_min: 200
    auth: none

  - name: grounding.bertscore
    cost_usd_per_call: 0
    rate_limit_per_min: 100
    auth: none
```

Agents declare required_tools: → Governor enforces budgets & back‑offs.

---

## 6. Relevance Heuristic v1

```cpp
score = 0.4 * embedding_sim
      + 0.3 * log10(citations+1) / 5
      + 0.2 * recency_norm
      + 0.1 * domain_trust
```

Keep if score ≥ 0.7.
Custodian updates domain_trust weekly (whitelist of .edu, journals, etc.).

---

## 7. Milestones & Exit Criteria

| Tag | Must‑Have (tests gated in CI) |
|-----|------------------------------|
| α Ingest | Curator→Vectoriser pipe stores vectors. Unit tests green. |
| β Teach | Professor + Reviewer produce grounded lessons; Reviewer stops ≥ 95 % seeded hallucinations. |
| γ Audit | Auditor false‑negatives ≤ 2 %; Governor kills over‑budget Agents. |
| δ Scale | Custodian nightly job passes; multi‑Cell orchestration; Grafana dashboards alive. |

---

## 8. Quick‑Start

```bash
git clone <repo>
cd neurospark-core
cp .env.example .env        # add your API keys
make dev                    # spins Postgres, Qdrant, Redis, MinIO
pytest -q                   # must be green
```

---

## 9. FAQ (read or repeat the same bugs)

Q: "Why Redis Streams over Kafka/NATS?"
A: Zero‑config for laptops; upgrade path is documented in /docs/migration.md.

Q: "Where do API keys live?"
A: .env file ➜ Docker injects ➜ Governor mounts as secrets.

Q: "What if OpenAI is down?"
A: Set LLM_PROVIDER=local, run make ollama, and Reviewer will still verify against local vectors.
