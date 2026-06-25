"""抢稿规则 — 标题末尾括号定制稿

规则摘要:
1. 只抢 config 里选定的公众号 (tag-channel)
2. 只抢「待领取」区、按钮为「领取」且未禁用的稿子
3. 标题末尾无括号 → 普通稿，可抢
4. 标题末尾为 (你的名字) → 你的定制稿，可抢
5. 标题末尾括号内含汉字且不是你的名字 → 他人定制稿，不抢
6. 标题末尾括号内为数字等非汉字 (如 (9)) → 可抢
7. 标题开头/中间的括号如 (横屏) 不影响判断
"""

import re

# 标题末尾括号内容
NAME_AT_END_RE = re.compile(r"[（(]([^）)]+)[）)]\s*$")
# 括号内是否含汉字
HAS_CJK_RE = re.compile(r"[一-鿿]")


def extract_end_name(title: str) -> str | None:
    m = NAME_AT_END_RE.search(title.strip())
    return m.group(1).strip() if m else None


def should_grab(title: str, owner_name: str) -> tuple[bool, str]:
    """
    判断是否可抢。
    """
    title = title.strip()
    if not title:
        return False, "标题为空"

    name = extract_end_name(title)
    if not name:
        return True, "普通稿(末尾无定制括号)"

    if name == owner_name:
        return True, f"你的定制稿({name})"

    if HAS_CJK_RE.search(name):
        return False, f"他人定制稿({name})"

    return True, f"可抢({name})"


# 自测用例
_SELF_TESTS = [
    # (title, owner, expected_ok, note)
    ("（横屏）马斯克创业那些事13：万亿身家从何而来", "朱昊天", True, "开头括号不算"),
    ("AI革命，开始烧电网了（朱昊天）", "朱昊天", True, "你的定制稿"),
    ("FBI造了个假小镇（胡铭宇）", "朱昊天", False, "他人三字定制稿"),
    ("某标题（樊乐鑫）", "朱昊天", False, "他人三字定制稿"),
    ("没有个人 IP，就像没有名片", "朱昊天", True, "普通稿"),
    ("某系列（9）", "朱昊天", True, "末尾数字括号可抢"),
    ("某系列（横屏）", "朱昊天", False, "末尾汉字括号非朱昊天不抢"),
    ("（横屏）马斯克（9）：特斯拉 钱烧光了", "朱昊天", True, "末尾无括号"),
]


def run_self_tests() -> list[str]:
    errors = []
    for title, owner, want, note in _SELF_TESTS:
        got, reason = should_grab(title, owner)
        if got != want:
            errors.append(f"FAIL [{note}] {title!r} => {got} ({reason}), want {want}")
    return errors
