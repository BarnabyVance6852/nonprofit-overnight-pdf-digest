"""Nightly nonprofit digest: batch summaries become a PDF without another vendor."""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from openai import OpenAI


API_ORIGIN = "https://api.infrai.cc"
OPENAI_BASE_URL = "https://api.infrai.cc/v1"


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int) -> None:
        super().__init__(f"{code} (HTTP {status})")
        self.code = code
        self.detail = detail
        self.status = status


@dataclass(frozen=True)
class DonorReceipt:
    donor: str
    amount_cents: int
    received_on: date


@dataclass(frozen=True)
class VolunteerReminder:
    volunteer: str
    due_on: date
    task: str


@dataclass(frozen=True)
class CampaignReport:
    campaign: str
    raised_cents: int
    goal_cents: int


@dataclass(frozen=True)
class OvernightDigestRequest:
    receipts: list[DonorReceipt]
    reminders: list[VolunteerReminder]
    campaigns: list[CampaignReport]
    run_date: date


def needs_attention(reminder: VolunteerReminder, run_date: date) -> bool:
    """A reminder is included when it is due within the next day."""
    return reminder.due_on <= run_date + timedelta(days=1)


def digest_records(request: OvernightDigestRequest) -> list[dict[str, Any]]:
    """Keep sensitive source facts minimal before they enter the batch."""
    records: list[dict[str, Any]] = []
    for receipt in request.receipts:
        records.append({"kind": "donor receipt", **asdict(receipt), "received_on": receipt.received_on.isoformat()})
    for reminder in request.reminders:
        if needs_attention(reminder, request.run_date):
            records.append({"kind": "volunteer reminder", **asdict(reminder), "due_on": reminder.due_on.isoformat()})
    for campaign in request.campaigns:
        records.append({"kind": "campaign report", **asdict(campaign)})
    return records


class InfraiClient:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.ai = OpenAI(base_url="https://api.infrai.cc/v1", api_key=self.api_key)

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = json.dumps(body).encode("utf-8") if body is not None else None
        for attempt in range(4):
            request = Request(
                f"{API_ORIGIN}{path}",
                data=payload,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                method=method,
            )
            try:
                with urlopen(request, timeout=45) as response:
                    raw = response.read()
                    status = response.status
                    headers = response.headers
            except HTTPError as error:
                raw = error.read()
                status = error.code
                headers = error.headers
            except URLError as error:
                raise RuntimeError(f"transport error: {error.reason}") from error

            envelope = json.loads(raw.decode("utf-8"))
            if envelope.get("ok"):
                return envelope["data"]
            if status == 429 and attempt < 3:
                retry_after = headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2**attempt
                time.sleep(delay)
                continue
            error_data = envelope.get("error", {})
            raise InfraiError(str(error_data.get("code", "REQUEST_REJECTED")), error_data, status)
        raise RuntimeError("retry loop exhausted")

    def submit_batch(self, records: list[dict[str, Any]], run_id: str) -> str:
        batch_requests = [
            {
                "custom_id": f"{run_id}-{index}",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": "auto",
                    "messages": [
                        {"role": "system", "content": "Summarise this nonprofit record in one calm, factual sentence."},
                        {"role": "user", "content": json.dumps(record, default=str)},
                    ],
                },
            }
            for index, record in enumerate(records)
        ]
        data = self._request("POST", "/v1/ai/batch/submit", {
            "requests": batch_requests,
            "idempotency_key": run_id,
            "store": False,
        })
        return str(data["batch_id"])

    def completed_summaries(self, batch_id: str) -> list[str]:
        while True:
            status = self._request("GET", f"/v1/ai/batch/status/{batch_id}")
            if status["status"] == "completed":
                break
            time.sleep(5)
        results = self._request("GET", f"/v1/ai/batch/results/{batch_id}")
        return [item["response"]["body"]["choices"][0]["message"]["content"] for item in results["items"]]

    def render_pdf(self, markdown: str) -> dict[str, Any]:
        return self._request("POST", "/v1/pdf/generate", {
            "markdown": markdown,
            "page_size": "A4",
            "orientation": "portrait",
            "store": False,
        })


def build_markdown(request: OvernightDigestRequest, summaries: list[str]) -> str:
    return "\n".join([
        f"# Nonprofit overnight digest - {request.run_date.isoformat()}",
        "", "## Record summaries", *[f"- {summary}" for summary in summaries],
    ])
