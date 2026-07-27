"""
场景：接口重构 — 改 get_user 签名导致调用点全部挂掉
"""
from pathlib import Path

TEMPLATE_FILES = {
    "src/__init__.py": "",
    "tests/__init__.py": "",
    "src/user_service.py": '''"""用户服务"""

class UserService:
    def __init__(self):
        self._users = {
            1: {"id": 1, "name": "Alice", "email": "alice@example.com", "deleted": False},
            2: {"id": 2, "name": "Bob", "email": "bob@example.com", "deleted": True},
            3: {"id": 3, "name": "Charlie", "email": "charlie@example.com", "deleted": False},
        }

    def get_user(self, user_id: int) -> dict | None:
        """获取用户（应改为 get_user(user_id, include_deleted=False)）"""
        return self._users.get(user_id)

    def list_active_users(self) -> list:
        return [u for u in self._users.values() if not u["deleted"]]
'''.strip(),

    "src/order_service.py": '''"""订单服务 — 依赖 user_service.get_user()"""
from src.user_service import UserService

_service = UserService()

def get_user_orders(user_id: int) -> list:
    user = _service.get_user(user_id)
    if user is None:
        raise ValueError(f"User {user_id} not found")
    return [{"order_id": 100 + user_id, "item": "Widget"}]

def get_order_summary(user_id: int) -> str:
    user = _service.get_user(user_id)
    name = user["name"]
    return f"Orders for {name}"
'''.strip(),

    "src/report_service.py": '''"""报表服务 — 依赖 user_service.get_user()"""
from src.user_service import UserService

_service = UserService()

def generate_user_report(user_id: int) -> dict:
    user = _service.get_user(user_id)
    if user is None:
        return {"error": "User not found"}
    return {"user": user["name"], "email": user["email"]}
'''.strip(),

    "src/admin_panel.py": '''"""管理面板 — 依赖 user_service.get_user()"""
from src.user_service import UserService

_service = UserService()

def get_user_details(user_id: int) -> str:
    user = _service.get_user(user_id)
    if user is None:
        return "Unknown user"
    return f"{user['name']} <{user['email']}>"
'''.strip(),

    "tests/test_user.py": '''"""用户服务测试"""
from src.user_service import UserService

def test_get_user_exists():
    svc = UserService()
    u = svc.get_user(1)
    assert u is not None
    assert u["name"] == "Alice"

def test_get_user_not_found():
    svc = UserService()
    assert svc.get_user(999) is None

def test_get_user_deleted():
    svc = UserService()
    u = svc.get_user(2)
    assert u is not None
    assert u["deleted"] is True

def test_list_active_users():
    svc = UserService()
    active = svc.list_active_users()
    assert len(active) == 2
    assert all(not u["deleted"] for u in active)

def test_get_user_returns_dict():
    svc = UserService()
    u = svc.get_user(1)
    assert isinstance(u, dict)
    assert "id" in u
    assert "name" in u
    assert "email" in u

def test_get_user_has_deleted_flag():
    svc = UserService()
    u = svc.get_user(1)
    assert "deleted" in u

def test_get_user_id_2_exists():
    svc = UserService()
    assert svc.get_user(2) is not None

def test_get_user_id_3():
    svc = UserService()
    u = svc.get_user(3)
    assert u["name"] == "Charlie"
'''.strip(),

    "tests/test_order.py": '''"""订单服务测试"""
from src.order_service import get_user_orders, get_order_summary

def test_get_orders_valid():
    orders = get_user_orders(1)
    assert len(orders) == 1
    assert orders[0]["item"] == "Widget"

def test_get_orders_invalid():
    try:
        get_user_orders(999)
        assert False, "Should have raised"
    except ValueError:
        pass

def test_order_summary():
    s = get_order_summary(1)
    assert "Alice" in s

def test_order_summary_includes_name():
    s = get_order_summary(3)
    assert "Charlie" in s

def test_get_orders_returns_list():
    orders = get_user_orders(1)
    assert isinstance(orders, list)
'''.strip(),

    "tests/test_report.py": '''"""报表服务测试"""
from src.report_service import generate_user_report

def test_report_valid():
    r = generate_user_report(1)
    assert r["user"] == "Alice"
    assert "email" in r

def test_report_invalid():
    r = generate_user_report(999)
    assert "error" in r

def test_report_has_email():
    r = generate_user_report(3)
    assert "@" in r["email"]

def test_report_not_none():
    r = generate_user_report(1)
    assert r is not None
'''.strip(),

    "tests/test_admin.py": '''"""管理面板测试"""
from src.admin_panel import get_user_details

def test_details_valid():
    d = get_user_details(1)
    assert "Alice" in d
    assert "@" in d

def test_details_invalid():
    d = get_user_details(999)
    assert d == "Unknown user"

def test_details_charlie():
    d = get_user_details(3)
    assert "Charlie" in d
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
    "name": "refactor-api",
    "description": "接口重构 — 改 get_user 签名导致 3 个调用点挂",
    "task_prompt": (
        "修改 src/user_service.py 中的 get_user 方法，添加 include_deleted 参数（默认 False）。\n\n"
        "当 include_deleted=False 时，不返回已删除的用户（deleted=True）。\n"
        "当 include_deleted=True 时，返回所有用户。\n\n"
        "确保项目中的所有测试都通过。"
    ),
    "test_command": "python3 -m pytest tests/ -v --tb=short 2>&1",
    "expected_new_tests": None,
}
