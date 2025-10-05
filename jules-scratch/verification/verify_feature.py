from playwright.sync_api import sync_playwright, expect

def run_verification():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # Navigate to the registration page
            page.goto("http://localhost:5001/register")

            # Register a new user
            page.fill('input[name="username"]', "testuser")
            page.fill('input[name="password"]', "password")
            page.fill('input[name="confirm_password"]', "password")
            page.click('input[type="submit"]')

            # Log in
            page.wait_for_url("http://localhost:5001/login")
            page.fill('input[name="username"]', "testuser")
            page.fill('input[name="password"]', "password")
            page.click('input[type="submit"]')

            # Wait for the main page to load
            page.wait_for_url("http://localhost:5001/")

            # Find the first "Install" button and click it
            install_button = page.locator(".install-button").first
            expect(install_button).to_be_visible()
            install_button.click()

            # Wait for the compose modal to appear
            compose_modal = page.locator("#compose-modal")
            expect(compose_modal).to_be_visible()

            # Take a screenshot of the modal
            page.screenshot(path="jules-scratch/verification/verification.png")

            print("Verification script completed successfully.")

        except Exception as e:
            print(f"An error occurred during verification: {e}")

        finally:
            browser.close()

if __name__ == "__main__":
    run_verification()