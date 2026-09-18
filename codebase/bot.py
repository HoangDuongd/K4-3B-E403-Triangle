"""Adapter Discord — lớp mỏng nối sự kiện Discord vào module quyết định trung tâm.

File này CHỈ làm ba việc thuộc về Discord:
  1. đăng nhập, dò kênh, nạp thông báo vào index;
  2. quyết định tin nhắn nào đáng trả lời (tag ở #thảo-luận, hoặc DM);
  3. gửi tin trả về, cắt tin dài, và giữ vòng TA xử lý câu hỏi bot đã chuyển.

Toàn bộ phần "trả lời cái gì" nằm ở codebase/decision.py — nhờ vậy
eval/run_eval.py chấm đúng đường code mà bot đang chạy thật.

Chạy:  python -m codebase.bot        (từ gốc repo)
"""

import asyncio
import os
import re
import sys
from collections import defaultdict, deque

import aiohttp
import discord

if __package__ in (None, ""):  # chạy trực tiếp bằng `python codebase/bot.py`
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from codebase.config import (
    AI_BASE_URL,
    AI_MAX_TOKENS,
    AI_MODEL,
    AI_TEMPERATURE,
    AI_THINKING,
    AI_TOKEN,
    ANNOUNCE_CHANNEL,
    BOT_TRACE_PATH,
    CACHE_PATH,
    DISCORD_TOKEN,
    DISCUSS_CHANNEL,
    EMBED_MODEL,
    HISTORY_SIZE,
    SSL_CONTEXT,
    TA_USER_ID,
    TOP_K,
)
from codebase.decision import DecisionEngine, compose_reply
from codebase.retrieval import Retriever
from codebase.tracing import Tracer


def split_message(text: str, limit: int = 1990) -> list[str]:
    """Discord giới hạn 2000 ký tự mỗi tin nhắn nên phải cắt thành nhiều phần."""
    if len(text) <= limit:
        return [text]

    parts = []
    while len(text) > limit:
        cut = text.rfind("\n", 0, limit)
        if cut <= 0:
            cut = limit
        parts.append(text[:cut])
        text = text[cut:].lstrip("\n")
    if text:
        parts.append(text)
    return parts


def strip_bot_mention(content: str, mentions, bot_id: int) -> str:
    """Bỏ tag khỏi câu hỏi trước khi gửi cho AI, để model không nhận được chuỗi <@id>."""
    text = re.sub(rf"<@!?{bot_id}>", " ", content)
    for user in mentions:
        text = re.sub(rf"<@!?{user.id}>", f"@{user.display_name} ", text)
    return text.strip()


# Ngữ cảnh hội thoại theo kênh, và khoá để các lượt trong cùng kênh không chạy chồng nhau
_history: dict[int, deque] = defaultdict(lambda: deque(maxlen=HISTORY_SIZE))
_locks: dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)

# Câu hỏi bot đã chuyển cho TA và đang chờ TA xử lý:
#   _pending[bot_msg_id] = thông tin câu hỏi gốc của học viên
#   _last_pending[channel_id] = bot_msg_id gần nhất, dùng khi TA gõ lệnh mà không reply
_pending: dict[int, dict] = {}
_last_pending: dict[int, int] = {}


