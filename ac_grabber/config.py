"""配置读写 — 用户改 config.json 里「人名 / 抢稿上限 / 目标公众号」即可"""

import json
import sys
from pathlib import Path

START_EDGE_BAT = "start-edge.bat"

# 页面上可选的公众号
ALL_PUBLISHERS = [
    "小金AI新科技",
    "康健求真",
    "大宝说创业",
    "AI壹号",
    "秦刚·个人IP",
    "秦刚头条",
]

# 内部默认（一般不用改，可在 config.json 里用英文键覆盖）
DEFAULTS = {
    "owner_name": "",
    "publishers": ["小金AI新科技", "康健求真"],
    "max_grab_count": 8,
    "refresh_interval": 0.3,
    "cdp_port": 9222,
    "background_mode": False,
    "target_url": "https://ai-copywriter.risevideo.ai/distribute",
}

# config.json 中文键 ↔ 内部字段
_CN_KEYS = {
    "人名": "owner_name",
    "抢稿上限": "max_grab_count",
    "目标公众号": "publishers",
    "刷新间隔": "refresh_interval",
}


def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


def ensure_edge_bat():
    """打包后首次运行, 将 bat 释放到 exe 同目录"""
    if not getattr(sys, "frozen", False):
        return
    dest = app_dir() / START_EDGE_BAT
    if dest.exists():
        return
    src = Path(sys._MEIPASS) / START_EDGE_BAT  # type: ignore[attr-defined]
    if src.exists():
        import shutil
        shutil.copy2(src, dest)


def config_path() -> Path:
    return app_dir() / "config.json"


def _apply_file_data(cfg: dict, data: dict) -> dict:
    for cn, en in _CN_KEYS.items():
        if cn in data:
            val = data[cn]
            if en == "owner_name":
                cfg[en] = str(val).strip()
            elif en == "max_grab_count":
                cfg[en] = max(0, int(val))
            elif en == "publishers":
                cfg[en] = [str(p).strip() for p in val if str(p).strip()]
            elif en == "refresh_interval":
                cfg[en] = max(0.1, float(val))

    for key in DEFAULTS:
        if key in data:
            cfg[key] = data[key]
    return cfg


def load_config() -> dict:
    path = config_path()
    cfg = dict(DEFAULTS)
    if not path.exists():
        save_config(cfg)
        return cfg
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        cfg = _apply_file_data(cfg, data)
    except Exception:
        pass
    return cfg


def save_config(cfg: dict):
    """保存 config.json（保留 _说明 / _可选公众号 等注释项）"""
    path = config_path()
    data: dict = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            data = {}

    if "_说明" not in data:
        data["_说明"] = "改下面四项后保存, 重新运行 run-cli.bat 生效"
    if "_可选公众号" not in data:
        data["_可选公众号"] = list(ALL_PUBLISHERS)

    data["人名"] = cfg.get("owner_name", DEFAULTS["owner_name"])
    data["抢稿上限"] = int(cfg.get("max_grab_count", DEFAULTS["max_grab_count"]))
    data["目标公众号"] = list(cfg.get("publishers", DEFAULTS["publishers"]))
    data["刷新间隔"] = float(cfg.get("refresh_interval", DEFAULTS["refresh_interval"]))

    # 高级项：仅当与默认不同或原文件已有时才写入
    for key in ("refresh_interval", "cdp_port", "background_mode", "target_url"):
        if key in cfg and (key in data or cfg[key] != DEFAULTS.get(key)):
            data[key] = cfg[key]

    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
