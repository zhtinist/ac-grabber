"""AC Grabber — AI Copywriter 抢稿助手 GUI"""

import sys
import asyncio
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
from pathlib import Path

from ac_grabber.config import ALL_PUBLISHERS, DEFAULTS, load_config, save_config, app_dir
from ac_grabber.edge_launcher import restart_edge_debug
from ac_grabber.worker import GrabWorker

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


class ToggleButton(tk.Button):
    """可切换的公众号选择按钮"""

    def __init__(self, master, text, variable: dict, **kw):
        self.name = text
        self.state_var = variable
        super().__init__(
            master, text=text, width=14, relief=tk.RAISED,
            command=self._toggle, **kw,
        )
        self._sync()

    def _toggle(self):
        self.state_var[self.name] = not self.state_var.get(self.name, False)
        self._sync()

    def _sync(self):
        on = self.state_var.get(self.name, False)
        self.config(
            relief=tk.SUNKEN if on else tk.RAISED,
            bg="#4CAF50" if on else "#e0e0e0",
            fg="white" if on else "black",
        )


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AC Grabber — AI Copywriter 抢稿助手")
        self.geometry("720x620")
        self.minsize(640, 520)

        self.cfg = load_config()
        self.pub_states: dict[str, bool] = {
            p: p in self.cfg.get("publishers", DEFAULTS["publishers"])
            for p in ALL_PUBLISHERS
        }
        self.worker: GrabWorker | None = None
        self.worker_thread: threading.Thread | None = None
        self.loop: asyncio.AbstractEventLoop | None = None

        self._build_ui()
        self._log("就绪。请先点「启动 Edge」按钮。")

    def _build_ui(self):
        pad = {"padx": 8, "pady": 4}

        # --- Edge 启动 ---
        frm_edge = ttk.LabelFrame(self, text="Edge 浏览器")
        frm_edge.pack(fill=tk.X, **pad)
        row_edge = ttk.Frame(frm_edge)
        row_edge.pack(fill=tk.X, padx=8, pady=8)
        self.btn_launch_edge = ttk.Button(
            row_edge, text="🌐 启动 Edge (关闭旧窗口 + 调试模式)",
            command=self._launch_edge,
        )
        self.btn_launch_edge.pack(side=tk.LEFT)
        ttk.Label(
            row_edge,
            text="  自动关闭所有 Edge, 以调试模式重启并保留登录",
            foreground="gray",
        ).pack(side=tk.LEFT, padx=8)
        # --- 公众号选择 ---
        frm_pub = ttk.LabelFrame(self, text="选择要抢的公众号 (点击切换)")
        frm_pub.pack(fill=tk.X, **pad)

        frm_btns = ttk.Frame(frm_pub)
        frm_btns.pack(fill=tk.X, padx=8, pady=8)
        self.pub_buttons = []
        for i, name in enumerate(ALL_PUBLISHERS):
            btn = ToggleButton(frm_btns, name, self.pub_states)
            btn.grid(row=i // 3, column=i % 3, padx=4, pady=4, sticky="ew")
            self.pub_buttons.append(btn)
        for c in range(3):
            frm_btns.columnconfigure(c, weight=1)

        # --- 参数 ---
        frm_cfg = ttk.LabelFrame(self, text="参数设置")
        frm_cfg.pack(fill=tk.X, **pad)

        row1 = ttk.Frame(frm_cfg)
        row1.pack(fill=tk.X, padx=8, pady=6)
        ttk.Label(row1, text="定制稿归属名:").pack(side=tk.LEFT)
        self.var_owner = tk.StringVar(value=self.cfg.get("owner_name", ""))
        ttk.Entry(row1, textvariable=self.var_owner, width=12).pack(side=tk.LEFT, padx=6)
        ttk.Label(row1, text="(仅标题末尾括号内为此名字的可抢)").pack(side=tk.LEFT)

        row2 = ttk.Frame(frm_cfg)
        row2.pack(fill=tk.X, padx=8, pady=6)
        ttk.Label(row2, text="刷新间隔(秒):").pack(side=tk.LEFT)
        self.var_interval = tk.StringVar(value=str(self.cfg.get("refresh_interval", 1.0)))
        ttk.Entry(row2, textvariable=self.var_interval, width=6).pack(side=tk.LEFT, padx=6)
        ttk.Label(row2, text="  最多领取(0=不限):").pack(side=tk.LEFT)
        self.var_max = tk.StringVar(value=str(self.cfg.get("max_grab_count", 0)))
        ttk.Entry(row2, textvariable=self.var_max, width=6).pack(side=tk.LEFT, padx=6)
        self.lbl_grabbed = ttk.Label(row2, text="  已领: 0 篇")
        self.lbl_grabbed.pack(side=tk.LEFT, padx=12)

        # --- 控制 ---
        frm_ctrl = ttk.Frame(self)
        frm_ctrl.pack(fill=tk.X, padx=8, pady=8)
        self.btn_start = ttk.Button(frm_ctrl, text="▶ 开始抢稿", command=self._start)
        self.btn_start.pack(side=tk.LEFT, padx=4)
        self.btn_stop = ttk.Button(frm_ctrl, text="■ 停止", command=self._stop, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=4)
        ttk.Button(frm_ctrl, text="保存设置", command=self._save_settings).pack(side=tk.LEFT, padx=4)

        # --- 日志 ---
        frm_log = ttk.LabelFrame(self, text="运行日志")
        frm_log.pack(fill=tk.BOTH, expand=True, padx=8, pady=(4, 8))
        self.txt_log = scrolledtext.ScrolledText(frm_log, height=18, state=tk.DISABLED, font=("Consolas", 9))
        self.txt_log.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        tip = "使用步骤: 1) 点「启动 Edge」  2) 确认已登录  3) 选公众号  4) 开始抢稿"
        ttk.Label(self, text=tip, foreground="gray").pack(pady=(0, 6))

    def _log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}\n"

        def append():
            self.txt_log.config(state=tk.NORMAL)
            self.txt_log.insert(tk.END, line)
            self.txt_log.see(tk.END)
            self.txt_log.config(state=tk.DISABLED)

        self.after(0, append)

    def _collect_cfg(self) -> dict:
        pubs = [p for p, on in self.pub_states.items() if on]
        try:
            interval = float(self.var_interval.get())
        except ValueError:
            interval = 1.0
        try:
            max_grab = int(self.var_max.get())
        except ValueError:
            max_grab = 0
        return {
            "owner_name": self.var_owner.get().strip(),
            "publishers": pubs,
            "max_grab_count": max(0, max_grab),
            "refresh_interval": max(0.5, interval),
            "cdp_port": 9222,
            "target_url": DEFAULTS["target_url"],
        }

    def _save_settings(self):
        self.cfg = self._collect_cfg()
        save_config(self.cfg)
        self._log("设置已保存")
        messagebox.showinfo("保存", f"配置已写入:\n{app_dir() / 'config.json'}")

    def _launch_edge(self):
        if not messagebox.askyesno(
            "启动 Edge",
            "将关闭所有 Edge 窗口, 然后以调试模式重新启动。\n"
            "登录状态会保留。未保存的网页标签页会丢失。\n\n继续?",
        ):
            return

        self.btn_launch_edge.config(state=tk.DISABLED)
        self._log("正在关闭 Edge 并重新启动...")

        def task():
            ok, lines = restart_edge_debug(
                port=self.cfg.get("cdp_port", 9222),
                url=DEFAULTS["target_url"],
            )
            for line in lines:
                self._log(line)
            if ok:
                self._log("Edge 就绪, 可以开始抢稿")
            else:
                self.after(0, lambda: messagebox.showerror("启动失败", "\n".join(lines)))
            self.after(0, lambda: self.btn_launch_edge.config(state=tk.NORMAL))

        threading.Thread(target=task, daemon=True).start()

    def _on_grabbed(self, count: int):
        self.after(0, lambda: self.lbl_grabbed.config(text=f"  已领: {count} 篇"))

    def _start(self):
        cfg = self._collect_cfg()
        if not cfg["publishers"]:
            messagebox.showwarning("提示", "请至少选择一个公众号")
            return
        save_config(cfg)
        self.cfg = cfg

        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.lbl_grabbed.config(text="  已领: 0 篇")
        self._log("启动中...")

        def run_worker():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.worker = GrabWorker(cfg, log_fn=self._log, on_grabbed=self._on_grabbed)
            try:
                self.loop.run_until_complete(self.worker.run())
            finally:
                self.loop.close()
                self.after(0, self._on_worker_done)

        self.worker_thread = threading.Thread(target=run_worker, daemon=True)
        self.worker_thread.start()

    def _stop(self):
        if self.worker:
            self.worker.stop()
            self._log("正在停止...")

    def _on_worker_done(self):
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self._log("运行结束")


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
