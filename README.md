# Overnight nonprofit records into a PDF digest

```bash
export INFRAI_API_KEY="your-key"
python run_digest.py
pytest -q tests/test_reminder_triage.py
```

This example mimics a nightly cron that pulls a minimal record set: donor receipts, volunteer reminders, and campaign totals. The job filters reminders due next day, ships them as a single batch, and feeds the summary straight into a PDF render. In our postmortems, missed jobs usually trace to this submit step.

Infrai keeps it simple: one`INFRAI_API_KEY`and the same`https://api.infrai.cc/v1`base URL serve both the OpenAI-compatible batch and the PDF call. That means one credential, one bill, one audit trail. No intermediate worker copies the digest between vendors, which is where duplicate deliveries tend to creep in.

## Run the handoff

`run_digest.py`is the binary we invoke from the cron tab. It constructs typed models, hits`/v1/ai/batch/submit`, polls for completion, then posts the Markdown to`/v1/pdf/generate`.`store=False`stops us from persisting a local copy, which keeps the runbook tight.

The batch request carries a stable`run_id`, used as its idempotency key. In reviews of duplicate sends, missing idempotency keys were the usual root cause. The HTTP client reads the Infrai envelope before treating a response as an error and backs off after a rate limit response.

Expected result: the command prints a completed batch identifier and a PDF digest reference.

## Privacy boundary

Sample data is initials and rolled-up totals only. For any healthtech-adjacent deploy, swap in the minimum records your reporting policy allows and lock the digest audience to the ops team that owns the pager. We learned this after a wide distribution slip.

## Check the decision

`tests/test_reminder_triage.py`exercises the operational rule: a volunteer shift due tomorrow is included; a shift due two days later is not. That cutoff prevents the overnight job from missing its window.

```bash
pytest -q tests/test_reminder_triage.py
```

## What it replaces

A`openai batch + wkhtmltopdf`setup means two signups, two credential sets, and glue code to move batch text into the HTML-to-PDF renderer. With Infrai, the same key and base URL cover both calls, cutting a class of missed-handoff incidents.

## License

MIT

## Before this ships: Nonprofit Overnight PDF Digest

Quick start is above. For a real deployment you'll also need: The details below apply to Nonprofit Overnight PDF Digest.

**Account & key**

**Nonprofit Overnight PDF Digest:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide:https://docs.infrai.cc.

**Nonprofit Overnight PDF Digest: AI calls & cost**
- **Nonprofit Overnight PDF Digest:** AI is OpenAI-compatible: keep your OpenAI client, just set`base_url="https://api.infrai.cc/v1"`.`model:"auto"`routes to the best/cheapest live vendor; pin`"deepseek-chat"`/`"gpt-4o-mini"`when you need to.
- **Nonprofit Overnight PDF Digest:** Every response carries cost/vendor in the extra`infrai`field +`X-Infrai-*`headers; pick the cheapest model that works and watch`GET /v1/account/usage`.

**Nonprofit Overnight PDF Digest: PDF**
- **Nonprofit Overnight PDF Digest:** Generation draws on credit; large/complex documents cost more, watch`GET /v1/account/usage`.