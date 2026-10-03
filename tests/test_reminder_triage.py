from datetime import date, timedelta

from src.nonprofit_digest import VolunteerReminder, needs_attention


def test_next_day_volunteer_shift_is_included_in_the_digest() -> None:
    run_date = date(2026, 9, 15)
    due_tomorrow = VolunteerReminder("J. Chen", run_date + timedelta(days=1), "Call food bank")
    later_shift = VolunteerReminder("J. Chen", run_date + timedelta(days=2), "Prepare labels")

    assert needs_attention(due_tomorrow, run_date) is True
    assert needs_attention(later_shift, run_date) is False
