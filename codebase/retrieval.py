"""Truy xuất thông tin từ kênh #thông-báo bằng embedding.

Module này cố tình KHÔNG biết gì về Discord: nó nhận nội dung tin nhắn đã lấy
sẵn (do bot.py lấy) và trả về những đoạn liên quan nhất tới câu hỏi.
Nhờ vậy có thể kiểm thử toàn bộ phần truy xuất mà không cần kết nối Discord.
"""

import json
import math
import os
import re
from dataclasses import dataclass

CACHE_VERSION = 2

# Kích thước mục tiêu của một đoạn, tính bằng ký tự
CHUNK_TARGET = 600
CHUNK_MAX = 1200

# Ký tự emoji ở đầu dòng thường là tiêu đề mục trong thông báo
_EMOJI_HEAD = re.compile(r"^[\U0001F300-\U0001FAFF☀-➿⬀-⯿]")


@dataclass
class Chunk:
    content: str
    message_id: int
    jump_url: str
    section: str
    created_at: str

    def to_dict(self, embedding: list[float] | None = None) -> dict:
        data = {
            "content": self.content,
            "message_id": self.message_id,
            "jump_url": self.jump_url,
            "section": self.section,
            "created_at": self.created_at,
        }
        if embedding is not None:
            data["embedding"] = embedding
        return data


@dataclass
class Match:
    chunk: Chunk
    score: float


# --------------------------------------------------------------------- chia đoạn

NL = chr(10)


def _is_heading_line(line: str) -> bool:
    """Một dòng được coi là tiêu đề mục của thông báo.

    Thông báo mới ghi tiêu đề dính liền nội dung, không có dòng trống ngăn cách,
    nên không thể chỉ dựa vào "khối một dòng" như trước — phải xét từng dòng.
    Tiêu đề trong thông báo luôn viết HOA toàn bộ, còn dòng dữ liệu như
    "🕗 Thời gian: 20:00" thì không.
    """
    s = line.strip()
    if not s or len(s) > 110:
        return False
    if s.startswith("**") and s.endswith("**"):
        return True

    letters = [ch for ch in s if ch.isalpha()]
    if len(letters) < 3:
        return False
    return all(ch.isupper() for ch in letters)


def _cut_long(text: str, limit: int) -> list[str]:
    """Cắt một dòng quá dài, ưu tiên cắt ở cuối dòng cho dễ đọc."""
    parts = []
    while len(text) > limit:
        cut = text.rfind(NL, 0, limit)
        if cut <= 0:
            cut = limit
        parts.append(text[:cut])
        text = text[cut:].lstrip(NL)
    if text.strip():
        parts.append(text)
    return parts


def chunk_announcement(
    content: str, message_id: int, jump_url: str, created_at: str
) -> list[Chunk]:
    """Chia một tin nhắn thông báo thành các đoạn nhỏ, mỗi đoạn thuộc một mục.

    Duyệt theo TỪNG DÒNG thay vì từng khối: gặp dòng tiêu đề thì chốt đoạn trước
    và mở mục mới; đoạn nào dài tới CHUNK_TARGET thì chốt luôn. Nhờ vậy đoạn bám
    sát chủ đề và nhãn mục dùng được để trích dẫn nguồn.
    """
    chunks: list[Chunk] = []
    buf: list[str] = []
    section = "(mở đầu)"

    def flush():
        text = NL.join(buf).strip()
        # Bỏ đoạn vụn (dòng kẻ, ký tự trang trí) — không có gì để tra cứu
        if sum(ch.isalnum() for ch in text) >= 10:
            chunks.append(Chunk(text, message_id, jump_url, section, created_at))
        buf.clear()

    for line in content.split(NL):
        stripped = line.strip()

        if _is_heading_line(stripped):
            flush()
            section = stripped.strip("* ").strip()
            buf.append(stripped)
            continue

        if not stripped:
            if len(NL.join(buf)) >= CHUNK_TARGET:
                flush()
            elif buf:
                buf.append("")
            continue

        for piece in _cut_long(stripped, CHUNK_MAX):
            buf.append(piece)
            if len(NL.join(buf)) >= CHUNK_TARGET:
                flush()

    flush()
    return chunks


# --------------------------------------------------------------------- embedding

def _norm(vec: list[float]) -> float:
    return math.sqrt(sum(x * x for x in vec))


