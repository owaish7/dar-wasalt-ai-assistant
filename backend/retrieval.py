"""Small, inspectable hybrid retriever. No external vector database required."""
import hashlib
import json
import math
import re
import threading
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import numpy as np

EMBED_MODEL = "assessment/multilingual-e5-small-int8"
EMBED_REPO = "Xenova/multilingual-e5-small"
EMBED_FILE = "onnx/model_quantized.onnx"
EMBED_REVISION = "761b726dd34fb83930e26aab4e9ac3899aa1fa78"
ALLOWED_HOSTS = {"darglobal.co.uk", "www.darglobal.co.uk", "wasalt.sa", "www.wasalt.sa"}
STOP = set("the a an and or is are of in to for what which how tell me about does do it its with this that can you more please".split()) | set("ما ماذا هي هو عن في من إلى على هل كيف لي هذه هذا التي الذي و".split())


def tokens(text: str) -> list[str]:
    text = unicodedata.normalize("NFKC", text).lower()
    text = re.sub(r"[\u064b-\u065f\u0670\u0640]", "", text)
    text = re.sub("[أإآ]", "ا", text).replace("ى", "ي")
    return [t for t in re.findall(r"[^\W_]+", text, re.UNICODE) if t not in STOP and len(t) > 1]


def safe_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "https" and parsed.hostname in ALLOWED_HOSTS and not parsed.username and not parsed.password and parsed.port in {None, 443}


@dataclass(frozen=True)
class Passage:
    id: str
    title: str
    url: str
    language: str
    collected_at: str
    text: str
    synthetic: bool
    company: str


def load_corpus(path: Path) -> list[Passage]:
    # JSON permits Unicode paragraph separators inside strings; only LF delimits JSONL.
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").split("\n") if line.strip()]
    if not records or len(records) > 200:
        raise ValueError("Corpus must contain 1–200 documents")
    passages = []
    seen = set()
    for row in records:
        if not safe_url(row["url"]) or row["language"] not in {"en", "ar"} or row["company"] not in {"dar", "wasalt"}:
            raise ValueError("Invalid source metadata")
        if not isinstance(row.get("synthetic"), bool):
            raise ValueError("Corpus must explicitly declare synthetic status")
        if not row["synthetic"] and not row.get("permission_reference"):
            raise ValueError("Real source data requires a permission reference")
        if hashlib.sha256(row["text"].encode()).hexdigest() != row["content_hash"]:
            raise ValueError("Content hash mismatch")
        # Character windows keep Arabic and English bounded, including unspaced inputs.
        text = row["text"][:24000]
        for offset in range(0, len(text), 1000):
            chunk = text[max(0, offset - 150):offset + 1000].strip()
            pid = hashlib.sha256((row["url"] + str(offset) + row["content_hash"]).encode()).hexdigest()[:16]
            if pid in seen:
                continue
            seen.add(pid)
            passages.append(Passage(pid, row["title"], row["url"], row["language"], row["collected_at"], chunk, row["synthetic"], row["company"]))
    return passages


def fingerprint(passages: list[Passage]) -> str:
    return hashlib.sha256("\n".join(p.id + p.text for p in passages).encode()).hexdigest()


