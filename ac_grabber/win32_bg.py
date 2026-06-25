"""后台控制 — 使用日常 Edge 配置时不最小化窗口, 避免影响你其他标签页"""

import ctypes
import sys
from ctypes import wintypes

SW_SHOWMINNOACTIVE = 7

user32 = ctypes.windll.user32
WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)


def minimize_edge_windows(_pids=None) -> int:
    """仅在 background_mode 开启时使用; 默认不最小化日常 Edge"""
    return 0


def keep_edge_background():
    """使用日常 Edge 时不抢焦点、不最小化, 仅靠 JS 静默操作"""
    pass
