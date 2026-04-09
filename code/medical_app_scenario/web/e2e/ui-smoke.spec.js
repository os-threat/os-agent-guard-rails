// @ts-check
const { test, expect } = require("@playwright/test");

test.describe("Medical mini-app UI smoke", () => {
  test("home loads dashboard metrics", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: "Medical Mini App" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
    await expect(page.locator("#activeTrials")).not.toHaveText("-", { timeout: 20_000 });
    await expect(page.locator("#openAes")).not.toHaveText("-");
    await expect(page.locator("#pendingReviews")).not.toHaveText("-");
  });

  test("demo quick-pick M1 appears and Patients search finds Jordan Hayes", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("button", { name: /M1 ALLOW/i })).toBeVisible();
    await page.getByRole("button", { name: "Patients" }).click();
    await page.getByPlaceholder(/Search name/).fill("Jordan Hayes");
    await page.getByRole("button", { name: "Search" }).click();
    await expect(page.locator("#patientList li").first()).toContainText("Hayes");
  });

  test("prescription form has trial-related policy controls (MED-R06 hint)", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("button", { name: "Prescription Form" }).click();
    await expect(page.getByLabel(/Trial-related prescription/i)).toBeVisible();
    await expect(page.locator("#rxTrialGuardBanner")).toBeVisible();
  });
});
