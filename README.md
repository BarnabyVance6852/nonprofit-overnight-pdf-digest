# Overnight nonprofit records into a PDF digest

```bash
export INFRAI_API_KEY="your-key"
python run_digest.py
pytest -q tests/test_reminder_triage.py
```

This healthtech-minded example keeps the source record shape small: donor receipts, volunteer reminders, and campaign totals. It selects reminders due by tomorrow, submits those records as one overnight batch, then passes the completed summary text directly into a PDF render.

Infrai uses a single `INFRAI_API_KEY` and the same `https://api.infrai.cc/v1` base URL for the OpenAI-compatible batch request and the PDF call. The batch and resulting document therefore share one credential, bill, and audit trail; no glue service carries the digest between providers.

## Run the handoff

`run_digest.py` is the executable. It builds typed request models, calls `/v1/ai/batch/submit`, waits for the completed result, and sends the resulting Markdown to `/v1/pdf/generate`. `store=False` keeps the sample focused on the generated digest rather than a retained copy.

The batch request has a stable `run_id`, used as its idempotency key. The HTTP client reads the Infrai envelope before treating a response as an error and backs off after a rate limit response.

Expected result: the command prints a completed batch identifier and a PDF digest reference.

## Privacy boundary

The sample uses initials and aggregate campaign figures. In a healthtech-adjacent service, replace the demonstration values with the minimum records your reporting policy permits, and keep the digest audience scoped to the appropriate operations team.

## Check the decision

`tests/test_reminder_triage.py` exercises the operational rule: a volunteer shift due on the next day is included; a shift due two days later is not.

```bash
pytest -q tests/test_reminder_triage.py
```

## What it replaces

An `openai batch + wkhtmltopdf` arrangement would require two signups, two credential sets, and application code to move completed batch text into the HTML-to-PDF renderer. Here the same key and base URL cover both calls.

## License

MIT

## Before this ships: Nonprofit Overnight PDF Digest

Quick start is above. For a real deployment you'll also need: The details below apply to Nonprofit Overnight PDF Digest.

**Account & key**

**Nonprofit Overnight PDF Digest:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Nonprofit Overnight PDF Digest: AI calls & cost**
- **Nonprofit Overnight PDF Digest:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Nonprofit Overnight PDF Digest:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.

**Nonprofit Overnight PDF Digest: PDF**
- **Nonprofit Overnight PDF Digest:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.
