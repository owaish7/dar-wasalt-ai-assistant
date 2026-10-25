# Atlas — Dar Global & Wasalt Chatbot

Ask questions about Dar Global projects and Wasalt property services in English or Arabic. Answers use collected website information and include clickable references, with source details collapsed below each answer.

**[Open the live demo](https://atlas-property-chat-owaish7.onrender.com/)** · **[View test runs](https://github.com/owaish7/dar-wasalt-ai-assistant/actions)**

The free backend may take around a minute to wake after inactivity. Free model quotas can also affect availability.

## Architecture, simply explained

```text
Website pages → Clean text → Searchable passages
                                    ↓
User question → FastAPI → Find relevant passages → OpenRouter model
                                                      ↓
React chatbot ← Answer with checked source references
```

1. **React + TypeScript** provides the chat interface, English/Arabic selection and right-to-left Arabic layout.
2. **FastAPI** receives the question and recent conversation, checks the input and limits requests.
3. **Search** finds up to six relevant passages. It combines keyword matching (BM25) with meaning-based search (multilingual E5-small).
4. **OpenRouter** receives those passages and is instructed to answer only from them, ask for clarification when needed, and decline unrelated or unsupported requests.
5. **The backend checks citation numbers** against the supplied passages. The interface displays the answer and links to its sources. Invalid or interrupted responses produce an honest fallback or error.

This approach is called **retrieval-augmented generation (RAG)**: find relevant information first, then give it to the model. The model is not trained on the websites. Pages are collected in advance, so chatting does not trigger scraping. A small local search index avoids needing a separate database.

## How the data was collected

The current snapshot has **68 pages: 55 Dar Global and 13 Wasalt**, split into 310 searchable passages. It includes selected projects, company information, services, FAQs, news, property guides and three dated Wasalt listing examples.

- A shared Python scraper handles both websites with separate URL lists. It checks allowed domains, robots rules and redirects, spaces requests, and stops on repeated access denials.
- Some pages were collected through normal browser navigation and visible FAQ expansion when direct HTTP collection was denied. Browser import scripts process those captures; no access challenge was bypassed.
- Cleaning removes navigation, unrelated project cards, duplicates and contact details. Each record keeps its source URL, title, language, collection date and content hash.
- The collected text and index stay private. The public repository includes the [source URL list](data/reviewed-source-manifest.json), collection scripts and clearly labelled fictional fixtures for local setup.

This is a selected snapshot, not every page or live property inventory. Collection records the candidate's assumed assessment authorization; no separate website licence is claimed. See [collection details](docs/collection.md) and [coverage](docs/expanded-source-coverage.md).

## Model choice

The primary model is `cohere/north-mini-code:free`, with `poolside/laguna-s-2.1:free` as a free backup. These were selected after trials with free OpenRouter models. The server checks that configured models have zero listed usage pricing and records the model actually used. There is no paid fallback.

Free-model quality varies, especially for Arabic. Citation checks verify source references, not the truth of every sentence. Evaluation findings and remaining issues are documented in the [verification report](docs/final-review.md).

## Run locally

Requires **Python 3.12** and **Node.js 22.14+ within Node 22**. Commands below use PowerShell.

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r backend/requirements.txt
Copy-Item .env.example .env
# Add OPENROUTER_API_KEY to .env. Never commit it.
.venv\Scripts\python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Open `http://localhost:5173`. A clean checkout uses **fictional demo data and keyword search**, not the private live dataset. An OpenRouter key is required for generated answers.

To enable meaning-based search locally, run `.venv\Scripts\python -m scripts.build_index`, set `RETRIEVAL_MODE=hybrid` in `.env`, and restart the backend. This downloads the pinned embedding model and builds the search index. On macOS/Linux, use `.venv/bin/python` and `cp` instead.

## Docker and deployment

```sh
docker build -t atlas-assistant .
docker run --rm -p 8000:8000 --env-file .env -e RETRIEVAL_MODE=hybrid -e EMBEDDING_CACHE=/opt/models atlas-assistant
```

Docker packages the **backend**, search model and fixture index. The frontend is built separately.

The live app uses a Render Free Static Site for React and a Render Free Web Service for the Docker backend. Set `VITE_API_URL` to the backend URL and `ALLOWED_ORIGINS` to the frontend URL. Add the OpenRouter key as a backend environment secret. The real dataset and index are restored from a private Render secret file on startup.

See [step-by-step deployment instructions](docs/deployment.md) for the private bundle and hosting configuration.

## Security

- API keys stay on the server; credentials and collected text are excluded from public Git and Docker images.
- Input size, history, request rate, concurrent requests and response time are limited.
- Website content and chat history are treated as untrusted input, not instructions.
- Model text is rendered without executing HTML. Citation links use approved HTTPS source domains.
- Missing keys, quota exhaustion and interrupted answers produce visible errors. The app never silently switches to paid inference.

## Testing and AI-assisted code verification

AI assisted with implementation, tests and documentation. Review focused on data attribution, safe links, secrets, free-only inference, streaming failures and bilingual retrieval.

**50 backend tests and nine frontend tests passed locally.** GitHub Actions also checks the frontend build, dependencies, Docker startup and container restart.

```powershell
.venv\Scripts\python -m unittest discover -s tests -v
npm --prefix frontend test
npm --prefix frontend run build
```

A 40-question English/Arabic live evaluation completed and exposed model errors that informed later fixes. Follow-up checks found remaining Arabic reliability issues; a final 90% accuracy score is **not claimed**. The [verification report](docs/final-review.md) separates completed checks from pending ones.

## Further details

- [Assignment requirement checklist and verification](docs/final-review.md)
- [Architecture and implementation walkthrough](docs/assignment-notes.md)
- [Data collection](docs/collection.md) and [source coverage](docs/expanded-source-coverage.md)
- [Deployment guide](docs/deployment.md)
- [Evaluation procedure](docs/evaluation.md)

The demo uses dated source snapshots and does not provide live inventory or booking. Free-host sleep, provider quotas and occasional model errors remain practical limitations.
