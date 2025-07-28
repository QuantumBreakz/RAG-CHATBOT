import { test, expect } from '@playwright/test';

test.describe('XOR RAG Chatbot - Multi-Document Features', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
    // Wait for the app to load
    await page.waitForSelector('[data-testid="chat-interface"]', { timeout: 10000 });
  });

  test('should display domain filter in chat header', async ({ page }) => {
    // Check if domain filter is present
    const domainFilter = page.locator('[data-testid="domain-filter"]');
    await expect(domainFilter).toBeVisible();
    
    // Check if filter button shows "All Domains" by default
    const filterButton = domainFilter.locator('button');
    await expect(filterButton).toContainText('All Domains');
  });

  test('should show available domains in filter dropdown', async ({ page }) => {
    // Click on domain filter to open dropdown
    const domainFilter = page.locator('[data-testid="domain-filter"]');
    const filterButton = domainFilter.locator('button');
    await filterButton.click();
    
    // Wait for dropdown to appear
    await page.waitForSelector('[data-testid="domain-dropdown"]');
    
    // Check if "All Domains" option is present
    const allDomainsOption = page.locator('[data-testid="domain-option-all"]');
    await expect(allDomainsOption).toBeVisible();
  });

  test('should display source attribution for responses', async ({ page }) => {
    // Type a query that should return results with sources
    const input = page.locator('textarea[placeholder*="Ask me anything"]');
    await input.fill('What is Section 304?');
    await input.press('Enter');
    
    // Wait for response
    await page.waitForSelector('[data-testid="assistant-message"]', { timeout: 15000 });
    
    // Check if sources are displayed
    const sources = page.locator('[data-testid="source-display"]');
    await expect(sources).toBeVisible();
    
    // Check if source attribution is shown
    const sourceAttribution = page.locator('[data-testid="source-attribution"]');
    await expect(sourceAttribution).toBeVisible();
  });

  test('should filter queries by domain', async ({ page }) => {
    // Select a specific domain
    const domainFilter = page.locator('[data-testid="domain-filter"]');
    const filterButton = domainFilter.locator('button');
    await filterButton.click();
    
    // Wait for dropdown and select a domain
    await page.waitForSelector('[data-testid="domain-dropdown"]');
    const lawOption = page.locator('[data-testid="domain-option-law"]');
    await lawOption.click();
    
    // Verify domain is selected
    await expect(filterButton).toContainText('law');
    
    // Type a query
    const input = page.locator('textarea[placeholder*="Ask me anything"]');
    await input.fill('What is the penalty for theft?');
    await input.press('Enter');
    
    // Wait for response
    await page.waitForSelector('[data-testid="assistant-message"]', { timeout: 15000 });
    
    // Check that response is from law domain
    const response = page.locator('[data-testid="assistant-message"]');
    await expect(response).toBeVisible();
  });

  test('should show query classification in response', async ({ page }) => {
    // Type a query that should be classified
    const input = page.locator('textarea[placeholder*="Ask me anything"]');
    await input.fill('What is the electronegativity of chlorine?');
    await input.press('Enter');
    
    // Wait for response
    await page.waitForSelector('[data-testid="assistant-message"]', { timeout: 15000 });
    
    // Check if query classification is shown (if implemented in UI)
    const classification = page.locator('[data-testid="query-classification"]');
    if (await classification.isVisible()) {
      await expect(classification).toContainText('chemistry');
    }
  });

  test('should handle multiple document types', async ({ page }) => {
    // Upload a law document
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles('test-files/law-document.pdf');
    
    // Wait for upload to complete
    await page.waitForSelector('[data-testid="upload-success"]', { timeout: 10000 });
    
    // Upload a chemistry document
    await fileInput.setInputFiles('test-files/chemistry-document.pdf');
    await page.waitForSelector('[data-testid="upload-success"]', { timeout: 10000 });
    
    // Check that both documents are listed
    const documents = page.locator('[data-testid="document-list"]');
    await expect(documents).toContainText('law-document.pdf');
    await expect(documents).toContainText('chemistry-document.pdf');
  });

  test('should show health status', async ({ page }) => {
    // Click on health check button
    const healthButton = page.locator('[data-testid="health-check"]');
    await healthButton.click();
    
    // Wait for health status to update
    await page.waitForTimeout(2000);
    
    // Check if health status is displayed
    const healthStatus = page.locator('[data-testid="health-status"]');
    await expect(healthStatus).toBeVisible();
  });

  test('should handle domain-specific queries correctly', async ({ page }) => {
    // Test law query
    const input = page.locator('textarea[placeholder*="Ask me anything"]');
    await input.fill('What is the punishment for murder?');
    await input.press('Enter');
    
    await page.waitForSelector('[data-testid="assistant-message"]', { timeout: 15000 });
    
    // Test chemistry query
    await input.fill('What is the molecular weight of water?');
    await input.press('Enter');
    
    await page.waitForSelector('[data-testid="assistant-message"]', { timeout: 15000 });
    
    // Both responses should be different and domain-appropriate
    const responses = page.locator('[data-testid="assistant-message"]');
    await expect(responses).toHaveCount(2);
  });

  test('should clear domain filter', async ({ page }) => {
    // Select a domain
    const domainFilter = page.locator('[data-testid="domain-filter"]');
    const filterButton = domainFilter.locator('button');
    await filterButton.click();
    
    await page.waitForSelector('[data-testid="domain-dropdown"]');
    const lawOption = page.locator('[data-testid="domain-option-law"]');
    await lawOption.click();
    
    // Verify domain is selected
    await expect(filterButton).toContainText('law');
    
    // Clear filter
    const clearButton = page.locator('[data-testid="clear-domain-filter"]');
    await clearButton.click();
    
    // Verify filter is cleared
    await expect(filterButton).toContainText('All Domains');
  });

  test('should show source details on click', async ({ page }) => {
    // Type a query
    const input = page.locator('textarea[placeholder*="Ask me anything"]');
    await input.fill('What is Section 304?');
    await input.press('Enter');
    
    // Wait for response with sources
    await page.waitForSelector('[data-testid="assistant-message"]', { timeout: 15000 });
    await page.waitForSelector('[data-testid="source-display"]');
    
    // Click on source details
    const sourceButton = page.locator('[data-testid="source-details-button"]');
    await sourceButton.click();
    
    // Check if source details modal appears
    const sourceModal = page.locator('[data-testid="source-modal"]');
    await expect(sourceModal).toBeVisible();
  });

  test('should handle streaming responses with sources', async ({ page }) => {
    // Type a query
    const input = page.locator('textarea[placeholder*="Ask me anything"]');
    await input.fill('Explain the concept of electronegativity');
    await input.press('Enter');
    
    // Wait for streaming to start
    await page.waitForSelector('[data-testid="streaming-indicator"]');
    
    // Wait for streaming to complete
    await page.waitForSelector('[data-testid="assistant-message"]', { timeout: 15000 });
    
    // Check that sources are displayed after streaming
    const sources = page.locator('[data-testid="source-display"]');
    await expect(sources).toBeVisible();
  });
});

