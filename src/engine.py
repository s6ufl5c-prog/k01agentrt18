import os
import time
import re
from dataclasses import dataclass
from typing import Optional, Dict, Any
from patchright.sync_api import sync_playwright, BrowserContext, Page


@dataclass
class RedeemResult:
    success: bool
    status: str
    message: str
    plan_name: Optional[str] = None
    account_email: Optional[str] = None


class GoogleAutoRedeemer:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.redeemer_cfg = config.get("redeemer", {})
        self.headless = self.redeemer_cfg.get("headless", False)
        self.user_data_dir = os.path.abspath(
            self.redeemer_cfg.get("user_data_dir", "./google_profile")
        )
        self.timeout = self.redeemer_cfg.get("timeout", 30) * 1000
        self.auto_confirm = self.redeemer_cfg.get("auto_confirm", True)
        self.proxy_url = self.redeemer_cfg.get("proxy", "").strip()

    def _create_context(self, playwright_instance) -> BrowserContext:
        """Create a persistent browser context to retain Google session & avoid detection."""
        args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-infobars",
            "--disable-dev-shm-usage",
            "--lang=en-US,en,zh-CN,zh",
        ]

        proxy_cfg = None
        if self.proxy_url:
            proxy_cfg = {"server": self.proxy_url}

        os.makedirs(self.user_data_dir, exist_ok=True)

        context = playwright_instance.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            headless=self.headless,
            args=args,
            proxy=proxy_cfg,
            viewport={"width": 1280, "height": 850},
            locale="en-US",
        )
        return context

    def redeem(self, url: str) -> RedeemResult:
        """Execute redemption sequence for a given serviceactivation.google.com URL."""
        # Clean and validate url
        clean_url = self.clean_url(url)
        if not clean_url:
            return RedeemResult(
                success=False,
                status="INVALID_URL",
                message="URL format does not match Google Service Activation pattern."
            )

        with sync_playwright() as p:
            context = self._create_context(p)
            page = context.pages[0] if context.pages else context.new_page()
            page.set_default_timeout(self.timeout)

            try:
                # 1. Navigate to target url
                page.goto(clean_url, wait_until="domcontentloaded")
                page.wait_for_timeout(2000)

                # 2. Check if redirected to Google Accounts login page
                current_url = page.url
                if "accounts.google.com" in current_url:
                    # Login required
                    if self.headless:
                        context.close()
                        return RedeemResult(
                            success=False,
                            status="LOGIN_REQUIRED",
                            message="Google login required. Please run with headless: false to log in once."
                        )
                    else:
                        print("[!] Google login required. Waiting up to 180s for user to complete login...")
                        try:
                            page.wait_for_url(
                                lambda u: "serviceactivation.google.com" in u,
                                timeout=180000
                            )
                            page.wait_for_timeout(3000)
                        except Exception:
                            context.close()
                            return RedeemResult(
                                success=False,
                                status="LOGIN_TIMEOUT",
                                message="Login timed out."
                            )

                # 3. Analyze page state for expiration or already redeemed
                page_content = page.content()
                lower_content = page_content.lower()

                # Known failure keywords
                expired_keywords = [
                    "this offer is no longer valid",
                    "offer has expired",
                    "already redeemed",
                    "code has already been used",
                    "this promotion is not available",
                    "something went wrong",
                    "link is not valid",
                    "此优惠已失效",
                    "该优惠已被兑换",
                    "优惠已被使用",
                    "此链接无效",
                    "无法兑换",
                ]

                for kw in expired_keywords:
                    if kw in lower_content:
                        context.close()
                        return RedeemResult(
                            success=False,
                            status="EXPIRED_OR_USED",
                            message=f"Offer is expired or already redeemed (matched: '{kw}')"
                        )

                # 4. Extract offer / plan information
                plan_name = self._extract_plan_info(page)
                account_email = self._extract_account_info(page)

                # 5. Look for confirmation / subscribe button
                button_selectors = [
                    "button:has-text('Start subscription')",
                    "button:has-text('Agree and continue')",
                    "button:has-text('Agree & continue')",
                    "button:has-text('Get started')",
                    "button:has-text('Redeem')",
                    "button:has-text('Continue')",
                    "button:has-text('Confirm')",
                    "button:has-text('Subscribe')",
                    "button:has-text('开始订阅')",
                    "button:has-text('同意并继续')",
                    "button:has-text('兑换')",
                    "button:has-text('确认')",
                    "[role='button']:has-text('Agree')",
                    "[role='button']:has-text('Continue')",
                ]

                target_button = None
                for selector in button_selectors:
                    btn = page.locator(selector).first
                    if btn.count() > 0 and btn.is_visible():
                        target_button = btn
                        break

                if not target_button:
                    # Check if page is already on success state
                    if self._is_success_state(page):
                        context.close()
                        return RedeemResult(
                            success=True,
                            status="SUCCESS",
                            message="Subscription successfully activated!",
                            plan_name=plan_name,
                            account_email=account_email,
                        )

                    # Fallback check
                    context.close()
                    return RedeemResult(
                        success=False,
                        status="BUTTON_NOT_FOUND",
                        message="Confirmation button not detected. The offer might be region-locked, invalid, or already active.",
                        plan_name=plan_name,
                        account_email=account_email
                    )

                if not self.auto_confirm:
                    # If auto_confirm is false, notify user and pause
                    print(f"[*] Offer found: {plan_name}. Auto-confirm is disabled.")
                    print("[*] Browser is kept open for manual review. Press Ctrl+C when done.")
                    time.sleep(30)
                    context.close()
                    return RedeemResult(
                        success=True,
                        status="READY_FOR_CONFIRMATION",
                        message="Offer details detected. Ready for manual confirmation.",
                        plan_name=plan_name,
                        account_email=account_email,
                    )

                # Click redemption button
                target_button.click()
                page.wait_for_timeout(3000)

                # Check for secondary confirmation or payment method prompt
                # Google often opens a secondary modal or Google Pay iframe
                secondary_button_selectors = [
                    "button:has-text('Subscribe')",
                    "button:has-text('Start trial')",
                    "button:has-text('Complete redemption')",
                    "button:has-text('订阅')",
                    "button:has-text('完成兑换')",
                    "button:has-text('确认购买')",
                ]
                for sec_sel in secondary_button_selectors:
                    sec_btn = page.locator(sec_sel).first
                    if sec_btn.count() > 0 and sec_btn.is_visible():
                        sec_btn.click()
                        page.wait_for_timeout(3000)
                        break

                # Final success check
                if self._is_success_state(page):
                    context.close()
                    return RedeemResult(
                        success=True,
                        status="SUCCESS",
                        message="Subscription successfully redeemed and activated!",
                        plan_name=plan_name,
                        account_email=account_email,
                    )

                context.close()
                return RedeemResult(
                    success=True,
                    status="SUBMITTED",
                    message="Activation request submitted. Check Google Account / Play Store subscriptions.",
                    plan_name=plan_name,
                    account_email=account_email,
                )

            except Exception as ex:
                context.close()
                return RedeemResult(
                    success=False,
                    status="ERROR",
                    message=f"Error during redemption execution: {str(ex)}"
                )

    def _extract_plan_info(self, page: Page) -> Optional[str]:
        """Extract offer title from the DOM."""
        try:
            for sel in ["h1", "h2", "[role='heading']", ".offer-title", ".plan-name"]:
                heading = page.locator(sel).first
                if heading.count() > 0 and heading.is_visible():
                    text = heading.inner_text().strip()
                    if text and len(text) < 100:
                        return text
        except Exception:
            pass
        return "Google Subscription Offer"

    def _extract_account_info(self, page: Page) -> Optional[str]:
        """Extract the logged-in Google account email if visible."""
        try:
            content = page.content()
            match = re.search(r'[\w\.-]+@(?:gmail\.com|googlemail\.com)', content)
            if match:
                return match.group(0)
        except Exception:
            pass
        return None

    def _is_success_state(self, page: Page) -> bool:
        """Check if page transitioned to a known success state."""
        content = page.content().lower()
        success_keywords = [
            "welcome to",
            "you're all set",
            "subscription is now active",
            "offer redeemed",
            "thank you",
            "已成功开通",
            "订阅成功",
            "欢迎使用",
        ]
        return any(kw in content for kw in success_keywords)

    @staticmethod
    def clean_url(url: str) -> Optional[str]:
        """Extract and clean the valid serviceactivation.google.com URL."""
        match = re.search(
            r'https?://serviceactivation\.google\.com/subscription/new/[A-Za-z0-9_\-=%+]+',
            url.strip()
        )
        if match:
            return match.group(0)
        return None
