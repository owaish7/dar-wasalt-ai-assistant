# Submission draft and walkthrough

Prepared for the candidate to review and send. Consult `final-review.md` for actual verification results and remaining limitations; this draft has not been emailed.

> Dear Nada,
>
> Please find my completed technical assignment below:
>
> Live application: https://atlas-property-chat-owaish7.onrender.com/
>
> Source repository: https://github.com/owaish7/dar-wasalt-ai-assistant
>
> The application supports English and Arabic questions, retrieves relevant information from the reviewed public Dar Global and Wasalt content snapshot, and provides source citations. It uses a free OpenRouter model, with a Dockerised FastAPI backend and React frontend.
>
> The repository includes setup/deployment instructions, architecture and collection notes, security measures, verification evidence and known free-tier limitations. The backend may take approximately one minute to wake after inactivity.
>
> Best regards,
> Md. Owais

## Interview walkthrough

1. Explain one English and one Arabic question end to end: UI input, request validation, follow-up context, retrieval, evidence prompt, free inference, streaming, validation and final citations.
2. Explain why snapshots keep chats independent of website availability, and how permissions, source timestamps, hashes and index fingerprints preserve provenance.
3. Explain why BM25 plus multilingual semantic retrieval helps names and cross-language questions, and why this small corpus does not require a managed vector database.
4. Show insufficient-evidence, missing-key, quota and interrupted-stream behaviour. Explain why partial drafts are discarded on failures.
5. Explain the distinction between citation validity and factual support. Show human-reviewed evaluation results, including failures.
6. Explain free hosting sleep and model quotas, measured memory/latency, and what would need to change for a production service.
