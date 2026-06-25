"""命令行抢稿 — 持续刷新稿池, 状态单行刷新, 抢到新稿另起一行"""

import sys
import asyncio
from datetime import datetime

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from ac_grabber.config import load_config
from ac_grabber.edge_launcher import ensure_edge_debug
from ac_grabber.rules import run_self_tests
from ac_grabber.worker import GrabWorker
from ac_grabber.win32_bg import keep_edge_background

_status_len = 0


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def status(msg: str):
    """同一行原地更新监测状态"""
    global _status_len
    line = f"[{_ts()}] {msg}"
    pad = max(0, _status_len - len(line))
    sys.stdout.write(f"\r{line}{' ' * pad}")
    sys.stdout.flush()
    _status_len = len(line)


def log(msg: str):
    """另起一行输出 (抢到新稿、启动信息等)"""
    global _status_len
    line = f"[{_ts()}] {msg}"
    if _status_len > 0:
        sys.stdout.write("\n")
        _status_len = 0
    print(line, flush=True)


def main():
    cfg = load_config()

    fails = run_self_tests()
    if fails:
        print("规则自检失败:")
        for f in fails:
            print(" ", f)
        return 1

    interval = float(cfg.get("refresh_interval", 0.3))
    max_n = int(cfg.get("max_grab_count", 0))

    log("AI Copywriter | 使用你的 Edge 登录状态")
    log("关闭本 CMD 窗口即停止抢稿 | Edge 可继续开其他标签页")
    log(
        f"人名: {cfg['owner_name']} | "
        f"上限: {max_n or '不限'} 篇 | "
        f"刷新: {interval}s | "
        f"公众号: {', '.join(cfg['publishers'])}"
    )

    if not ensure_edge_debug(
        port=cfg.get("cdp_port", 9222),
        url=cfg.get("target_url"),
        log_fn=log,
    ):
        return 1

    if cfg.get("background_mode", True):
        keep_edge_background()

    worker = GrabWorker(cfg, log_fn=log, status_fn=status)
    try:
        asyncio.run(worker.run())
    except KeyboardInterrupt:
        worker.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
