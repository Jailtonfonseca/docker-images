from playwright.sync_api import sync_playwright, expect
import time

def generate_screenshots(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    new_template_url = "https://raw.githubusercontent.com/Lissy93/portainer-templates/main/templates_v3.json"
    username = "testuser"
    password = "password123"

    try:
        # 1. Registration Page
        print("--- Capturing Registration Page ---")
        page.goto("http://localhost:5001")
        expect(page).to_have_url("http://localhost:5001/register")
        page.screenshot(path="jules-scratch/screenshots/01_registration_page.png")
        print("Screenshot of registration page captured.")

        page.get_by_label("Username").fill(username)
        page.locator("#password").fill(password)
        page.locator("#confirm_password").fill(password)
        page.get_by_role("button", name="Sign Up").click()

        # 2. Login Page
        print("\n--- Capturing Login Page ---")
        expect(page).to_have_url("http://localhost:5001/login")
        page.screenshot(path="jules-scratch/screenshots/02_login_page.png")
        print("Screenshot of login page captured.")

        page.get_by_label("Username").fill(username)
        page.get_by_label("Password").fill(password)
        page.get_by_role("button", name="Login").click()

        expect(page).to_have_url("http://localhost:5001/")
        print("Login successful.")

        # 3. Add Template Source
        print("\n--- Adding Template Source ---")
        page.goto("http://localhost:5001/settings")
        page.locator("textarea").fill(new_template_url)
        page.get_by_role("button", name="Save Settings").click()
        expect(page.locator("#messageArea")).to_contain_text("Template sources saved and cache updated.", timeout=20000)
        print("New template source added.")

        # 4. Main Page (Home)
        print("\n--- Capturing Main Page ---")
        page.goto("http://localhost:5001/")
        page.locator(".template-card").first.wait_for(state='visible', timeout=20000)
        page.screenshot(path="jules-scratch/screenshots/03_main_page.png")
        print("Screenshot of main page captured.")

        # 5. App Details Page
        print("\n--- Capturing App Details Page ---")
        page.locator(".template-card a").first.click()
        expect(page.get_by_role("heading", name="Details:")).to_be_visible()
        page.screenshot(path="jules-scratch/screenshots/04_app_details_page.png")
        print("Screenshot of app details page captured.")

        # 6. Dashboard Page
        print("\n--- Capturing Dashboard Page ---")
        page.get_by_role("link", name="Dashboard").click()
        expect(page).to_have_url("http://localhost:5001/dashboard")
        expect(page.get_by_role("heading", name="System Dashboard")).to_be_visible()
        page.screenshot(path="jules-scratch/screenshots/06_dashboard_page.png")
        print("Screenshot of dashboard page captured.")

        print("\nAll screenshots generated successfully!")

    except Exception as e:
        print(f"\nAn error occurred during screenshot generation: {e}")
        page.screenshot(path="jules-scratch/screenshots/error.png")

    finally:
        browser.close()

with sync_playwright() as playwright:
    generate_screenshots(playwright)