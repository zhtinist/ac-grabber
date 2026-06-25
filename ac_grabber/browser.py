"""Edge CDP 浏览器操作 — 全程 JS 静默点击, 不抢前台焦点"""

import asyncio

from .config import load_config
from .win32_bg import keep_edge_background

EXTRACT_CARDS_JS = r"""() => {
    function stripEmoji(s) {
        return s.replace(/^[\u{1F300}-\u{1FAFF}\u2600-\u27BF\uFE0F\u200D\s]+/u, '').trim();
    }
    function isManuscriptCard(el) {
        const cls = (el.className || '').toString();
        const tokens = cls.split(/\s+/);
        if (!tokens.includes('card')) return false;
        if (cls.includes('card-tags') || cls.includes('card-footer') ||
            cls.includes('card-actions') || cls.includes('card-meta')) return false;
        return el.querySelector('[class*="card-title"]') &&
               el.querySelector('[class*="card-tags"]');
    }
    function getTopLevelCards() {
        const candidates = [...document.querySelectorAll('div')].filter(isManuscriptCard);
        return candidates.filter(card =>
            !candidates.some(other => other !== card && card.contains(other))
        );
    }
    return getTopLevelCards().map(card => {
        const title = (card.querySelector('[class*="card-title"]')?.innerText || '').trim();
        const channel = (card.querySelector('[class*="tag-channel"]')?.innerText || '').trim();
        const claimed = (card.className || '').toString().includes('card-claimed');
        const meta = (card.querySelector('[class*="card-meta"]')?.innerText || '').trim();
        const btns = [...card.querySelectorAll('[class*="card-actions"] button')].map(b => ({
            text: stripEmoji((b.innerText || '').trim()),
            disabled: b.disabled,
        }));
        const canClaim = btns.some(b => b.text === '领取' && !b.disabled);
        return { title, channel, claimed, meta, canClaim };
    });
}"""

READ_STATUS_JS = r"""() => {
    const bodyText = document.body.innerText || '';
    const pendingMatch = bodyText.match(/待领取\s*\n?\s*(\d+)\s*篇/);
    return {
        pending: pendingMatch ? pendingMatch[1] : '?',
        refreshHint: [...document.querySelectorAll('span, div, p')]
            .map(el => (el.innerText || '').trim())
            .find(t => /^刚刚刷新$/.test(t) || /^\d+秒前刷新$/.test(t)) || '',
        hasRefreshBtn: !!document.querySelector('[class*="refresh-btn"]'),
    };
}"""

CLICK_REFRESH_JS = r"""() => {
    const btn = document.querySelector('[class*="refresh-btn"]');
    if (!btn || btn.disabled) return false;
    btn.click();
    return true;
}"""

ENSURE_ALL_JS = r"""() => {
    const buttons = [...document.querySelectorAll('button')];
    const allBtn = buttons.find(b => (b.innerText || '').trim() === '全部');
    if (!allBtn) return false;
    allBtn.click();
    return true;
}"""

CLAIM_BY_TITLE_JS = r"""(targetTitle) => {
    function stripEmoji(s) {
        return s.replace(/^[\u{1F300}-\u{1FAFF}\u2600-\u27BF\uFE0F\u200D\s]+/u, '').trim();
    }
    function isManuscriptCard(el) {
        const cls = (el.className || '').toString();
        const tokens = cls.split(/\s+/);
        if (!tokens.includes('card')) return false;
        if (cls.includes('card-tags') || cls.includes('card-footer') ||
            cls.includes('card-actions') || cls.includes('card-meta')) return false;
        return el.querySelector('[class*="card-title"]') &&
               el.querySelector('[class*="card-tags"]');
    }
    const cards = [...document.querySelectorAll('div')].filter(isManuscriptCard);
    for (const card of cards) {
        if ((card.className || '').toString().includes('card-claimed')) continue;
        const titleEl = card.querySelector('[class*="card-title"]');
        const t = (titleEl?.innerText || '').trim();
        if (t !== targetTitle) continue;
        for (const btn of card.querySelectorAll('[class*="card-actions"] button')) {
            const txt = stripEmoji((btn.innerText || '').trim());
            if (txt === '领取' && !btn.disabled) {
                btn.click();
                return true;
            }
        }
        return false;
    }
    return false;
}"""

