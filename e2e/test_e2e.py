"""End-to-end system tests: a real browser against the running stack.

  docker compose up -d
  python -m pytest e2e -v

Drives Chromium through the same flows a user takes, against the seeded demo
account. Each test cleans up whatever it creates.
"""
import os
import re
import time

import pytest
from playwright.sync_api import Page, expect, sync_playwright

BASE = os.environ.get("VIGIL_URL", "http://localhost:3000")
EMAIL, PASSWORD = "demo@vigil.dev", "vigil-demo-2026"

pytestmark = pytest.mark.e2e


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        yield b
        b.close()


@pytest.fixture
def page(browser) -> Page:
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    p = ctx.new_page()
    yield p
    ctx.close()


def sign_in(page: Page, password: str = PASSWORD) -> None:
    page.goto(f"{BASE}/login")
    page.fill("input[type=email]", EMAIL)
    page.fill("input[type=password]", password)
    page.get_by_role("button", name="Sign in").click()


def test_signed_out_visitors_are_sent_to_sign_in(page):
    page.goto(BASE)
    expect(page).to_have_url(re.compile(r"/login$"))


def test_a_wrong_password_shows_a_readable_error(page):
    sign_in(page, password="not-the-password")
    expect(page.get_by_text("Email or password is incorrect.")).to_be_visible()


def test_sign_in_shows_every_monitor_on_one_screen(page):
    sign_in(page)
    expect(page.get_by_role("heading", name="Everything you asked us to watch")).to_be_visible()
    expect(page.locator("a.row")).to_have_count(4)
    expect(page.get_by_text("Recent incidents")).to_be_visible()


def test_monitor_lifecycle_add_pause_resume_and_confirmed_delete(page):
    name = f"E2E check {int(time.time())}"
    sign_in(page)
    page.get_by_role("button", name="Add monitor").click()
    page.fill("#mname", name)
    page.fill("#murl", "https://example.com/")
    page.get_by_role("button", name="Start watching").click()
    row = page.locator("a.row", has_text=name)
    expect(row).to_contain_text("pending")                     # US-06: appears immediately

    row.click()
    expect(page.get_by_role("heading", name=name)).to_be_visible()
    page.get_by_role("button", name="Pause checks").click()    # US-12 AC1
    expect(page.get_by_text("· paused")).to_be_visible()
    page.get_by_role("button", name="Resume checks").click()
    expect(page.get_by_role("button", name="Pause checks")).to_be_visible()

    page.once("dialog", lambda d: d.dismiss())                 # US-12 AC3: cancel keeps it
    page.get_by_role("button", name="Stop watching").click()
    expect(page.get_by_role("heading", name=name)).to_be_visible()

    page.once("dialog", lambda d: d.accept())                  # confirm deletes it
    page.get_by_role("button", name="Stop watching").click()
    expect(page).to_have_url(f"{BASE}/")
    expect(page.locator("a.row", has_text=name)).to_have_count(0)


def test_monitor_detail_draws_the_response_time_chart(page):
    sign_in(page)
    page.locator("a.row").first.click()
    expect(page.get_by_text("Response time, last 24 hours")).to_be_visible()
    expect(page.locator("svg").first).to_be_visible()
    expect(page.get_by_text("Latest checks")).to_be_visible()


def test_the_public_status_page_needs_no_login(page):
    page.goto(f"{BASE}/status/demo")
    expect(page.get_by_text("Live from Vigil", exact=False)).to_be_visible()
    expect(page.get_by_text("Checkout API")).to_be_visible()
    expect(page.get_by_text("Legacy invoice worker")).to_have_count(0)   # private monitor stays private
