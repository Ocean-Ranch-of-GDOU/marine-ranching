from datetime import datetime


def iso_now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def chart_time_label(include_seconds: bool = False) -> str:
    return datetime.now().strftime("%H:%M:%S" if include_seconds else "%H:%M")
