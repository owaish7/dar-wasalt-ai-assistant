# Free Render deployment

The deployment uses a free static site for React and a free Docker web service for FastAPI. [Render's free-tier documentation](https://render.com/docs/free) explains sleep, quota, filesystem and availability limits. No paid instance, database, persistent disk or custom domain is required.

Current engineering preview: [frontend](https://atlas-property-chat-owaish7.onrender.com/) and [backend readiness](https://atlas-property-api-owaish7.onrender.com/healthz). Both run on free services. The content is synthetic; the server-side OpenRouter key has been configured by the owner. Services were connected through the public repository URL without granting Render GitHub account access; after a Git push, use **Manual Deploy → Deploy latest commit** unless you later configure a Blueprint/Git integration.

## Initial fixture deployment

1. Publish the source repository and ensure CI passes. Open Render and choose **New → Blueprint**, using the public repository and its root `render.yaml`. Alternatively create the two services manually with the settings below.
2. Backend: Docker runtime, root `Dockerfile`, **Free** plan, Frankfurt region, health check `/healthz`. Use a unique service name; copy the actual assigned HTTPS backend URL.
3. Set `OPENROUTER_API_KEY` as a secret environment variable, `OPENROUTER_MODEL=google/gemma-4-26b-a4b-it:free` (or leave it unset for that default), `RETRIEVAL_MODE=hybrid`, and `ALLOWED_ORIGINS` to the exact frontend origin. Never put the key in source control or a `VITE_` variable. Avoid reading secrets aloud or capturing them in screenshots.
4. Frontend: Static Site; build command `npm ci --prefix frontend && npm run build --prefix frontend`; publish directory `frontend/dist`; `NODE_VERSION=22.14.0`; `VITE_API_URL` set to the actual backend HTTPS origin. Static hosting is free; do not choose a paid web-service instance for it.
5. Copy the actual frontend origin into the backend's `ALLOWED_ORIGINS`, then redeploy. The frontend environment variable is compiled into the JS bundle; changing it requires a new frontend build.
6. Verify `/healthz` returns `status=ok`, `retrieval=hybrid`, `synthetic=true` and `inference_configured=true`. Verify both languages through the public frontend and test quota/error handling.

The displayed fixture notice is intentional. Do not submit this preview as grounded in real website data.

## Enable approved content

1. Collect and review approved data, build the index and package the bundle as described in the README.
2. In the backend's **Environment → Secret Files**, create `deployment-bundle.json` with the contents of the private bundle. It contains source text and precomputed vectors and must not be committed or pasted into a public issue.
3. Set `CORPUS_BUNDLE_PATH=/etc/secrets/deployment-bundle.json` and redeploy. Startup restores it to the ephemeral runtime directory. On every restart the original secret file restores it again; no persistent disk is needed.
4. The corpus/model fingerprint is validated before readiness. Confirm `synthetic=false` and the source library covers both websites/languages. Test actual content and refresh the evaluation expected facts before submission.

## Speed and resource checks

- The image packages its quantised ONNX model; startup does not fetch model weights from Hugging Face.
- Use one worker. Document embeddings are generated offline, not during chat. Query inference uses one CPU thread; responses are streamed with a small context and a 900-token cap, reasoning disabled, and a request for fewer than 150 words.
- Free-instance RAM is limited. Check actual container memory in CI and Render metrics. Reduce `MAX_CONCURRENT_CHATS` to one if memory pressure appears. Do not silently degrade to English-only embeddings or upgrade to a paid tier.
- Let the backend idle naturally, then test wake-up through the frontend. Polling is bounded to 90 seconds and runs only when a person visits/uses the app.
- No-key, quota, timeout and incomplete-stream errors must remain visible; never serve a canned response as an AI result.
- Do not promise a fixed full-answer speed: free provider latency and cold starts are outside this application's control.

## Rollback and shutdown

Redeploy the last verified commit through Render if a release fails. Revert to fixtures only as an explicitly labelled engineering preview. Remove secrets and delete the services from Render after the assessment if no longer needed. Never enable automatic paid upgrades.
