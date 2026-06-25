"""Edge CDP — 使用你平时的 Edge 配置 (登录/书签保留)"""

import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

from .config import DEFAULTS

EDGE_CANDIDATES = [
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
]


def edge_user_data_dir() -> Path:
    """日常 Edge 配置目录 — 登录状态、Cookie 都在这里"""
    return Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Edge" / "User Data"


def find_edge_exe() -> Path | None:
    for p in EDGE_CANDIDATES:
        if p.is_file():
            return p
    return None


def any_edge_running() -> bool:
    if os.name != "nt":
        return False
    try:
        r = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq msedge.exe", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            encoding="gbk",
            errors="replace",
        )
        return "msedge.exe" in r.stdout.lower()
    except Exception:
        return False


def cdp_ready(port: int | None = None, timeout: float = 2.0) -> bool:
    port = port or DEFAULTS["cdp_port"]
    url = f"http://127.0.0.1:{port}/json/version"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def wait_for_cdp(
    port: int | None = None,
    total_wait: float = 30.0,
    interval: float = 1.0,
) -> bool:
    deadline = time.monotonic() + total_wait
    while time.monotonic() < deadline:
        if cdp_ready(port):
            return True
        time.sleep(interval)
    return False


def close_all_edge() -> tuple[bool, str]:
    """关闭 Edge 以便用同一配置以调试模式重启 (登录状态不丢)"""
    try:
        r = subprocess.run(
            ["taskkill", "/IM", "msedge.exe", "/F"],
            capture_output=True,
            text=True,
            encoding="gbk",
            errors="replace",
        )
        if r.returncode == 0:
            return True, "已关闭 Edge (准备以调试模式重启, 登录状态保留)"
        if r.returncode == 128:
            return True, "Edge 未在运行"
        msg = (r.stderr or r.stdout or "").strip()
        return False, msg or f"taskkill 退出码 {r.returncode}"
    except Exception as e:
        return False, str(e)


def start_edge_debug(
    port: int | None = None,
    url: str | None = None,
    minimized: bool = False,
) -> tuple[bool, str]:
    edge = find_edge_exe()
    if not edge:
        return False, "未找到 Microsoft Edge, 请先安装"

    port = port or DEFAULTS["cdp_port"]
    url = url or DEFAULTS["target_url"]
    user_data = edge_user_data_dir()

    args = [
        str(edge),
        f"--remote-debugging-port={port}",
        f"--user-data-dir={user_data}",
    ]
    if minimized:
        args.append("--start-minimized")
    args.append(url)

    try:
        subprocess.Popen(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )
        return True, f"Edge 已启动 (你的现有配置, 调试端口 {port})"
    except Exception as e:
        return False, str(e)


def ensure_edge_debug(
    port: int | None = None,
    url: str | None = None,
    log_fn=None,
) -> bool:
    """
    连接你的 Edge (现有登录状态).
    若 CDP 已就绪则直接连接, 不重启.
    否则以调试模式重启 Edge — 同一配置目录, 登录不丢.
    重启后可在其他标签页照常使用 Edge.
    """
    log = log_fn or print
    port = port or DEFAULTS["cdp_port"]

    if cdp_ready(port):
        log(f"已连接你的 Edge (端口 {port}, 登录状态保留)")
        return True

    if any_edge_running():
        log("Edge 在运行但未开启调试端口, 需要重启一次 Edge")
        log("提示: 登录和书签会保留, 请先保存未保存的标签页")
    else:
        log("正在启动 Edge (使用你的现有配置)...")

    ok, msg = close_all_edge()
    log(msg)
    if not ok:
        return False

    time.sleep(2.5)
    ok, msg = start_edge_debug(port=port, url=url, minimized=False)
    log(msg)
    if not ok:
        return False

    if wait_for_cdp(port, total_wait=30.0):
        log("Edge 就绪 — 可在其他标签页继续工作, 抢稿在稿池页后台进行")
        return True

    log("等待 Edge 调试端口超时, 请手动运行 start-edge.bat")
    return False


# 兼容旧名
close_grab_edge = close_all_edge
grab_profile_dir = edge_user_data_dir
