import { test, expect } from '@playwright/test';

test.describe('Audio2Text — Smoke Tests', () => {
  test('app loads and shows navigation', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('nav.sidebar')).toBeVisible();
    await expect(page.locator('nav.sidebar .sidebar-header')).toContainText('Audio2Text');
  });

  test('navigation tabs render', async ({ page }) => {
    await page.goto('/');
    const tabs = page.locator('.nav-item');
    await expect(tabs).toHaveCount(5);
  });

  test('transcribe view loads', async ({ page }) => {
    await page.goto('/');
    const recordBtn = page.locator('.record-btn');
    await expect(recordBtn).toBeVisible();
  });

  test('navigation to settings shows sub-tabs', async ({ page }) => {
    await page.goto('/');
    await page.locator('.nav-item', { hasText: 'Ajustes' }).click();
    const subTabs = page.locator('.sub-tab');
    await expect(subTabs).toHaveCount(8);
  });

  test('navigation to info shows version', async ({ page }) => {
    await page.goto('/');
    await page.locator('.nav-item', { hasText: 'Info' }).click();
    await expect(page.locator('.info-view')).toBeVisible();
    await expect(page.locator('.accent')).toContainText('0.16.0');
  });
});