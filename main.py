#!/usr/bin/env python3
"""
Google Service Activation Auto-Redeemer (全自动/监听秒兑换神器)
"""

import sys
import argparse
from colorama import init, Fore, Style
from src.config import load_config
from src.engine import GoogleAutoRedeemer
from src.watcher import ClipboardWatcher
from src.notifier import send_notification

init(autoreset=True)

BANNER = rf"""{Fore.CYAN}
  ____                   _        ____          _                                
 / ___| ___   ___   __ _| | ___  |  _ \ ___  __| | ___  ___ _ __ ___   ___ _ __  
| |  _ / _ \ / _ \ / _` | |/ _ \ | |_) / _ \/ _` |/ _ \/ _ \ '_ ` _ \ / _ \ '__| 
| |_| | (_) | (_) | (_| | |  __/ |  _ <  __/ (_| |  __/  __/ | | | | |  __/ |    
 \____|\___/ \___/ \__, |_|\___| |_| \_\___|\__,_|\___|\___|_| |_| |_|\___|_|    
                   |___/                                                          
{Fore.YELLOW}           Google Service Activation Auto-Redeemer v1.0.0
{Fore.WHITE}      Automated, anti-detection redemption tool for Google Subscriptions
==================================================================================={Style.RESET_ALL}
"""


def print_banner():
    print(BANNER)


def run_redeem(url: str, config: dict):
    print(f"\n{Fore.CYAN}[*] Processing Link:{Style.RESET_ALL} {url}")
    redeemer = GoogleAutoRedeemer(config)
    result = redeemer.redeem(url)

    if result.success:
        print(f"{Fore.GREEN}[+] SUCCESS: {result.message}{Style.RESET_ALL}")
        if result.plan_name:
            print(f"{Fore.GREEN}    Offer Plan: {result.plan_name}{Style.RESET_ALL}")
        if result.account_email:
            print(f"{Fore.GREEN}    Account: {result.account_email}{Style.RESET_ALL}")
        send_notification(
            config,
            title="Google Subscription Redeemed Successfully",
            message=f"Plan: {result.plan_name or 'N/A'}\nAccount: {result.account_email or 'N/A'}\nStatus: {result.status}"
        )
    else:
        print(f"{Fore.RED}[-] FAILED [{result.status}]: {result.message}{Style.RESET_ALL}")
        send_notification(
            config,
            title="Google Subscription Redemption Failed",
            message=f"Status: {result.status}\nMessage: {result.message}\nURL: {url[:50]}..."
        )
    return result


def main():
    print_banner()

    parser = argparse.ArgumentParser(
        description="Google Service Activation Auto-Redeemer CLI"
    )
    parser.add_argument(
        "--url", "-u",
        type=str,
        help="Direct URL or redemption link to redeem immediately"
    )
    parser.add_argument(
        "--watch", "-w",
        action="store_true",
        help="Start clipboard monitoring mode (auto-snipes copied links)"
    )
    parser.add_argument(
        "--config", "-c",
        type=str,
        default="config.yaml",
        help="Path to YAML config file (default: config.yaml)"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless browser mode"
    )
    parser.add_argument(
        "--login-setup",
        action="store_true",
        help="Launch browser to manually log into your Google Account once"
    )

    args = parser.parse_args()
    config = load_config(args.config)

    if args.headless:
        config["redeemer"]["headless"] = True

    # Special helper: Login setup mode
    if args.login_setup:
        print(f"{Fore.YELLOW}[*] Launching browser for initial Google login setup...{Style.RESET_ALL}")
        config["redeemer"]["headless"] = False
        redeemer = GoogleAutoRedeemer(config)
        from patchright.sync_api import sync_playwright
        with sync_playwright() as p:
            context = redeemer._create_context(p)
            page = context.pages[0] if context.pages else context.new_page()
            page.goto("https://accounts.google.com")
            print(f"{Fore.GREEN}[*] Please log into your Google Account in the opened browser window.{Style.RESET_ALL}")
            print(f"{Fore.GREEN}[*] Once logged in, simply close the browser or press Ctrl+C.{Style.RESET_ALL}")
            try:
                page.wait_for_timeout(300000)  # 5 minutes
            except KeyboardInterrupt:
                pass
            context.close()
        print(f"{Fore.GREEN}[+] Profile saved! Future redemptions will use this logged-in session.{Style.RESET_ALL}")
        return

    if args.url:
        run_redeem(args.url, config)
    elif args.watch:
        poll_int = config.get("redeemer", {}).get("clipboard_poll_interval", 1.0)
        watcher = ClipboardWatcher(
            callback=lambda u: run_redeem(u, config),
            poll_interval=poll_int
        )
        watcher.start()
    else:
        # Interactive mode
        print(f"{Fore.YELLOW}Select an operation:{Style.RESET_ALL}")
        print("  1. Redeem a link now")
        print("  2. Start Clipboard Monitor (Sniper Mode)")
        print("  3. First-time Google Login Setup")
        print("  4. Exit")

        try:
            choice = input(f"\n{Fore.CYAN}Enter choice [1-4]: {Style.RESET_ALL}").strip()
            if choice == "1":
                url_input = input(f"{Fore.CYAN}Paste serviceactivation URL: {Style.RESET_ALL}").strip()
                if url_input:
                    run_redeem(url_input, config)
                else:
                    print(f"{Fore.RED}[-] URL cannot be empty.{Style.RESET_ALL}")
            elif choice == "2":
                poll_int = config.get("redeemer", {}).get("clipboard_poll_interval", 1.0)
                watcher = ClipboardWatcher(
                    callback=lambda u: run_redeem(u, config),
                    poll_interval=poll_int
                )
                watcher.start()
            elif choice == "3":
                print(f"{Fore.YELLOW}[*] Launching browser for Google login setup...{Style.RESET_ALL}")
                config["redeemer"]["headless"] = False
                redeemer = GoogleAutoRedeemer(config)
                from patchright.sync_api import sync_playwright
                with sync_playwright() as p:
                    context = redeemer._create_context(p)
                    page = context.pages[0] if context.pages else context.new_page()
                    page.goto("https://accounts.google.com")
                    print(f"{Fore.GREEN}[*] Please log into your Google Account in the browser.{Style.RESET_ALL}")
                    try:
                        page.wait_for_timeout(300000)
                    except KeyboardInterrupt:
                        pass
                    context.close()
                print(f"{Fore.GREEN}[+] Profile saved!{Style.RESET_ALL}")
            else:
                print("Exiting.")
        except KeyboardInterrupt:
            print("\nAborted.")


if __name__ == "__main__":
    main()