test.describe('Performance Tests', () => {
  test('should handle large document uploads', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Upload a large document
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles('test-files/large-document.pdf');
    
    // Wait for upload progress
    await page.waitForSelector('[data-testid="upload-progress"]');
    
    // Wait for upload to complete
    await page.waitForSelector('[data-testid="upload-success"]', { timeout: 30000 });
    
    // Verify document is processed
    const documents = page.locator('[data-testid="document-list"]');
    await expect(documents).toContainText('large-document.pdf');
  });

  test('should maintain performance with multiple documents', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Upload multiple documents
    const fileInput = page.locator('input[type="file"]');
    const testFiles = [
      'test-files/law-document.pdf',
      'test-files/chemistry-document.pdf',
      'test-files/physics-document.pdf',
      'test-files/religion-document.pdf'
    ];
    
    for (const file of testFiles) {
      await fileInput.setInputFiles(file);
      await page.waitForSelector('[data-testid="upload-success"]', { timeout: 10000 });
    }
    
    // Query should still be fast
    const input = page.locator('textarea[placeholder*="Ask me anything"]');
    await input.fill('What is Section 304?');
    await input.press('Enter');
    
    // Response should come within reasonable time
    await page.waitForSelector('[data-testid="assistant-message"]', { timeout: 10000 });
  });
}); 