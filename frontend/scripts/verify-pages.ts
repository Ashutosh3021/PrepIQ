/**
 * verify-pages.ts (SCRIPT-02)
 *
 * Scans pages/desktop/ and pages/mobile/ for all .tsx files and verifies
 * each is referenced in nav constants OR is a known standalone page.
 *
 * Usage: npx tsx scripts/verify-pages.ts
 * Exit: 0 if all pages accounted for, 1 if orphan pages found
 */

import { DESKTOP_NAV, MOBILE_NAV } from '../lib/navigation';
import * as fs from 'fs';
import * as path from 'path';

// ANSI color codes
const GREEN = '\x1b[32m';
const RED = '\x1b[31m';
const YELLOW = '\x1b[33m';
const BOLD = '\x1b[1m';
const RESET = '\x1b[0m';
const CYAN = '\x1b[36m';

// Resolve paths relative to the frontend/ directory
const FRONTEND_DIR = path.resolve(__dirname, '..');
const PAGES_DIR = path.join(FRONTEND_DIR, 'pages');

/**
 * Known standalone pages that are not in nav but should exist.
 */
const KNOWN_STANDALONES = [
  'pages/index.tsx',
  'pages/404.tsx',
  'pages/_app.tsx',
  'pages/_document.tsx',
  'pages/desktop/index.tsx',
  'pages/mobile/index.tsx',
  'pages/desktop/start-test.tsx',
  'pages/mobile/start-test.tsx',
  'pages/mobile/profile.tsx', // Not in mobile bottom nav (space-limited) but accessible via settings
];

/**
 * Get all .tsx files in a directory (non-recursive, top-level only).
 */
function getTsxFiles(dir: string): string[] {
  if (!fs.existsSync(dir)) return [];
  return fs
    .readdirSync(dir)
    .filter((file) => file.endsWith('.tsx') && !file.startsWith('_'))
    .map((file) => path.join(dir, file));
}

/**
 * Convert a page file path to a nav-style path.
 * e.g., pages/desktop/dashboard.tsx → /desktop/dashboard
 */
function fileToNavPath(filePath: string): string {
  const relativePath = path.relative(PAGES_DIR, filePath);
  // Remove .tsx extension and normalize Windows backslashes to forward slashes
  const withoutExt = relativePath.replace(/\.tsx$/, '').replace(/\\/g, '/');
  return `/${withoutExt}`;
}

/**
 * Get all nav paths from both nav arrays.
 */
function getAllNavPaths(): Set<string> {
  const paths = new Set<string>();
  for (const item of [...DESKTOP_NAV, ...MOBILE_NAV]) {
    paths.add(item.path);
  }
  return paths;
}

/**
 * Format and print a table row.
 */
function printRow(pageFile: string, navPath: string, status: string, detail: string): void {
  const statusColor = status === '✅' ? GREEN : status === '⚠️' ? YELLOW : RED;

  console.log(
    `  ${pageFile.padEnd(40)} | ${navPath.padEnd(28)} | ${statusColor}${status}${RESET} ${detail}`
  );
}

// ─── Main ───────────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  console.log(`\n${BOLD}🔍 Verifying page coverage...${RESET}\n`);

  let issues = 0;
  const navPaths = getAllNavPaths();

  // Collect all page files from desktop/ and mobile/ (excluding index.tsx)
  const desktopDir = path.join(PAGES_DIR, 'desktop');
  const mobileDir = path.join(PAGES_DIR, 'mobile');

  const desktopFiles = getTsxFiles(desktopDir);
  const mobileFiles = getTsxFiles(mobileDir);
  const allFiles = [...desktopFiles, ...mobileFiles];

  console.log(`${BOLD}Page coverage:${RESET}`);
  console.log(`  ${'Page File'.padEnd(40)} | ${'Nav Path'.padEnd(28)} | Status\n`);

  const orphanedPages: string[] = [];

  for (const file of allFiles) {
    const relativePath = path.relative(FRONTEND_DIR, file).replace(/\\/g, '/');
    const navPath = fileToNavPath(file);
    const isNavReferenced = navPaths.has(navPath);
    const isKnownStandalone = KNOWN_STANDALONES.includes(relativePath);

    if (isNavReferenced) {
      printRow(relativePath, navPath, '✅', '→ linked in nav');
    } else if (isKnownStandalone) {
      printRow(relativePath, navPath, '✅', '→ known standalone');
    } else {
      printRow(relativePath, navPath, '⚠️', '→ orphan (no nav entry)');
      orphanedPages.push(relativePath);
    }
  }

  // Check that every nav path has a corresponding page file
  console.log(`\n${BOLD}Nav path coverage:${RESET}\n`);

  const missingPages: string[] = [];
  for (const navPath of Array.from(navPaths)) {
    const possibleFiles = [
      path.join(PAGES_DIR, `${navPath.replace(/^\//, '')}.tsx`),
      path.join(PAGES_DIR, navPath.replace(/^\//, ''), 'index.tsx'),
    ];

    const exists = possibleFiles.some((f) => fs.existsSync(f));
    if (!exists) {
      console.log(`  ${RED}❌${RESET} Nav path "${navPath}" has no matching page file`);
      missingPages.push(navPath);
      issues++;
    }
  }

  if (missingPages.length === 0) {
    console.log(`  ${GREEN}✅${RESET} All nav paths have matching page files`);
  }

  // Summary
  console.log(`\n${'─'.repeat(100)}`);

  if (orphanedPages.length > 0) {
    console.log(`\n${YELLOW}⚠️  Orphan pages (not in nav, not in known standalones):${RESET}`);
    for (const orphan of orphanedPages) {
      console.log(`    - ${orphan}`);
    }
    console.log(
      `\n  Add these to KNOWN_STANDALONES in verify-pages.ts or add them to navigation.ts`
    );
    issues += orphanedPages.length;
  }

  if (issues === 0) {
    console.log(
      `\n${GREEN}${BOLD}✅ All pages accounted for — ${allFiles.length} pages, 0 orphans${RESET}\n`
    );
    process.exit(0);
  } else {
    console.log(`\n${RED}${BOLD}❌ Found ${issues} issue(s)${RESET}\n`);
    process.exit(1);
  }
}

main().catch((err) => {
  console.error(`${RED}Fatal error:${RESET}`, err);
  process.exit(1);
});
