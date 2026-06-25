"""抢稿工作循环 — 持续监测, 符合条件立即领取"""

import asyncio

from .browser import Browser
from .edge_launcher import cdp_ready, ensure_edge_debug
from .rules import should_grab
from .win32_bg import keep_edge_background


class GrabWorker:
    def __init__(self, cfg: dict, log_fn=None, status_fn=None, on_grabbed=None):
        self.cfg = cfg
        self.log = log_fn or print
        self.status = status_fn or self.log
        self.on_grabbed = on_grabbed
        self.background = bool(cfg.get("background_mode", True))
        self.browser = Browser(log_fn=self.log, background=self.background)
        self.running = False
        self.grabbed_count = 0
        self._grabbed_titles: set[str] = set()

    def stop(self):
        self.running = False

    async def _ensure_connected(self) -> bool:
        port = int(self.cfg.get("cdp_port", 9222))
        if not cdp_ready(port):
            if not ensure_edge_debug(
                port=port,
                url=self.cfg.get("target_url"),
                log_fn=self.log,
            ):
                return False
        if not await self.browser.connect():
            return False
        await self.browser.ensure_all_filter()
        if self.background:
            keep_edge_background()
        return True

    def _count_claimable(self, cards: list, publishers: set, owner: str) -> int:
        n = 0
        for card in cards:
            if card.get("claimed"):
                continue
            if card.get("channel") not in publishers:
                continue
            if not card.get("canClaim"):
                continue
            title = card.get("title", "")
            if title in self._grabbed_titles:
                continue
            ok, _ = should_grab(title, owner)
            if ok:
                n += 1
        return n

    def _log_tick(self, status: dict, claimable: int, refreshed: bool):
        pending = status.get("pending", "?")
        hint = status.get("refreshHint", "")
        tag = "OK" if refreshed else "失败"
        line = f"刷新{tag} | 待领取 {pending} | 可抢 {claimable} | 已抢 {self.grabbed_count}"
        if hint:
            line += f" | {hint}"
        self.status(line)

    async def run(self):
        self.running = True
        self.grabbed_count = 0
        self._grabbed_titles.clear()

        if not await self._ensure_connected():
            self.running = False
            return

        interval = float(self.cfg.get("refresh_interval", 1.0))
        max_count = int(self.cfg.get("max_grab_count", 0))
        publishers = set(self.cfg.get("publishers", []))
        owner = self.cfg.get("owner_name", "朱昊天")

        if not publishers:
            self.log("请至少选择一个公众号")
            self.running = False
            await self.browser.close()
            return

        self.log(f"开始循环 | 每 {interval}s 刷新 | 上限 {max_count or '不限'} 篇")

        fail_streak = 0
        try:
            while self.running:
                if max_count > 0 and self.grabbed_count >= max_count:
                    self.log(f"已达上限 {max_count} 篇, 停止监测")
                    break

                refreshed = await self.browser.click_refresh()
                if not refreshed:
                    fail_streak += 1
                    status = await self.browser.read_status()
                    self._log_tick(status, 0, False)
                    if fail_streak >= 5:
                        self.log("连续刷新失败5次, 重新进入稿池页面...")
                        if await self.browser.reenter_pool_page():
                            fail_streak = 0
                        else:
                            self.log("重新进入失败, 尝试重连 Edge...")
                            await self.browser.close()
                            if not await self._ensure_connected():
                                self.log("重连失败, 5s 后重试")
                                await asyncio.sleep(5)
                                continue
                            fail_streak = 0
                    await asyncio.sleep(interval)
                    continue

                fail_streak = 0
                status = await self.browser.read_status()
                cards = await self.browser.extract_cards()
                claimable = self._count_claimable(cards, publishers, owner)
                self._log_tick(status, claimable, True)
                for card in cards:
                    if not self.running:
                        break
                    if max_count > 0 and self.grabbed_count >= max_count:
                        break
                    if card.get("claimed"):
                        continue
                    if card.get("channel") not in publishers:
                        continue
                    if not card.get("canClaim"):
                        continue

                    title = card.get("title", "")
                    if title in self._grabbed_titles:
                        continue

                    ok, reason = should_grab(title, owner)
                    if not ok:
                        continue

                    if await self.browser.claim_by_title(title, owner):
                        self.grabbed_count += 1
                        self._grabbed_titles.add(title)
                        self.log(
                            f">>> 抢到 #{self.grabbed_count} "
                            f"[{card['channel']}] {title[:50]} ({reason})"
                        )
                        if self.on_grabbed:
                            self.on_grabbed(self.grabbed_count)
                        if self.background:
                            keep_edge_background()
                        if max_count > 0 and self.grabbed_count >= max_count:
                            self.log(f"已达上限 {max_count} 篇, 停止监测")
                            self.running = False
                            break
                    else:
                        pass  # 领取失败, 下轮状态行继续刷新

                if self.running:
                    if self.background:
                        keep_edge_background()
                    await asyncio.sleep(interval)
        finally:
            await self.browser.close()
            self.running = False
            self.log("监测已停止")
