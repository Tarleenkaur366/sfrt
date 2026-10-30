from datetime import date, timedelta
from typing import Tuple

def get_previous_period_dates(start_date: date, end_date: date) -> Tuple[date, date]:
    """
    Computes an equivalent previous date range for period-over-period comparison.
    If period is 30 days (start to end), previous period is the 30 days immediately preceding start.
    """
    days = (end_date - start_date).days + 1
    prev_end = start_date - timedelta(days=1)
    prev_start = prev_end - timedelta(days=days - 1)
    return prev_start, prev_end

def parse_iso_date(date_str: str) -> date:
    return date.fromisoformat(date_str)
