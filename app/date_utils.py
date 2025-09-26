"""Date utility functions for Project A.N.C.

This module provides common date handling utilities that implement the 3 AM rule:
- Conversations from 00:00-02:59 are considered part of the previous day
- Conversations from 03:00-23:59 are considered part of the current day

This ensures that late-night conversations are grouped with the correct day's activities.
"""

from datetime import datetime, timedelta


def get_log_date(current_time: datetime = None) -> str:
    """Get the appropriate log date based on the 3 AM rule.

    Args:
        current_time (datetime, optional): The current time to check.
                                         If None, uses datetime.now()

    Returns:
        str: Date string in YYYY-MM-DD format for log storage

    Examples:
        # 1:30 AM on 2024-01-02 -> returns "2024-01-01" (previous day)
        # 3:00 AM on 2024-01-02 -> returns "2024-01-02" (current day)
        # 11:30 PM on 2024-01-02 -> returns "2024-01-02" (current day)
    """
    if current_time is None:
        current_time = datetime.now()

    # If the time is between midnight (00:00) and 2:59 AM, use previous day
    if current_time.hour < 3:
        log_date = current_time - timedelta(days=1)
    else:
        log_date = current_time

    return log_date.strftime("%Y-%m-%d")


def get_current_log_date() -> str:
    """Get the current log date based on the 3 AM rule.

    This is a convenience function that calls get_log_date() with the current time.

    Returns:
        str: Date string in YYYY-MM-DD format for log storage
    """
    return get_log_date()