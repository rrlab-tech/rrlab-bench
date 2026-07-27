"""
场景：添加校验的边界效应 — 校验过严会挂掉 batch_import 的边界数据
"""
from pathlib import Path

TEMPLATE_FILES = {
    "src/__init__.py": "",
    "tests/__init__.py": "",
    "src/models.py": '''"""数据模型 — 需要添加输入校验"""

class User:
    def __init__(self, name: str, email: str, age: int):
        self.name = name
        self.email = email
        self.age = age

    def to_dict(self) -> dict:
        return {"name": self.name, "email": self.email, "age": self.age}

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        return cls(name=data["name"], email=data["email"], age=data["age"])

    def validate(self) -> list[str]:
        """验证用户数据，返回错误列表（当前为空——需要添加校验）"""
        return []
'''.strip(),

    "src/api_handlers.py": '''"""API 处理 — 用 models 处理请求"""
from src.models import User

def create_user(data: dict) -> dict:
    user = User(name=data["name"], email=data["email"], age=data["age"])
    errors = user.validate()
    if errors:
        return {"success": False, "errors": errors}
    return {"success": True, "user": user.to_dict()}

def update_user(user: User, data: dict) -> dict:
    if "name" in data:
        user.name = data["name"]
    if "email" in data:
        user.email = data["email"]
    if "age" in data:
        user.age = data["age"]
    errors = user.validate()
    if errors:
        return {"success": False, "errors": errors}
    return {"success": True, "user": user.to_dict()}
'''.strip(),

    "src/batch_import.py": '''"""批量导入 — 处理一些不规范但可接受的数据"""
from src.models import User

def import_users(records: list[dict]) -> dict:
    """批量导入用户。部分数据可能来自旧系统，格式不太规范但业务上可接受。"""
    imported = []
    skipped = []
    for i, rec in enumerate(records):
        try:
            # 处理缺失字段（旧数据可能没有 age）
            name = rec.get("name", f"unknown_{i}")
            email = rec.get("email", f"user{i}@placeholder.local")
            age = rec.get("age", 0)  # 默认 0 表示"未知"
            user = User(name=name, email=email, age=age)
            errors = user.validate()
            if errors:
                skipped.append({"index": i, "errors": errors})
            else:
                imported.append(user.to_dict())
        except Exception as e:
            skipped.append({"index": i, "error": str(e)})
    return {"imported": len(imported), "skipped": len(skipped), "total": len(records)}
'''.strip(),

    "tests/test_models.py": '''"""数据模型测试"""
from src.models import User

def test_create_user():
    u = User("Alice", "alice@example.com", 30)
    assert u.name == "Alice"
    assert u.email == "alice@example.com"
    assert u.age == 30

def test_to_dict():
    u = User("Bob", "bob@example.com", 25)
    d = u.to_dict()
    assert d["name"] == "Bob"
    assert d["email"] == "bob@example.com"
    assert d["age"] == 25

def test_from_dict():
    d = {"name": "Charlie", "email": "charlie@example.com", "age": 40}
    u = User.from_dict(d)
    assert u.name == "Charlie"

def test_validate_empty():
    u = User("Dave", "dave@example.com", 50)
    errors = u.validate()
    assert errors == []

def test_user_age_zero():
    u = User("Eve", "eve@example.com", 0)
    assert u.age == 0
    assert u.validate() == []
'''.strip(),

    "tests/test_api.py": '''"""API 测试"""
from src.api_handlers import create_user, update_user
from src.models import User

def test_create_valid():
    r = create_user({"name": "Alice", "email": "alice@example.com", "age": 30})
    assert r["success"]

def test_create_invalid_missing_data():
    data = {"name": "", "email": "alice@example.com", "age": 30}
    u = User.from_dict(data)
    errors = u.validate()
    assert isinstance(errors, list)

def test_update_valid():
    u = User("Bob", "bob@example.com", 25)
    r = update_user(u, {"name": "Bobby"})
    assert r["success"]
    assert r["user"]["name"] == "Bobby"

def test_update_email():
    u = User("Charlie", "charlie@example.com", 40)
    r = update_user(u, {"email": "new@example.com"})
    assert r["success"]
    assert r["user"]["email"] == "new@example.com"

def test_create_normal():
    r = create_user({"name": "Dave", "email": "dave@example.com", "age": 35})
    assert r["success"]
    assert r["user"]["name"] == "Dave"

def test_create_with_email():
    r = create_user({"name": "Eve", "email": "eve@domain.com", "age": 22})
    assert r["success"]
    assert "@" in r["user"]["email"]
'''.strip(),

    "tests/test_batch.py": '''"""批量导入测试"""
from src.batch_import import import_users

def test_import_valid():
    records = [
        {"name": "Alice", "email": "alice@example.com", "age": 30},
        {"name": "Bob", "email": "bob@example.com", "age": 25},
        {"name": "Charlie", "email": "charlie@example.com", "age": 40},
    ]
    r = import_users(records)
    assert r["imported"] == 3
    assert r["skipped"] == 0

def test_import_missing_age():
    """旧数据可能没有 age 字段"""
    records = [
        {"name": "Dave", "email": "dave@example.com"},  # 无 age
    ]
    r = import_users(records)
    assert r["imported"] == 1

def test_import_missing_email():
    """旧数据可能没有 email 字段"""
    records = [
        {"name": "Eve", "age": 22},  # 无 email
    ]
    r = import_users(records)
    assert r["imported"] == 1

def test_import_mixed():
    records = [
        {"name": "Frank", "email": "frank@example.com", "age": 50},
        {"name": "Grace", "email": "grace@example.com"},  # 缺 age
        {"name": "Henry", "age": 35},  # 缺 email
    ]
    r = import_users(records)
    assert r["imported"] == 3

def test_import_empty_name():
    records = [
        {"name": "", "email": "test@example.com", "age": 20},
    ]
    r = import_users(records)
    assert r["imported"] == 1  # 空名字业务上可接受

def test_import_boundary_age():
    """边界年龄值"""
    records = [
        {"name": "Infant", "email": "infant@example.com", "age": 0},
        {"name": "Centenarian", "email": "old@example.com", "age": 100},
        {"name": "Young", "email": "young@example.com", "age": 13},
    ]
    r = import_users(records)
    assert r["imported"] == 3

def test_import_non_standard_email():
    """不规范但有效的邮箱"""
    records = [
        {"name": "X", "email": "x@y", "age": 30},  # 短邮箱
        {"name": "Y", "email": "user+tag@example.com", "age": 30},  # 带 tag
    ]
    r = import_users(records)
    assert r["imported"] == 2

def test_import_all_fields():
    records = [
        {"name": "Zack", "email": "z@example.com", "age": 30},
    ]
    r = import_users(records)
    assert r["imported"] == 1
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
    "name": "add-validation",
    "description": "添加校验边界效应 — 校验过严会挂掉 batch_import 的边界数据",
    "task_prompt": (
        "给 src/models.py 的 User 模型的 validate 方法添加输入校验逻辑。\n\n"
        "校验规则：\n"
        "1. email 字段必须包含 @ 符号\n"
        "2. age 字段必须在 0 到 150 之间\n\n"
        "如果有校验错误，validate 方法应该返回包含错误描述的字符串列表。\n"
        "同时更新 api_handlers.py 和 batch_import.py 中需要适配的代码。\n"
        "确保所有测试都通过。"
    ),
    "test_command": "python3 -m pytest tests/ -v --tb=short 2>&1",
    "expected_new_tests": None,
}
