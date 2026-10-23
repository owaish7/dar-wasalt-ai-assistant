"""Runtime configuration. Never expose this object through the API."""
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    api_key: str = field(default_factory=lambda: os.getenv("OPENROUTER_API_KEY", ""))
    model: str = field(default_factory=lambda: os.getenv("OPENROUTER_MODEL", "google/gemma-4-26b-a4b-it:free"))
    corpus_path: Path = field(default_factory=lambda: Path(os.getenv("CORPUS_PATH", "data/fixtures/corpus.jsonl")))
    index_path: Path = field(default_factory=lambda: Path(os.getenv("INDEX_PATH", "data/fixtures/index.npz")))
    retrieval_mode: str = field(default_factory=lambda: os.getenv("RETRIEVAL_MODE", "lexical"))
    embedding_cache: str = field(default_factory=lambda: os.getenv("EMBEDDING_CACHE", ".cache/fastembed"))
    origins: tuple[str, ...] = field(default_factory=lambda: tuple(x.strip() for x in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",") if x.strip()))
    rate_limit: int = field(default_factory=lambda: int(os.getenv("RATE_LIMIT_PER_MINUTE", "8")))
    max_concurrency: int = field(default_factory=lambda: int(os.getenv("MAX_CONCURRENT_CHATS", "2")))

    def __post_init__(self):
        if self.retrieval_mode not in {"lexical", "hybrid"}:
            raise ValueError("RETRIEVAL_MODE must be lexical or hybrid")
        if "*" in self.origins:
            raise ValueError("Use explicit ALLOWED_ORIGINS")
        if not 1 <= self.rate_limit <= 60 or not 1 <= self.max_concurrency <= 4:
            raise ValueError("Invalid request/concurrency limits")