class AIBot(discord.Client):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.session: aiohttp.ClientSession | None = None
        self.retriever: Retriever | None = None
        self.engine: DecisionEngine | None = None
        self.announce_channel: discord.abc.Messageable | None = None
        self.discuss_channel: discord.abc.Messageable | None = None
        self._ready_once = False

    async def setup_hook(self):
        # Dùng chung 1 session cho cả bot thay vì mở kết nối mới mỗi lần gọi API.
        # Token đặt ở đây vì Retriever gọi /v1/embeddings qua session này và không
        # tự set header; DecisionEngine set header riêng cho /v1/chat/completions.
        self.session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=SSL_CONTEXT),
            headers={"Authorization": f"Bearer {AI_TOKEN}"},
            timeout=aiohttp.ClientTimeout(total=180),
        )
        self.retriever = Retriever(self.session, AI_BASE_URL, EMBED_MODEL, CACHE_PATH)
        self.retriever.load_cache()
        # Lượt gọi model khi bot chạy thật cũng được ghi vết, cùng định dạng với
        # lượt chấm golden set — cần khi TA xác minh ở CP3/CP5.
        self.engine = DecisionEngine(
            self.session,
            base_url=AI_BASE_URL,
            api_token=AI_TOKEN,
            model=AI_MODEL,
            max_tokens=AI_MAX_TOKENS,
            thinking=AI_THINKING,
            temperature=AI_TEMPERATURE,
            tracer=Tracer(BOT_TRACE_PATH),
        )

    async def close(self):
        if self.session is not None:
            await self.session.close()
        await super().close()

    # -- tìm kênh ----------------------------------------------------------

    def _resolve_channels(self):
        for guild in self.guilds:
            for channel in guild.text_channels:
                if channel.name == ANNOUNCE_CHANNEL:
                    self.announce_channel = channel
                elif channel.name == DISCUSS_CHANNEL:
                    self.discuss_channel = channel

    # -- nạp thông báo vào index -------------------------------------------

    async def load_announcements(self, force: bool = False):
        if self.announce_channel is None:
            print(f"[index] Không tìm thấy kênh #{ANNOUNCE_CHANNEL}")
            return

        try:
            messages = [m async for m in self.announce_channel.history(limit=None)]
        except discord.Forbidden:
            print(f"[index] Không có quyền đọc lịch sử #{ANNOUNCE_CHANNEL}")
            return

        current_ids = {m.id for m in messages if m.content.strip()}
        if (
            not force
            and len(self.retriever)
            and current_ids == self.retriever.indexed_message_ids
        ):
            print(f"[index] Đã đồng bộ: {len(self.retriever)} đoạn từ {len(current_ids)} thông báo.")
            return

        # Có thông báo mới, bị xoá, hoặc bị sửa -> nạp lại từ đầu.
        # Thông báo ít nên nạp lại toàn bộ rẻ hơn nhiều so với việc theo dõi từng thay đổi.
        self.retriever.reset()
        total = 0
        for message in reversed(messages):  # cũ -> mới để index theo đúng thứ tự thời gian
            if not message.content.strip():
                continue
            total += await self.retriever.add_message(
                message.id,
                message.content,
                message.jump_url,
                message.created_at.isoformat(),
                save=False,
            )
        self.retriever.save_cache()
        print(f"[index] Đã nạp {total} đoạn từ {len(current_ids)} thông báo.")

    # -- sự kiện -----------------------------------------------------------

    async def on_ready(self):
        print(f"Bot đã đăng nhập thành công với tên {self.user}")
        print(f"Model: {AI_MODEL} | Embedding: {EMBED_MODEL} | API: {AI_BASE_URL}")

        self._resolve_channels()
        if self._ready_once:
            return
        self._ready_once = True

        await self.load_announcements()
        print(
            f"Chỉ trả lời khi được tag ở #{DISCUSS_CHANNEL} (và trong DM). "
            f"TA khi cần chuyển câu hỏi: {TA_USER_ID}"
        )

    async def _send(self, message, text: str):
        """Gửi phản hồi dạng REPLY vào tin gốc.

        Trong kênh thảo luận đông người, một tin nhắn trơ trọi không cho biết bot
        đang trả lời ai. Reply của Discord tạo liên kết tới tin gốc nên ai đọc
        cũng thấy rõ.

        mention_author=False vì bản thân việc reply đã thông báo cho người hỏi rồi,
        thêm @mention chỉ làm nhiễu kênh.
        """
        parts = split_message(text)
        first: discord.Message | None = None
        for index, part in enumerate(parts):
            if index == 0:
                try:
                    first = await message.reply(part, mention_author=False)
                    continue
                except discord.HTTPException:
                    # Tin gốc đã bị xoá thì không reply được -> gửi bình thường
                    pass
            sent = await message.channel.send(part)
            if first is None:
                first = sent
        return first

    # -- TA ra lệnh --------------------------------------------------------

    def _pending_target(self, message) -> tuple[int, dict | None]:
        """Tìm câu hỏi đang chờ mà TA đang nói tới.

        Ưu tiên chuỗi reply: TA reply thẳng vào tin bot đã chuyển câu hỏi. Nếu TA
        gõ lệnh trống không thì lấy câu hỏi được chuyển gần nhất trong kênh.
        """
        ref = message.reference
        if ref is not None and ref.message_id in _pending:
            return ref.message_id, _pending[ref.message_id]

        last = _last_pending.get(message.channel.id)
        if last is not None and last in _pending:
            return last, _pending[last]

        return 0, None

    async def handle_ta_message(self, message, text: str) -> bool:
        """Xử lý tin nhắn của TA. True = đã xử lý xong, không đi tiếp luồng hỏi đáp."""
        bot_msg_id, target = self._pending_target(message)

        try:
            verdict = await self.engine.classify_ta(text, target)
        except Exception as exc:
            print(f"[LỖI TA] {type(exc).__name__}: {exc}")
            return False

        intent = verdict["intent"]

        if intent == "question":
            return False  # TA hỏi bình thường -> rơi xuống luồng hỏi đáp chung

        if intent == "unclear":
            await self._send(
                message, verdict["reply"] or "Bạn muốn mình làm gì với câu hỏi này?"
            )
            return True

        if not target:
            await self._send(
                message, "Mình chưa thấy câu hỏi nào đang chờ bạn xử lý."
            )
            return True

        reply = verdict["reply"]
        if intent == "refuse" and not reply:
            reply = "Câu hỏi này mình chưa có thông tin chính thức, bạn thông cảm nhé."
        if intent == "relay" and not reply:
            await self._send(message, "Bạn cho mình nội dung cần gửi tới học viên nhé.")
            return True

        # Gửi tới học viên, reply đúng vào câu hỏi gốc của họ
        try:
            partial = message.channel.get_partial_message(target["student_msg_id"])
            await partial.reply(reply, mention_author=False)
        except Exception as exc:
            print(f"[LỖI TA] không gửi được cho học viên: {type(exc).__name__}: {exc}")
            await self._send(message, "Mình không gửi được cho học viên đó.")
            return True

        # Câu hỏi đã xử lý xong -> bỏ khỏi danh sách chờ
        _pending.pop(bot_msg_id, None)
        if _last_pending.get(message.channel.id) == bot_msg_id:
            _last_pending.pop(message.channel.id, None)

        action_label = "từ chối" if intent == "refuse" else "trả lời"
        await self._send(message, f"Mình đã {action_label} giúp bạn rồi nhé.")
        print(f"[TA] {message.author.display_name}: {text[:50]!r} -> {intent}")
        return True

    async def on_message(self, message):
        # Bỏ qua tin nhắn của chính bot và của bot khác để tránh vòng lặp vô hạn
        if message.author.bot or not message.content.strip():
            return

        # Thông báo mới ở #thông-báo: nạp vào index rồi thôi, không trả lời
        if self.announce_channel is not None and message.channel.id == self.announce_channel.id:
            try:
                added = await self.retriever.add_message(
                    message.id,
                    message.content,
                    message.jump_url,
                    message.created_at.isoformat(),
                )
                if added:
                    print(f"[index] +{added} đoạn từ thông báo mới {message.id}")
            except Exception as exc:
                print(f"[LỖI index] {type(exc).__name__}: {exc}")
            return

        is_dm = isinstance(message.channel, discord.DMChannel)
        mentioned = any(u.id == self.user.id for u in message.mentions)

        if not mentioned and not is_dm:
            return

        # Chỉ trả lời ở #thảo-luận hoặc DM — không chen vào kênh khác
        if not is_dm and (
            self.discuss_channel is None or message.channel.id != self.discuss_channel.id
        ):
            return

        text = strip_bot_mention(message.content, message.mentions, self.user.id)
        if not text:
            return

        # Giữ trạng thái "đang nhập..." trong lúc tra cứu và chờ model
        # TA có quyền ra lệnh cho bot (từ chối / trả lời thay học viên) thay vì bị
        # coi như một học viên đang đặt câu hỏi. handle_ta_message trả về False khi
        # TA thật sự đang hỏi, lúc đó rơi xuống luồng hỏi đáp bên dưới.
        if TA_USER_ID and message.author.id == TA_USER_ID:
            async with _locks[message.channel.id]:
                async with message.channel.typing():
                    if await self.handle_ta_message(message, text):
                        return

        async with _locks[message.channel.id]:
            async with message.channel.typing():
                try:
                    matches = await self.retriever.search(text, k=TOP_K)
                    history = list(_history[message.channel.id])
                    decision = await self.engine.decide(text, matches, history)
                except asyncio.TimeoutError:
                    await self._send(
                        message, "Xin lỗi, mình phản hồi quá lâu. Bạn thử lại giúp mình nhé."
                    )
                    return
                except Exception as exc:
                    print(f"[LỖI] {type(exc).__name__}: {exc}")
                    await self._send(message, "Xin lỗi, mình đang gặp lỗi khi tra cứu.")
                    return

        reply = compose_reply(decision, matches, TA_USER_ID)
        if not reply:
            return

        sent = await self._send(message, reply)

        # Ghi lại câu hỏi vừa chuyển cho TA, để sau đó TA có thể ra lệnh
        # "từ chối" hoặc "trả lời thay" cho đúng câu hỏi này.
        if decision["action"] == "escalate" and sent is not None:
            _pending[sent.id] = {
                "student_msg_id": message.id,
                "student_name": message.author.display_name,
                "question": text,
            }
            _last_pending[message.channel.id] = sent.id

        _history[message.channel.id].append(f"Học viên: {text}")
        _history[message.channel.id].append(f"Trợ lý: {decision['reply']}")
        # Ghi cả câu hỏi: khi vận hành cần biết học viên đã hỏi gì mà bot trả lời như vậy
        print(
            f"[{message.channel}] {message.author.display_name}: {text[:60]!r} "
            f"-> ({decision['action']}) {decision['reply'][:60]!r}"
        )


if __name__ == "__main__":
    missing = [
        name
        for name, value in {"DISCORD_TOKEN": DISCORD_TOKEN, "AUTH_TOKEN": AI_TOKEN}.items()
        if not value
    ]
    if missing:
        raise SystemExit(
            f"Lỗi: thiếu cấu hình trong file .env: {', '.join(missing)}\n"
            "Mở file .env trong thư mục dự án và điền các biến còn thiếu."
        )

    intents = discord.Intents.default()
    intents.message_content = True

    bot = AIBot(intents=intents)
    bot.run(DISCORD_TOKEN, log_handler=None)