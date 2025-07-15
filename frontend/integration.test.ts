import { test, expect } from '@playwright/test';

// Adjust baseURL as needed for your dev environment
const baseURL = 'http://localhost:3000';

test.describe('RAG App Integration', () => {
  test('Document upload, list, and delete', async ({ page }) => {
    await page.goto(`${baseURL}/chat`);
    // Upload a document (simulate file input)
    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.getByText('Upload files').click();
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles('README.md'); // Use a real file in your repo for testing
    // Wait for upload to complete
    await expect(page.getByText('README.md')).toBeVisible({ timeout: 10000 });
    // Delete the document
    await page.getByText('README.md').locator('button').click();
    await page.on('dialog', dialog => dialog.accept()); // Accept confirm dialog
    await expect(page.getByText('README.md')).not.toBeVisible({ timeout: 10000 });
  });

  test('Chat query and response', async ({ page }) => {
    await page.goto(`${baseURL}/chat`);
    await page.getByPlaceholder('Ask me anything about your documents...').fill('What is this document about?');
    await page.getByRole('button', { name: /send/i }).click();
    await expect(page.getByText(/assistant/i)).toBeVisible({ timeout: 10000 });
  });

  test('Admin actions', async ({ page }) => {
    await page.goto(`${baseURL}/chat`);
    await page.getByRole('button', { name: /reset kb/i }).click();
    await page.on('dialog', dialog => dialog.accept()); // Accept confirm dialog
    await expect(page.getByText(/knowledge base reset/i)).toBeVisible({ timeout: 10000 });
  });
}); 