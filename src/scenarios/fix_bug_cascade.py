"""
场景：修 bug 的连带影响 — 修 date_parser 影响依赖旧行为的模块
"""
from pathlib import Path

TEMPLATE_FILES = {
    "src/__init__.py": "",
    "tests/__init__.py": "",
    "src/date_parser.py": '''"""日期解析模块 — 有 bug：不支持 ISO 8601 时区格式"""

from datetime import datetime, timedelta

def parse_date(date_str: str) -> datetime:
    """解析日期字符串（BUG：不支持时区格式如 2025-06-15T14:30:00+08:00）"""
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {date_str}")

def format_date(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")

def days_between(d1: str, d2: str) -> int:
    a = parse_date(d1)
    b = parse_date(d2)
    return abs((b - a).days)

def add_days(date_str: str, days: int) -> str:
    dt = parse_date(date_str)
    return format_date(dt + timedelta(days=days))
'''.strip(),

    "src/event_scheduler.py": '''"""事件调度器 — 依赖 date_parser"""
from src.date_parser import parse_date, format_date

def schedule_event(name: str, date_str: str, duration_days: int) -> dict:
    start = parse_date(date_str)
    from datetime import timedelta
    end = start + timedelta(days=duration_days)
    return {
        "name": name,
        "start": format_date(start),
        "end": format_date(end),
    }

def get_upcoming_events(events: list[dict], today_str: str) -> list:
    today = parse_date(today_str)
    upcoming = []
    for e in events:
        event_date = parse_date(e["start"])
        if event_date >= today:
            upcoming.append(e)
    return upcoming

def is_event_overlapping(e1: dict, e2: dict) -> bool:
    s1 = parse_date(e1["start"])
    e1_end = parse_date(e1["end"])
    s2 = parse_date(e2["start"])
    e2_end = parse_date(e2["end"])
    return s1 < e2_end and s2 < e1_end
'''.strip(),

    "src/report_generator.py": '''"""报表生成器 — 依赖 date_parser 的行为"""
from src.date_parser import parse_date, days_between

def generate_quarterly_report(transactions: list[dict], quarter_start: str, quarter_end: str) -> dict:
    total = 0
    count = 0
    for tx in transactions:
        tx_date = parse_date(tx["date"])
        start = parse_date(quarter_start)
        end = parse_date(quarter_end)
        if start <= tx_date <= end:
            total += tx["amount"]
            count += 1
    return {"total_amount": total, "transaction_count": count}

def calculate_growth(current: str, previous: str) -> float:
    current_days = days_between("2025-01-01", current)
    prev_days = days_between("2025-01-01", previous)
    if prev_days == 0:
        return 0.0
    return (current_days - prev_days) / prev_days
'''.strip(),

    "tests/test_date_parser.py": '''"""日期解析器测试"""
from src.date_parser import parse_date, format_date, days_between, add_days
import pytest

def test_parse_simple_date():
    dt = parse_date("2025-06-15")
    assert dt.year == 2025 and dt.month == 6 and dt.day == 15

def test_parse_datetime():
    dt = parse_date("2025-06-15 14:30")
    assert dt.hour == 14 and dt.minute == 30

def test_parse_full_datetime():
    dt = parse_date("2025-06-15 14:30:00")
    assert dt.second == 0

def test_parse_invalid():
    with pytest.raises(ValueError):
        parse_date("not-a-date")

def test_format_date():
    from datetime import datetime
    dt = datetime(2025, 6, 15)
    assert format_date(dt) == "2025-06-15"

def test_days_between():
    assert days_between("2025-06-01", "2025-06-10") == 9
'''.strip(),

    "tests/test_scheduler.py": '''"""事件调度器测试"""
from src.event_scheduler import schedule_event, get_upcoming_events, is_event_overlapping

def test_schedule_basic():
    e = schedule_event("Meeting", "2025-07-01", 3)
    assert e["name"] == "Meeting"
    assert e["start"] == "2025-07-01"
    assert e["end"] == "2025-07-04"

def test_schedule_full_date():
    e = schedule_event("Workshop", "2025-08-15 09:00", 2)
    assert e["start"] == "2025-08-15"

def test_upcoming_events():
    events = [
        {"name": "Past", "start": "2025-01-01", "end": "2025-01-02"},
        {"name": "Future", "start": "2025-12-25", "end": "2025-12-26"},
    ]
    upcoming = get_upcoming_events(events, "2025-06-15")
    assert len(upcoming) == 1
    assert upcoming[0]["name"] == "Future"

def test_upcoming_empty():
    events = [{"name": "Old", "start": "2025-01-01", "end": "2025-01-02"}]
    upcoming = get_upcoming_events(events, "2025-06-15")
    assert len(upcoming) == 0

def test_overlap_true():
    e1 = {"name": "A", "start": "2025-06-01", "end": "2025-06-10"}
    e2 = {"name": "B", "start": "2025-06-05", "end": "2025-06-15"}
    assert is_event_overlapping(e1, e2)

def test_overlap_false():
    e1 = {"name": "A", "start": "2025-06-01", "end": "2025-06-05"}
    e2 = {"name": "B", "start": "2025-06-06", "end": "2025-06-10"}
    assert not is_event_overlapping(e1, e2)

def test_schedule_multi_day():
    e = schedule_event("Conference", "2025-09-01", 5)
    assert e["end"] == "2025-09-06"
'''.strip(),

    "tests/test_report.py": '''"""报表测试"""
from src.report_generator import generate_quarterly_report, calculate_growth

def test_quarterly_basic():
    txs = [
        {"date": "2025-01-15", "amount": 100},
        {"date": "2025-02-20", "amount": 200},
        {"date": "2025-04-01", "amount": 300},
    ]
    r = generate_quarterly_report(txs, "2025-01-01", "2025-03-31")
    assert r["total_amount"] == 300
    assert r["transaction_count"] == 2

def test_quarterly_empty():
    txs = [{"date": "2025-04-01", "amount": 100}]
    r = generate_quarterly_report(txs, "2025-01-01", "2025-03-31")
    assert r["total_amount"] == 0
    assert r["transaction_count"] == 0

def test_calculate_growth_positive():
    g = calculate_growth("2025-03-01", "2025-02-01")
    assert g > 0

def test_calculate_growth_zero():
    g = calculate_growth("2025-01-01", "2025-01-01")
    assert g == 0.0

def test_quarterly_date_range():
    txs = [
        {"date": "2025-06-15 10:30", "amount": 500},
    ]
    r = generate_quarterly_report(txs, "2025-06-01", "2025-06-30")
    assert r["total_amount"] == 500
'''.strip(),
}


def create_project(target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    for path, content in TEMPLATE_FILES.items():
        f = target_dir / path
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(content, encoding="utf-8")
    return target_dir


SCENARIO_CONFIG = {
    "name": "fix-bug-cascade",
    "description": "修 bug 连带影响 — 修 date_parser 可能影响依赖旧行为的模块",
    "task_prompt": (
        "修复 src/date_parser.py 中的 parse_date 函数，使其支持 ISO 8601 时区格式。\n\n"
        "当前 parse_date 只能解析 \"2025-06-15 14:30:00\" 这样的格式，\n"
        "但不能解析 \"2025-06-15T14:30:00+08:00\" 这样的带时区格式。\n\n"
        "修复后应该能正确解析这两种格式。确保所有测试都通过。"
    ),
    "test_command": "python3 -m pytest tests/ -v --tb=short 2>&1",
    "expected_new_tests": None,
}
