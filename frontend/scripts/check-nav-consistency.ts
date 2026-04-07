/**
 * check-nav-consistency.ts (SCRIPT-01)
 *
 * Validates that every NavItem.path in DESKTOP_NAV and MOBILE_NAV
 * maps to an existing page file. Also checks for duplicate paths.
 *
 * Usage: npx tsx scripts/check-nav-consistency.ts
 * Exit: 0 if all checks pass, 1 if any issues found
 */

import { DESKTOP_NAV, MOBILE_NAV } from '../lib/navigation';
import type { NavItem } from '../lib/types/nav.types';
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
 * Map a nav path like '/desktop/dashboard' to possible page file paths.
 * Handles:
 *   - /desktop/foo → pages/desktop/foo.tsx
 *   - /desktop/foo/bar → pages/desktop/foo/bar.tsx (or bar/index.tsx)
 *   - /desktop → pages/desktop/index.tsx
 */
function pathToPageFiles(navPath: string): string[] {
  // Strip leading slash
  const cleanPath = navPath.replace(/^\//, '');
  if (!cleanPath) {
    return [path.join(PAGES_DIR, 'index.tsx')];
  }

  const segments = cleanPath.split('/');
  const directFile = path.join(PAGES_DIR, `${cleanPath}.tsx`);
  const indexFile = path.join(PAGES_DIR, cleanPath, 'index.tsx');

  return [directFile, indexFile];
}

/**
 * Check if any of the possible page files exist.
 */
function pageExists(navPath: string): { exists: boolean; foundFile: string | null } {
  const candidates = pathToPageFiles(navPath);
  for (const candidate of candidates) {
    if (fs.existsSync(candidate)) {
      return { exists: true, foundFile: path.relative(FRONTEND_DIR, candidate) };
    }
  }
  return { exists: false, foundFile: null };
}

/**
 * Check for duplicate paths within a nav array.
 */
function findDuplicates(items: NavItem[]): string[] {
  const seen = new Map<string, string[]>();
  for (const item of items) {
    const existing = seen.get(item.path) || [];
    existing.push(item.name);
    seen.set(item.path, existing);
  }

  const duplicates: string[] = [];
  for (const [pathValue, names] of Array.from(seen.entries())) {
    if (names.length > 1) {
      duplicates.push(`${pathValue} (${names.join(', ')})`);
    }
  }
  return duplicates;
}

/**
 * Format and print a table row.
 */
function printRow(variant: string, name: string, navPath: string, status: string, detail: string): void {
  const statusColor = status === '✅' ? GREEN : RED;
  const variantColor = variant === 'desktop' ? CYAN : YELLOW;

  console.log(
    `  ${variantColor}${variant.padEnd(8)}${RESET} | ${name.padEnd(14)} | ${navPath.padEnd(28)} | ${statusColor}${status}${RESET} ${detail}`
  );
}

// ─── Main ───────────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  console.log(`\n${BOLD}🔍 Checking navigation consistency...${RESET}\n`);

  let issues = 0;

  // Check for duplicate paths
  console.log(`${BOLD}Duplicate path check:${RESET}`);
  const desktopDupes = findDuplicates(DESKTOP_NAV);
  const mobileDupes = findDuplicates(MOBILE_NAV);

  if (desktopDupes.length === 0 && mobileDupes.length === 0) {
    console.log(`  ${GREEN}✅${RESET} No duplicate paths found\n`);
  } else {
    for (const dupe of [...desktopDupes, ...mobileDupes]) {
      console.log(`  ${RED}❌${RESET} Duplicate: ${dupe}`);
      issues++;
    }
    console.log();
  }

  // Check nav item paths map to page files
  console.log(`${BOLD}Path-to-page mapping:${RESET}`);
  console.log(`  ${'Variant'.padEnd(8)} | ${'Name'.padEnd(14)} | ${'Path'.padEnd(28)} | Status\n`);

  const allNav = [
    ...DESKTOP_NAV.map((item) => ({ ...item, variant: 'desktop' as const })),
    ...MOBILE_NAV.map((item) => ({ ...item, variant: 'mobile' as const })),
  ];

  for (const item of allNav) {
    const { exists, foundFile } = pageExists(item.path);
    if (exists) {
      printRow(item.variant, item.name, item.path, '✅', `→ ${foundFile}`);
    } else {
      printRow(item.variant, item.name, item.path, '❌', `→ page not found`);
      issues++;
    }
  }

  // Summary
  console.log(`\n${'─'.repeat(80)}`);
  if (issues === 0) {
    console.log(`${GREEN}${BOLD}✅ All checks passed — ${allNav.length} nav items, 0 issues${RESET}\n`);
    process.exit(0);
  } else {
    console.log(`${RED}${BOLD}❌ Found ${issues} issue(s)${RESET}\n`);
    process.exit(1);
  }
}

main().catch((err) => {
  console.error(`${RED}Fatal error:${RESET}`, err);
  process.exit(1);
});
