/**
 * check-css-variables.ts (QUAL-04)
 *
 * Scans the Next.js app source (pages/components/lib/styles) for `var(--x)`
 * usage and verifies every referenced custom property is defined in a CSS file.
 *
 * The previous version only scanned the deleted PROTOTYPE-D/M directories, so
 * it always reported "0 CSS variables used" and passed — a false green.
 *
 * Usage: npx tsx scripts/check-css-variables.ts
 * Exit: 0 if all variables are defined, 1 if any missing or nothing was scanned
 */
import * as fs from 'fs';
import * as path from 'path';

// ANSI color codes
const GREEN = '\x1b[32m';
const RED = '\x1b[31m';
const BOLD = '\x1b[1m';
const RESET = '\x1b[0m';
const CYAN = '\x1b[36m';

const FRONTEND_DIR = path.resolve(__dirname, '..');

// Directories that make up the app.
const SOURCE_DIRS = ['pages', 'components', 'lib', 'styles', 'public'];
const SOURCE_EXTENSIONS = new Set(['.tsx', '.ts', '.jsx', '.js', '.css']);
const IGNORE_DIRS = new Set(['node_modules', '.next', 'out', 'coverage']);

function findFiles(dir: string, extensions: Set<string>): string[] {
  if (!fs.existsSync(dir)) return [];
  const files: string[] = [];
  for (const entry of fs.readdirSync(dir)) {
    if (IGNORE_DIRS.has(entry)) continue;
    const fullPath = path.join(dir, entry);
    const stat = fs.statSync(fullPath);
    if (stat.isDirectory()) {
      files.push(...findFiles(fullPath, extensions));
    } else if (extensions.has(path.extname(entry))) {
      files.push(fullPath);
    }
  }
  return files;
}

function extractCssVariables(content: string): Set<string> {
  const varRegex = /var\(\s*(--[a-zA-Z0-9_-]+)/g;
  const variables = new Set<string>();
  let match;
  while ((match = varRegex.exec(content)) !== null) {
    variables.add(match[1]);
  }
  return variables;
}

function extractDefinedVariables(cssContent: string): Set<string> {
  const varRegex = /(--[a-zA-Z0-9_-]+)\s*:/g;
  const variables = new Set<string>();
  let match;
  while ((match = varRegex.exec(cssContent)) !== null) {
    variables.add(match[1]);
  }
  return variables;
}

function main(): void {
  console.log(`\n${BOLD}Checking CSS variable consistency...${RESET}\n`);

  const cssFiles = findFiles(FRONTEND_DIR, new Set(['.css']));
  const definedVariables = new Set<string>();
  for (const file of cssFiles) {
    for (const v of extractDefinedVariables(fs.readFileSync(file, 'utf-8'))) {
      definedVariables.add(v);
    }
  }

  console.log(`  ${CYAN}Defined custom properties in CSS:${RESET} ${definedVariables.size}`);

  const sourceFiles: string[] = [];
  for (const dir of SOURCE_DIRS) {
    sourceFiles.push(...findFiles(path.join(FRONTEND_DIR, dir), SOURCE_EXTENSIONS));
  }

  if (sourceFiles.length === 0) {
    console.log(
      `${RED}${BOLD}No source files scanned — the checker is not looking at anything.${RESET}\n`
    );
    process.exit(1);
  }

  // Custom properties can also be defined in source: inline style objects
  // (`'--s': '48px'`) and template-string CSS blocks (`--x: 1px`).
  for (const file of sourceFiles) {
    const content = fs.readFileSync(file, 'utf-8');
    const defRegex = /(['"]?)(--[a-zA-Z0-9_-]+)\1\s*:/g;
    let m;
    while ((m = defRegex.exec(content)) !== null) {
      definedVariables.add(m[2]);
    }
  }

  const missingByFile = new Map<string, string[]>();
  let usageCount = 0;
  const allUsed = new Set<string>();

  for (const file of sourceFiles) {
    const content = fs.readFileSync(file, 'utf-8');
    const used = extractCssVariables(content);
    if (used.size === 0) continue;
    usageCount += 1;
    const missing: string[] = [];
    for (const v of used) {
      allUsed.add(v);
      if (!definedVariables.has(v)) missing.push(v);
    }
    if (missing.length > 0) {
      missingByFile.set(path.relative(FRONTEND_DIR, file), missing);
    }
  }

  console.log(`  ${CYAN}Source files scanned:${RESET} ${sourceFiles.length}`);
  console.log(`  ${CYAN}Files using custom properties:${RESET} ${usageCount}`);
  console.log(
    `  ${CYAN}Unique custom properties used:${RESET} ${allUsed.size} (checked against CSS definitions)\n`
  );

  if (missingByFile.size === 0) {
    console.log(
      `${GREEN}${BOLD}All ${allUsed.size} referenced custom properties are defined${RESET}\n`
    );
    process.exit(0);
  }

  console.log(
    `${RED}${BOLD}Custom properties referenced in source but not defined in CSS:${RESET}\n`
  );
  for (const [file, vars] of missingByFile) {
    console.log(`  ${RED}${file}${RESET}`);
    for (const v of vars) {
      console.log(`    • ${v}`);
    }
  }
  console.log(`\n  Define them in ${path.join(FRONTEND_DIR, 'styles')}\n`);
  process.exit(1);
}

main();