CONFIRM_CLAIM_JS = r"""(ownerName) => {
    function stripEmoji(s) {
        return s.replace(/^[\u{1F300}-\u{1FAFF}\u2600-\u27BF\uFE0F\u200D\s]+/u, '').trim();
    }
    function visible(el) {
        if (!el) return false;
        const r = el.getBoundingClientRect();
        if (r.width <= 0 || r.height <= 0) return false;
        const st = window.getComputedStyle(el);
        return st.display !== 'none' && st.visibility !== 'hidden' && st.opacity !== '0';
    }
    function findModalRoot() {
        const nodes = [...document.querySelectorAll('div, section, dialog, [role="dialog"]')];
        for (const el of nodes) {
            if (!visible(el)) continue;
            const text = (el.innerText || '').trim();
            if (text.includes('领取稿件') && text.includes('确认领取')) return el;
        }
        return null;
    }
    const modal = findModalRoot();
    const scope = modal || document;

    const inputs = [...scope.querySelectorAll('input')].filter(visible);
    let nameInput = null;
    for (const inp of inputs) {
        const ph = (inp.placeholder || '').trim();
        const label = (inp.getAttribute('aria-label') || '').trim();
        if (ph.includes('姓名') || label.includes('姓名')) {
            nameInput = inp;
            break;
        }
    }
    if (!nameInput) {
        const labels = [...scope.querySelectorAll('label, span, div, p')];
        for (const lb of labels) {
            if (!(lb.innerText || '').includes('你的姓名')) continue;
            const inp = lb.querySelector('input')
                || lb.parentElement?.querySelector('input')
                || lb.nextElementSibling?.querySelector?.('input');
            if (inp && visible(inp)) {
                nameInput = inp;
                break;
            }
        }
    }
    if (!nameInput && inputs.length === 1) nameInput = inputs[0];
    if (nameInput && ownerName) {
        nameInput.focus();
        nameInput.value = ownerName;
        nameInput.dispatchEvent(new Event('input', { bubbles: true }));
        nameInput.dispatchEvent(new Event('change', { bubbles: true }));
    }

    const buttons = [...scope.querySelectorAll('button')].filter(visible);
    const confirmBtn = buttons.find(b => stripEmoji((b.innerText || '').trim()) === '确认领取');
    if (!confirmBtn || confirmBtn.disabled) return false;
    confirmBtn.click();
    return true;
}"""

CLAIM_MODAL_OPEN_JS = r"""() => {
    function visible(el) {
        if (!el) return false;
        const r = el.getBoundingClientRect();
        return r.width > 0 && r.height > 0;
    }
    return [...document.querySelectorAll('button')].some(b => {
        if (!visible(b)) return false;
        return (b.innerText || '').includes('确认领取');
    });
}"""

VERIFY_CLAIMED_JS = r"""(targetTitle) => {
    function stripEmoji(s) {
        return s.replace(/^[\u{1F300}-\u{1FAFF}\u2600-\u27BF\uFE0F\u200D\s]+/u, '').trim();
    }
    function isManuscriptCard(el) {
        const cls = (el.className || '').toString();
        const tokens = cls.split(/\s+/);
        if (!tokens.includes('card')) return false;
        if (cls.includes('card-tags') || cls.includes('card-footer') ||
            cls.includes('card-actions') || cls.includes('card-meta')) return false;
        return el.querySelector('[class*="card-title"]') &&
               el.querySelector('[class*="card-tags"]');
    }
    const modalOpen = [...document.querySelectorAll('button')].some(b => {
        const r = b.getBoundingClientRect();
        return r.width > 0 && (b.innerText || '').includes('确认领取');
    });
    if (modalOpen) return false;

    const cards = [...document.querySelectorAll('div')].filter(isManuscriptCard);
    for (const card of cards) {
        const titleEl = card.querySelector('[class*="card-title"]');
        const t = (titleEl?.innerText || '').trim();
        if (t !== targetTitle) continue;
        if ((card.className || '').toString().includes('card-claimed')) return true;
        const btns = [...card.querySelectorAll('[class*="card-actions"] button')];
        const stillClaim = btns.some(b => stripEmoji((b.innerText || '').trim()) === '领取' && !b.disabled);
        return !stillClaim;
    }
    return true;
}"""


