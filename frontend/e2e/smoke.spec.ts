import { test, expect } from "@playwright/test";

test.describe("Smoke tests", () => {
  test("landing page redirects to /login and renders correctly", async ({
    page,
  }) => {
    await page.goto("/");

    // App redirects unknown routes to /login
    await expect(page).toHaveURL(/\/login/);

    // Login page renders the title and sign-in buttons
    await expect(page.getByRole("heading", { name: "FlowDay" })).toBeVisible();
    await expect(page.getByTestId("btn-google")).toBeVisible();
    await expect(page.getByTestId("btn-github")).toBeVisible();
  });

  test("login page has correct title", async ({ page }) => {
    await page.goto("/login");
    await expect(page).toHaveTitle(/FlowDay/);
  });
});
