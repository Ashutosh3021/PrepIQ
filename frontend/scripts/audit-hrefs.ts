/**
 * audit-hrefs.ts (SCRIPT-03)
 *
 * Recursively scans all .tsx/.ts files in pages/ and components/
 * for href="#" placeholder patterns.
 *
 * Usage: npx tsx scripts/audit-hrefs.ts
 * Exit: 0 if no href="#" found, 1 if any violations detected
 */

import * as fs from 'fs';
import * as path from 'path';

// ANSI color codes
const GREEN = '\x1b[32m';
const RED = '\x1b[31m';
const BOLD = '\x1b[1m';
const RESET = '\x1b[0m';
const CYAN = '\x1b[36m';

// Resolve paths relative to the frontend/ directory
const FRONTEND_DIR = path.resolve(__dirname, '..');
const PAGES_DIR = path.join(FRONTEND_DIR, 'pages');
const COMPONENTS_DIR = path.join(FRONTEND_DIR, 'components');

// Directories to skip during recursive scan
const SKIP_DIRS = new Set(['node_modules', '.next', '.git', 'public', 'styles', 'scripts', 'tests']);

/**
 * Regex patterns that match placeholder hrefs.
 * Matches: href="#", href='#', href=" # ", href=' #'
 */
const HREF_PATTERNS = [
  /href\s*=\s*["']\s*#\s*["']/gi,
  /href\s*=\s*["']\s*["']/gi, // href="" is also a placeholder
];

interface Violation {
  file: string;
  line: number;
  content: string;
  match: string;
}

/**
 * Recursively collect all .tsx and .ts files, skipping ignored directories.
 */
function collectFiles(dir: string, files: string[] = []): string[] {
  if (!fs.existsSync(dir)) return files;

  const entries = fs.readdirSync(dir, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);

    if (entry.isDirectory()) {
      if (!SKIP_DIRS.has(entry.name)) {
        collectFiles(fullPath, files);
      }
    } else if (entry.isFile() && (entry.name.endsWith('.tsx') || entry.name.endsWith('.ts'))) {
      files.push(fullPath);
    }
  }

  return files;
}

/**
 * Scan a single file for href="#" violations.
 */
function scanFile(filePath: string): Violation[] {
  const violations: Violation[] = [];
  const content = fs.readFileSync(filePath, 'utf-8');
  const lines = content.split('\n');
  const relativePath = path.relative(FRONTEND_DIR, filePath);

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const lineNumber = i + 1;

    for (const pattern of HREF_PATTERNS) {
      // Reset regex lastIndex for global patterns
      pattern.lastIndex = 0;
      const match = pattern.exec(line);
      if (match) {
        violations.push({
          file: relativePath,
          line: lineNumber,
          content: line.trim(),
          match: match[0],
        });
        break; // One violation per line is enough
      }
    }
  }

  return violations;
}

/**
 * Format and print a table row.
 */
function printViolation(v: Violation): void {
  console.log(
    `  ${CYAN}${v.file}${RESET}:${v.line}  →  ${RED}${v.match}${RESET}`
  );
  console.log(`    ${v.content.substring(0, 100)}${v.content.length > 100 ? '...' : ''}`);
}

// ─── Main ───────────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  console.log(`\n${BOLD}🔍 Auditing for placeholder hrefs...${RESET}\n`);

  // Collect all source files
  const pagesFiles = collectFiles(PAGES_DIR);
  const componentsFiles = collectFiles(COMPONENTS_DIR);
  const allFiles = [...pagesFiles, ...componentsFiles];

  console.log(`  Scanning ${allFiles.length} files (${pagesFiles.length} pages, ${componentsFiles.length} components)\n`);

  // Scan all files
  const allViolations: Violation[] = [];
  for (const file of allFiles) {
    const violations = scanFile(file);
    allViolations.push(...violations);
  }

  // Output results
  if (allViolations.length > 0) {
    console.log(`${BOLD}Violations found:${RESET}\n`);
    for (const v of allViolations) {
      printViolation(v);
      console.log();
    }

    console.log(`${'─'.repeat(80)}`);
    console.log(`${RED}${BOLD}❌ Found ${allViolations.length} placeholder href(s)${RESET}\n`);
    process.exit(1);
  } else {
    console.log(`${GREEN}✅ No placeholder hrefs found — all links are properly routed${RESET}\n`);
    process.exit(0);
  }
}

main().catch((err) => {
  console.error(`${RED}Fatal error:${RESET}`, err);
  process.exit(1);
});
