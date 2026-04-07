/**
 * check-css-variables.ts (QUAL-04)
 *
 * Scans PROTOTYPE-D and PROTOTYPE-M HTML files for CSS variable usage,
 * checks each variable exists in styles/globals.css, and reports missing ones.
 *
 * Usage: npx tsx scripts/check-css-variables.ts
 * Exit: 0 if all variables exist, 1 if any missing
 */
import * as fs from 'fs';
import * as path from 'path';

// ANSI color codes
const GREEN = '\x1b[32m';
const RED = '\x1b[31m';
const YELLOW = '\x1b[33m';
const BOLD = '\x1b[1m';
const RESET = '\x1b[0m';
const CYAN = '\x1b[36m';

// Resolve paths
const FRONTEND_DIR = path.resolve(__dirname, '..');
const PROJECT_ROOT = path.resolve(FRONTEND_DIR, '..');
const PROTOTYPE_D = path.join(PROJECT_ROOT, 'PROTOTYPE-D');
const PROTOTYPE_M = path.join(PROJECT_ROOT, 'PROTOTYPE-M');
const GLOBALS_CSS = path.join(FRONTEND_DIR, 'styles', 'globals.css');

/**
 * Recursively find all .html files in a directory.
 */
function findHtmlFiles(dir: string): string[] {
  if (!fs.existsSync(dir)) return [];
  const files: string[] = [];
  for (const entry of fs.readdirSync(dir)) {
    const fullPath = path.join(dir, entry);
    const stat = fs.statSync(fullPath);
    if (stat.isDirectory()) {
      files.push(...findHtmlFiles(fullPath));
    } else if (entry.endsWith('.html')) {
      files.push(fullPath);
    }
  }
  return files;
}

/**
 * Extract CSS variable references from HTML content.
 * Matches patterns like var(--color-primary) or var(--spacing-4).
 */
function extractCssVariables(content: string): Set<string> {
  const varRegex = /var\((--[a-zA-Z0-9_-]+)/g;
  const variables = new Set<string>();
  let match;
  while ((match = varRegex.exec(content)) !== null) {
    variables.add(match[1]);
  }
  return variables;
}

/**
 * Extract CSS variable definitions from globals.css.
 */
function extractDefinedVariables(cssContent: string): Set<string> {
  const varRegex = /(--[a-zA-Z0-9_-]+)\s*:/g;
  const variables = new Set<string>();
  let match;
  while ((match = varRegex.exec(cssContent)) !== null) {
    variables.add(match[1]);
  }
  return variables;
}

async function main(): Promise<void> {
  console.log(`\n${BOLD}🔍 Checking CSS variable consistency...${RESET}\n`);

  // Read globals.css
  if (!fs.existsSync(GLOBALS_CSS)) {
    console.log(`${RED}❌ globals.css not found at: ${GLOBALS_CSS}${RESET}\n`);
    process.exit(1);
  }

  const globalsCss = fs.readFileSync(GLOBALS_CSS, 'utf-8');
  const definedVariables = extractDefinedVariables(globalsCss);

  console.log(`  ${CYAN}Defined variables in globals.css:${RESET} ${definedVariables.size}`);

  // Scan prototype directories
  const prototypeDirs = [
    { name: 'PROTOTYPE-D', path: PROTOTYPE_D },
    { name: 'PROTOTYPE-M', path: PROTOTYPE_M },
  ];

  const allUsedVariables = new Set<string>();
  const filesScanned: string[] = [];

  for (const proto of prototypeDirs) {
    const htmlFiles = findHtmlFiles(proto.path);
    for (const file of htmlFiles) {
      const content = fs.readFileSync(file, 'utf-8');
      const vars = extractCssVariables(content);
      for (const v of Array.from(vars)) {
        allUsedVariables.add(v);
      }
      if (vars.size > 0) {
        filesScanned.push(path.relative(FRONTEND_DIR, file));
      }
    }
  }

  console.log(`  ${CYAN}Prototype files scanned:${RESET} ${filesScanned.length}`);
  console.log(`  ${CYAN}Unique CSS variables used:${RESET} ${allUsedVariables.size}\n`);

  // Check for missing variables
  const missingVariables: string[] = [];
  for (const usedVar of Array.from(allUsedVariables)) {
    if (!definedVariables.has(usedVar)) {
      missingVariables.push(usedVar);
    }
  }

  // Report results
  if (missingVariables.length === 0) {
    console.log(`${GREEN}${BOLD}✅ All ${allUsedVariables.size} CSS variables are defined in globals.css${RESET}\n`);
    process.exit(0);
  } else {
    console.log(`${RED}${BOLD}❌ ${missingVariables.length} CSS variable(s) used in prototypes but missing from globals.css:${RESET}\n`);
    for (const variable of missingVariables) {
      console.log(`  ${RED}•${RESET} ${variable}`);
    }
    console.log(`\n  Add these variables to ${GLOBALS_CSS}\n`);
    process.exit(1);
  }
}

main().catch((err) => {
  console.error(`${RED}Fatal error:${RESET}`, err);
  process.exit(1);
});
