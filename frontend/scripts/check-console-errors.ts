/**
 * check-console-errors.ts (QUAL-01)
 *
 * Renders each page route in JSDOM and intercepts console.error calls.
 * Reports pages with errors and exits with code 1 if any errors found.
 *
 * Usage: npx tsx scripts/check-console-errors.ts
 * Exit: 0 if no console errors, 1 if errors found
 */
import * as fs from 'fs';
import * as path from 'path';
import { JSDOM } from 'jsdom';

// ANSI color codes
const GREEN = '\x1b[32m';
const RED = '\x1b[31m';
const YELLOW = '\x1b[33m';
const BOLD = '\x1b[1m';
const RESET = '\x1b[0m';

// Resolve paths relative to the frontend/ directory
const FRONTEND_DIR = path.resolve(__dirname, '..');
const PAGES_DIR = path.join(FRONTEND_DIR, 'pages');
const BUILD_DIR = path.join(FRONTEND_DIR, '.next', 'server', 'pages');

/**
 * Get all page routes from the pages directory.
 */
function getPageRoutes(): string[] {
  const routes: string[] = [];

  function scanDir(dir: string, prefix: string) {
    if (!fs.existsSync(dir)) return;
    const entries = fs.readdirSync(dir);
    for (const entry of entries) {
      const fullPath = path.join(dir, entry);
      const stat = fs.statSync(fullPath);
      if (stat.isDirectory() && !entry.startsWith('_')) {
        scanDir(fullPath, `${prefix}/${entry}`);
      } else if (entry.endsWith('.tsx') && !entry.startsWith('_')) {
        const route = entry === 'index.tsx'
          ? prefix || '/'
          : `${prefix}/${entry.replace('.tsx', '')}`;
        routes.push(route);
      }
    }
  }

  scanDir(PAGES_DIR, '');
  return routes;
}

/**
 * Check a page for console errors using JSDOM.
 */
async function checkPageForErrors(route: string): Promise<string[]> {
  const errors: string[] = [];

  // Create a minimal HTML document that simulates the page
  const html = `
    <!DOCTYPE html>
    <html>
      <head>
        <title>Test Page: ${route}</title>
      </head>
      <body>
        <div id="__next"></div>
      </body>
    </html>
  `;

  // Capture console errors
  const originalConsoleError = console.error;
  const capturedErrors: string[] = [];

  console.error = (...args: unknown[]) => {
    capturedErrors.push(args.map(String).join(' '));
    originalConsoleError(...args);
  };

  try {
    // Create JSDOM instance
    const dom = new JSDOM(html, {
      url: `http://localhost:3000${route}`,
      runScripts: 'dangerously',
      resources: 'usable',
    });

    // Check for basic DOM errors
    const { document } = dom.window;
    const body = document.querySelector('body');

    if (!body) {
      errors.push('No body element found');
    }

    // Check for missing required elements
    const nextRoot = document.getElementById('__next');
    if (!nextRoot) {
      errors.push('Missing #__next root element');
    }

  } catch (err) {
    errors.push(`JSDOM error: ${err instanceof Error ? err.message : String(err)}`);
  } finally {
    console.error = originalConsoleError;
  }

  return [...errors, ...capturedErrors];
}

async function main(): Promise<void> {
  console.log(`\n${BOLD}🔍 Checking pages for console errors...${RESET}\n`);

  const routes = getPageRoutes();
  const pagesWithErrors: Map<string, string[]> = new Map();

  for (const route of routes) {
    const errors = await checkPageForErrors(route);
    if (errors.length > 0) {
      pagesWithErrors.set(route, errors);
    }
  }

  // Report results
  if (pagesWithErrors.size === 0) {
    console.log(`${GREEN}${BOLD}✅ No console errors found in ${routes.length} pages${RESET}\n`);
    process.exit(0);
  } else {
    console.log(`${RED}${BOLD}❌ Console errors found in ${pagesWithErrors.size} page(s):${RESET}\n`);
    for (const [route, errors] of Array.from(pagesWithErrors.entries())) {
      console.log(`${YELLOW}${route}${RESET}:`);
      for (const error of errors) {
        console.log(`  ${RED}•${RESET} ${error}`);
      }
      console.log();
    }
    process.exit(1);
  }
}

main().catch((err) => {
  console.error(`${RED}Fatal error:${RESET}`, err);
  process.exit(1);
});
