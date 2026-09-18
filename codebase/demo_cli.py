"""Chạy một câu hỏi qua đúng đường code của sản phẩm, ngay trong terminal.

Dùng để quay video thao tác 30 giây ở CP3: người dùng gõ câu hỏi, thấy hệ thống
truy xuất nguồn, gọi model thật, và in ra phản hồi thô kèm thời gian — không cần
dựng Discord, không có gì gán cứng sẵn.

    python -m codebase.demo_cli "mấy giờ workshop tối nay?"

Không truyền câu hỏi thì chương trình hỏi từng câu một cho tới khi gõ trống.
"""

import asyncio
import json
import os
import sys
import time

import aiohttp

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from codebase.config import (
    AI_BASE_URL,
    AI_MAX_TOKENS,
    AI_MODEL,
    AI_TEMPERATURE,
    AI_THINKING,
    AI_TOKEN,
    BASE_DIR,
    CACHE_PATH,
    EMBED_MODEL,
    SSL_CONTEXT,
    TA_USER_ID,
    TOP_K,
)
from codebase.decision import DecisionEngine, compose_reply
from codebase.retrieval import Retriever
from codebase.tracing import Tracer

SNAPSHOT = os.path.join(BASE_DIR, "eval", "corpus", "announcements.json")


async def ensure_index(retriever: Retriever) -> str:
    """Nạp index từ cache; cache chưa có thì dựng từ corpus trong eval/."""
    if retriever.load_cache():
        return "cache .rag_cache.json"

    with open(SNAPSHOT, encoding="utf-8") as f:
        snapshot = json.load(f)
    for message in snapshot["messages"]:
        await retriever.add_message(
            message["message_id"],
            message["content"],
            message.get("jump_url", ""),
            message["created_at"],
            save=False,
        )
    retriever.save_cache()
    return "corpus eval/corpus/announcements.json"


async def answer_once(session, retriever, engine, question: str) -> None:
    print("\n" + "=" * 72)
    print(f"CÂU HỎI: {question}")
    print("=" * 72)

    matches = await retriever.search(question, k=TOP_K)
    print(f"\n[1] Truy xuất — {len(matches)} đoạn liên quan nhất:")
    for i, m in enumerate(matches):
        print(f"    [{i}] {m.score:.3f} | {m.chunk.section[:52]}")

    print(f"\n[2] Gọi model thật: {AI_MODEL} @ {AI_BASE_URL}")
    started = time.perf_counter()
    decision = await engine.decide(question, matches, [])
    elapsed = time.perf_counter() - started

    print(f"    xong sau {elapsed:.2f}s | action = {decision['action']} "
          f"| sources = {decision['sources']}")

    print("\n[3] Tin nhắn bot gửi học viên:")
    print("-" * 72)
    print(compose_reply(decision, matches, TA_USER_ID))
    print("-" * 72)


async def main() -> None:
    if not AI_TOKEN:
        raise SystemExit("Thiếu AUTH_TOKEN trong .env — không gọi được model.")

    trace = Tracer(os.path.join(BASE_DIR, "logs", "demo_cli.jsonl"))
    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(ssl=SSL_CONTEXT),
        timeout=aiohttp.ClientTimeout(total=180),
    ) as session:
        retriever = Retriever(session, AI_BASE_URL, EMBED_MODEL, CACHE_PATH)
        source = await ensure_index(retriever)
        print(f"[index] {len(retriever)} đoạn, nạp từ {source}")

        engine = DecisionEngine(
            session,
            base_url=AI_BASE_URL,
            api_token=AI_TOKEN,
            model=AI_MODEL,
            max_tokens=AI_MAX_TOKENS,
            thinking=AI_THINKING,
            temperature=AI_TEMPERATURE,
            tracer=trace,
        )

        questions = sys.argv[1:]
        if questions:
            for q in questions:
                await answer_once(session, retriever, engine, q)
        else:
            print("Gõ câu hỏi rồi Enter (gõ trống để thoát).")
            while True:
                try:
                    q = input("\n> ").strip()
                except (EOFError, KeyboardInterrupt):
                    break
                if not q:
                    break
                await answer_once(session, retriever, engine, q)

    print(f"\n[ghi vết] {trace.path}")


if __name__ == "__main__":
    asyncio.run(main())