class Browser:
    def __init__(self, log_fn=None, background: bool = True):
        self.log = log_fn or print
        self.background = background
        self.playwright = None
        self.browser = None
        self.page = None
        self.cfg = load_config()

    def _keep_bg(self):
        if self.background:
            keep_edge_background()

    async def connect(self) -> bool:
        from playwright.async_api import async_playwright

        port = self.cfg.get("cdp_port", 9222)
        target_url = self.cfg.get("target_url", "")
        if self.playwright:
            try:
                await self.playwright.stop()
            except Exception:
                pass
            self.playwright = None
            self.browser = None
            self.page = None

        self.playwright = await async_playwright().start()
        try:
            self.browser = await self.playwright.chromium.connect_over_cdp(
                f"http://127.0.0.1:{port}"
            )
        except Exception as e:
            self.log(f"无法连接 Edge: {e}")
            return False

        pages = [p for ctx in self.browser.contexts for p in ctx.pages]

        def is_web_page(p) -> bool:
            u = p.url or ""
            return u.startswith("http://") or u.startswith("https://")

        distribute_pages = [p for p in pages if "distribute" in (p.url or "")]
        if distribute_pages:
            self.page = distribute_pages[0]
        else:
            web_pages = [p for p in pages if is_web_page(p)]
            if web_pages:
                self.page = web_pages[0]
            elif self.browser.contexts:
                self.page = await self.browser.contexts[0].new_page()
            else:
                ctx = await self.browser.new_context()
                self.page = await ctx.new_page()

            self.log("正在进入稿池页面...")
            try:
                await self.page.goto(
                    target_url,
                    wait_until="domcontentloaded",
                    timeout=60000,
                )
                await asyncio.sleep(1.0)
            except Exception as e:
                self.log(f"打开稿池失败: {e}")
                return False

        if "distribute" not in (self.page.url or ""):
            self.log(f"稿池未打开, 当前页面: {(self.page.url or '')[:80]}")
            self.log("请确认 Edge 已登录 ai-copywriter 账号")
            return False

        ready = await self._wait_for_pool()
        if not ready:
            self.log("稿池页面已打开, 但未找到刷新按钮 (可能未登录或页面未加载完)")
            return False

        self._keep_bg()
        self.log(f"已连接稿池: {self.page.url[:70]}")
        return True

    async def _wait_for_pool(self, timeout_ms: int = 30000) -> bool:
        try:
            await self.page.wait_for_selector('[class*="refresh-btn"]', timeout=timeout_ms)
            return True
        except Exception:
            return False

    async def reenter_pool_page(self) -> bool:
        """重新打开稿池页面 (连续刷新失败时恢复)"""
        if not self.page:
            return False
        target_url = self.cfg.get("target_url", "")
        try:
            await self.page.goto(
                target_url,
                wait_until="domcontentloaded",
                timeout=60000,
            )
            await asyncio.sleep(1.0)
            if not await self._wait_for_pool():
                return False
            await self.ensure_all_filter()
            self._keep_bg()
            return True
        except Exception as e:
            self.log(f"重新进入稿池失败: {e}")
            return False

    async def ensure_all_filter(self):
        try:
            await self.page.evaluate(ENSURE_ALL_JS)
            await asyncio.sleep(0.3)
            self._keep_bg()
        except Exception:
            pass

    async def click_refresh(self) -> bool:
        try:
            ok = await self.page.evaluate(CLICK_REFRESH_JS)
            if ok:
                await asyncio.sleep(0.25)
                try:
                    await self.page.wait_for_selector('[class*="card-title"]', timeout=5000)
                except Exception:
                    pass
            self._keep_bg()
            return bool(ok)
        except Exception:
            self._keep_bg()
            return False

    async def read_status(self) -> dict:
        try:
            return await self.page.evaluate(READ_STATUS_JS)
        except Exception:
            return {}

    async def extract_cards(self) -> list:
        try:
            return await self.page.evaluate(EXTRACT_CARDS_JS)
        except Exception:
            return []

    async def claim_by_title(self, title: str, owner_name: str | None = None) -> bool:
        """点击领取 → 弹窗填姓名 → 确认领取"""
        title = title.strip()
        owner_name = (owner_name or self.cfg.get("owner_name", "")).strip()
        try:
            modal_open = await self.page.evaluate(CLAIM_MODAL_OPEN_JS)
            if not modal_open:
                clicked = await self.page.evaluate(CLAIM_BY_TITLE_JS, title)
                if not clicked:
                    self._keep_bg()
                    return False

                for _ in range(20):
                    await asyncio.sleep(0.15)
                    if await self.page.evaluate(CLAIM_MODAL_OPEN_JS):
                        break
                else:
                    self.log("未出现领取弹窗")
                    self._keep_bg()
                    return False

            confirmed = await self.page.evaluate(CONFIRM_CLAIM_JS, owner_name)
            if not confirmed:
                self.log("未找到「确认领取」按钮")
                self._keep_bg()
                return False

            # 等待弹窗关闭 / 卡片状态更新
            for _ in range(30):
                await asyncio.sleep(0.2)
                if await self.page.evaluate(VERIFY_CLAIMED_JS, title):
                    self._keep_bg()
                    return True

            self._keep_bg()
            return False
        except Exception:
            self._keep_bg()
            return False

    async def close(self):
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
            self.browser = None
            self.page = None