class E5Encoder:
    """Direct ONNX inference avoids pulling unrelated image-processing dependencies."""
    def __init__(self, cache: str, allow_download: bool):
        import onnxruntime as ort
        from huggingface_hub import snapshot_download
        from sentencepiece import SentencePieceProcessor

        root = Path(snapshot_download(EMBED_REPO, revision=EMBED_REVISION, cache_dir=cache,
            local_files_only=not allow_download,
            allow_patterns=[EMBED_FILE, "sentencepiece.bpe.model"]))
        # XLM-R uses the SentencePiece vocabulary with a fairseq offset of one.
        # Its JSON tokenizer consumes substantially more memory on startup.
        self.tokenizer = SentencePieceProcessor(model_file=str(root / "sentencepiece.bpe.model"))
        options = ort.SessionOptions()
        options.intra_op_num_threads = 1
        options.inter_op_num_threads = 1
        options.enable_cpu_mem_arena = False
        options.enable_mem_pattern = False
        # Avoid a second cached copy of packed weights on 512 MB free hosts.
        options.add_session_config_entry("session.disable_prepacking", "1")
        self.session = ort.InferenceSession(str(root / EMBED_FILE), sess_options=options, providers=["CPUExecutionProvider"])
        self.inputs = {item.name for item in self.session.get_inputs()}
        self.lock = threading.Lock()

    def embed(self, documents, batch_size=1):
        documents = list(documents)
        for offset in range(0, len(documents), batch_size):
            with self.lock:
                encoded = [self.encode(text) for text in documents[offset:offset + batch_size]]
                width = max(len(ids) for ids in encoded)
                mask = np.array([[1] * len(ids) + [0] * (width - len(ids)) for ids in encoded], dtype=np.int64)
                inputs = {"input_ids": np.array([ids + [1] * (width - len(ids)) for ids in encoded], dtype=np.int64), "attention_mask": mask}
                if "token_type_ids" in self.inputs:
                    inputs["token_type_ids"] = np.zeros_like(mask)
                hidden = self.session.run(None, inputs)[0]
                weighted = hidden * mask[..., None]
                vectors = weighted.sum(axis=1) / np.maximum(mask.sum(axis=1, keepdims=True), 1)
                vectors /= np.maximum(np.linalg.norm(vectors, axis=1, keepdims=True), 1e-12)
            yield from vectors.astype(np.float32)

    def encode(self, text):
        pieces = self.tokenizer.encode(text, out_type=int)
        return [0] + [piece + 1 if piece != 0 else 3 for piece in pieces[:254]] + [2]


def embedding_model(cache: str, allow_download: bool = False):
    return E5Encoder(cache, allow_download)


class Retriever:
    def __init__(self, passages: list[Passage], index_path: Path, mode: str, cache: str):
        self.passages = passages
        self.mode = mode
        self.docs = [Counter(tokens(p.title + " " + p.text)) for p in passages]
        self.lengths = np.array([sum(d.values()) for d in self.docs])
        self.avg_length = max(float(self.lengths.mean()), 1)
        self.df = Counter(t for doc in self.docs for t in doc)
        self.model = None
        self.vectors = None
        if mode == "hybrid":
            with np.load(index_path, allow_pickle=False) as data:
                if str(data["fingerprint"].item()) != fingerprint(passages) or str(data["model"].item()) != EMBED_MODEL:
                    raise ValueError("Index does not match corpus/model; rebuild it")
                self.vectors = data["vectors"].astype(np.float32)
                if self.vectors.shape != (len(passages), 384) or not np.isfinite(self.vectors).all():
                    raise ValueError("Invalid embedding index")
            self.model = embedding_model(cache)
            # Allocate/warm the ONNX session before reporting readiness.
            list(self.model.embed(["query: readiness"], batch_size=1))

    def search(self, question: str, history: list[str], limit=6) -> list[Passage]:
        # Previous user questions retain proper names without trusting assistant facts.
        query = (question + " " + " ".join(history[-2:]))[:4000]
        terms = set(tokens(query))
        lexical = np.zeros(len(self.docs), dtype=np.float32)
        for term in terms:
            df = self.df.get(term, 0)
            if not df:
                continue
            idf = math.log(1 + (len(self.docs) - df + 0.5) / (df + 0.5))
            tf = np.array([d.get(term, 0) for d in self.docs])
            lexical += idf * tf * 2.5 / (tf + 1.5 * (0.25 + 0.75 * self.lengths / self.avg_length))
        scores = np.zeros(len(self.docs))
        lexical_order = np.argsort(-lexical)
        for rank, i in enumerate(lexical_order[:12]):
            if lexical[i] > 0:
                scores[i] += 1 / (60 + rank + 1)
        if self.model is not None:
            vector = next(iter(self.model.embed(["query: " + query], batch_size=1)))
            similarity = self.vectors @ vector
            for rank, i in enumerate(np.argsort(-similarity)[:12]):
                # Similarity is a recall gate, not a probability of correctness.
                if similarity[i] >= 0.78:
                    scores[i] += 1 / (60 + rank + 1)
        # Avoid ambiguous broad queries being dominated by a single long page.
        results, counts = [], Counter()
        for i in np.argsort(-scores):
            p = self.passages[int(i)]
            if scores[i] <= 0 or counts[p.url] >= 2:
                continue
            results.append(p)
            counts[p.url] += 1
            if len(results) == limit:
                break
        return results
