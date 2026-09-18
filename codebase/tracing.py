"""Ghi vết các lượt gọi model — prompt đầu vào và phản hồi thô.

Mục đích: tại CP3/CP4/CP6, người chấm mở file JSONL ra là xác minh được
"có lời gọi AI thật ở quyết định trung tâm" mà không cần tin vào lời kể:

  - `request.prompt` là ĐÚNG chuỗi đã gửi lên API (system + user ghép lại);
  - `response.raw` là ĐÚNG chuỗi model trả về, chưa qua xử lý;
  - `response.parsed` là kết quả sau khi bóc JSON, để đối chiếu xem code có
    suy diễn thêm gì ngoài phản hồi thô hay không;
  - `usage` + `latency_ms` chứng minh thời gian thực, không phải dữ liệu gán cứng.

Mỗi dòng là một lượt gọi, độc lập, thêm vào cuối file nên tiến trình chết
giữa đường cũng không mất các lượt đã ghi.
"""

import json
import os
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class Tracer:
    """Ghi vết ra JSONL. `path=None` thì tắt ghi vết (không lỗi, chỉ là no-op)."""

    def __init__(self, path: str | None = None):
        self.path = path
        self.seq = 0
        if path:
            directory = os.path.dirname(os.path.abspath(path))
            if directory:
                os.makedirs(directory, exist_ok=True)

    @property
    def enabled(self) -> bool:
        return bool(self.path)

    def log_call(
        self,
        *,
        purpose: str,
        model: str,
        system_prompt: str,
        user_prompt: str,
        raw_response: str | None,
        parsed: dict | None,
        latency_ms: int,
        usage: dict | None = None,
        error: str | None = None,
        extra: dict | None = None,
    ) -> dict:
        """Ghi một lượt gọi model. Trả về bản ghi để nơi gọi in ra/kiểm tra."""
        self.seq += 1
        record = {
            "seq": self.seq,
            "ts": _now(),
            "purpose": purpose,
            "model": model,
            "request": {
                "system": system_prompt,
                "user": user_prompt,
            },
            "response": {
                # Phản hồi thô nguyên văn — KHÔNG cắt, để soi được cả phần model
                # viết thừa ngoài JSON nếu có.
                "raw": raw_response,
                "parsed": parsed,
            },
            "latency_ms": latency_ms,
            "usage": usage,
            "error": error,
        }
        if extra:
            record["extra"] = extra

        if self.path:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record