def cosine(a: list[float], b: list[float]) -> float:
    na, nb = _norm(a), _norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return sum(x * y for x, y in zip(a, b)) / (na * nb)


class Retriever:
    """Giữ vector của các đoạn thông báo, tìm đoạn gần nhất với câu hỏi."""

    def __init__(self, session, base_url: str, model: str, cache_path: str):
        self.session = session
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.cache_path = cache_path
        self._chunks: list[Chunk] = []
        self._vectors: list[list[float]] = []
        self._indexed_ids: set[int] = set()

    # -- gọi API embedding -------------------------------------------------

    async def _embed(self, texts: list[str]) -> list[list[float]]:
        async with self.session.post(
            f"{self.base_url}/v1/embeddings",
            json={"model": self.model, "input": texts},
        ) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Embedding HTTP {resp.status}: {(await resp.text())[:200]}")
            data = await resp.json()
        return [item["embedding"] for item in data["data"]]

    # -- cache -------------------------------------------------------------

    def load_cache(self) -> bool:
        if not os.path.exists(self.cache_path):
            return False
        try:
            with open(self.cache_path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            return False
        if data.get("version") != CACHE_VERSION:
            return False

        try:
            self._chunks = [
                Chunk(
                    content=c["content"],
                    message_id=c["message_id"],
                    jump_url=c["jump_url"],
                    section=c["section"],
                    created_at=c["created_at"],
                )
                for c in data["chunks"]
            ]
            self._vectors = [c["embedding"] for c in data["chunks"]]
        except (KeyError, TypeError):
            return False

        self._indexed_ids = {c.message_id for c in self._chunks}
        return True

    def save_cache(self) -> None:
        payload = {
            "version": CACHE_VERSION,
            "chunks": [c.to_dict(v) for c, v in zip(self._chunks, self._vectors)],
        }
        tmp = self.cache_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)
        # đổi tên kiểu nguyên tử để không hỏng cache nếu tiến trình chết giữa đường
        os.replace(tmp, self.cache_path)

    # -- nạp dữ liệu -------------------------------------------------------

    async def add_message(
        self, message_id: int, content: str, jump_url: str, created_at: str, save: bool = True
    ) -> int:
        """Chia đoạn + embed một tin nhắn thông báo. Trả về số đoạn đã thêm.

        `save=False` dùng khi nạp hàng loạt: gọi save_cache() một lần ở cuối
        thay vì ghi đĩa lại sau mỗi tin nhắn.
        """
        if message_id in self._indexed_ids:
            return 0

        chunks = chunk_announcement(content, message_id, jump_url, created_at)
        if not chunks:
            return 0

        vectors = await self._embed([c.content for c in chunks])
        self._chunks.extend(chunks)
        self._vectors.extend(vectors)
        self._indexed_ids.add(message_id)
        if save:
            self.save_cache()
        return len(chunks)

    @property
    def indexed_message_ids(self) -> set[int]:
        return set(self._indexed_ids)

    def reset(self) -> None:
        """Xoá sạch index trong bộ nhớ (chưa ghi đĩa) để nạp lại từ đầu."""
        self._chunks.clear()
        self._vectors.clear()
        self._indexed_ids.clear()

    # -- tìm kiếm ----------------------------------------------------------

    async def search(self, query: str, k: int = 4, min_score: float = 0.25) -> list[Match]:
        """Trả về các đoạn gần với câu hỏi nhất.

        `min_score` CHỈ là sàn chống rác, KHÔNG phải cổng quyết định "có nguồn
        hay không". Đo thực tế trên kênh #thông-báo: câu liên quan đạt
        0.395-0.703 còn câu lạc đề đạt 0.329-0.367 — khoảng cách chỉ 0.028 nên
        không thể tách bằng ngưỡng. Việc quyết định "nguồn có trả lời được câu
        hỏi không" (nút J trong sơ đồ) do LLM đảm nhiệm ở bot.py.
        """
        if not self._chunks:
            return []

        query_vec = (await self._embed([query]))[0]
        scored = [Match(c, cosine(query_vec, v)) for c, v in zip(self._chunks, self._vectors)]
        scored.sort(key=lambda m: -m.score)
        return [m for m in scored[:k] if m.score >= min_score]

    def __len__(self) -> int:
        return len(self._chunks)

    def stats(self) -> dict:
        return {
            "so_doan": len(self._chunks),
            "so_tin_nhan": len(self._indexed_ids),
        }