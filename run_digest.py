"""Submit the overnight digest and render its completed batch into a PDF."""

from datetime import date, timedelta

from src.nonprofit_digest import (
    CampaignReport,
    DonorReceipt,
    InfraiClient,
    OvernightDigestRequest,
    VolunteerReminder,
    build_markdown,
    digest_records,
)


def main() -> None:
    today = date.today()
    request = OvernightDigestRequest(
        receipts=[DonorReceipt("A. Donor", 12500, today)],
        reminders=[VolunteerReminder("M. Volunteer", today + timedelta(days=1), "Confirm Saturday shift")],
        campaigns=[CampaignReport("Winter pantry", 64000, 100000)],
        run_date=today,
    )
    client = InfraiClient()
    run_id = f"nonprofit-digest-{today.isoformat()}"
    batch_id = client.submit_batch(digest_records(request), run_id)
    summaries = client.completed_summaries(batch_id)
    pdf = client.render_pdf(build_markdown(request, summaries))
    print(f"Batch {batch_id} completed; PDF digest: {pdf.get('url', pdf.get('pdf_id'))}")


if __name__ == "__main__":
    main()
