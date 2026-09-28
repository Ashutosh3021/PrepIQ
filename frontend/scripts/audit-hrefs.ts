/**
 * audit-hrefs.ts (SCRIPT-03)
 *
 * Recursively scans all .tsx/.ts files in pages/ and components/ for:
 *   1. placeholder hrefs (href="#" / href="") — SCRIPT-03 original check
 *   2. broken route targets — every static href / router.push / router.replace
 *      / location href that points at a path with no matching file in pages/
 *
 * The original script only hunted for `href="#"` and then claimed "all links
 * are properly routed", which is not what it verified. Non-existent routes
 * (e.g. /privacy, /desktop/generate-test) passed silently.
 *
 * Usage: npx tsx scripts/audit-hrefs.ts
 * Exit: 0 if clean, 1 if any placeholder or broken route found
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

// Resolve paths relative to the frontend/ directory
const FRONTEND_DIR = path.resolve(__dirname, '..');
const PAGES_DIR = path.join(FRONTEND_DIR, 'pages');

// Directories to skip during recursive scan
const SKIP_DIRS = new Set(['node_modules', '.next', '.git', 'public', 'styles', 'scripts', 'tests']);

/** Regex patterns that match placeholder hrefs. */
const HREF_PATTERNS = [
  /href\s*=\s*["']\s*#\s*["']/gi,
  /href\s*=\s*["']\s*["']/gi, // href="" is also a placeholder
];

/**
 * Static route targets we can resolve without running the app:
 * href="/...", router.push('/...'), router.replace("/..."),
 * pathname: '/...', location.href = '/...'
 */
const ROUTE_PATTERNS: RegExp[] = [
  /href\s*=\s*["'](\/[^"']*)["']/g,
  /router\.(?:push|replace)\(\s*["'](\/[^"']*)["']/g,
  /router\.(?:push|replace)\(\s*\{\s*pathname\s*:\s*["'](\/[^"']*)["']/g,
  /(?:window\.)?location\.href\s*=\s*["'](\/[^"']*)["']/g,
];

/** External / non-page targets that are fine as-is. */
function isExternal(target: string): boolean {
  return /^(https?:|mailto:|tel:|#|\/\/)/i.test(target);
}

interface Violation {
  file: string;
  line: number;
  content: string;
  match: string;
  kind: 'placeholder' | 'route';
}

/** Build the set of routable paths from the pages/ directory. */
function buildRoutes(): string[] {
  const routes: string[] = [];

  const walk = (dir: string): void => {
    if (!fs.existsSync(dir)) return;
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const fullPath = path.join(dir, entry.name);
      if (entry.isDirectory()) {
        walk(fullPath);
        continue;
      }
      if (!entry.name.endsWith('.tsx') && !entry.name.endsWith('.ts')) continue;
      const name = entry.name.replace(/\.(tsx|ts)$/, '');
      if (name.startsWith('_')) continue; // _app, _document, _error are not routes

      const rel = path.relative(PAGES_DIR, fullPath).replace(/\\/g, '/');
      let route = '/' + rel.replace(/\.(tsx|ts)$/, '');
      if (name === 'index') {
        route = route.replace(/\/index$/, '');
      }
      if (route === '') route = '/';
      routes.push(route);
    }
  };

  walk(PAGES_DIR);
  return routes;
}

/** Normalise a link target into comparable segments. */
function toSegments(target: string): string[] {
  let p = target.split('?')[0].split('#')[0];
  p = p.replace(/\$\{[^}]*\}/g, '*'); // template interpolation → dynamic segment
  if (p.length > 1 && p.endsWith('/')) p = p.slice(0, -1);
  if (p === '') p = '/';
  return p === '/' ? [''] : p.split('/');
}

function routeExists(routes: string[], target: string): boolean {
  const targetSegs = toSegments(target);
  return routes.some((route) => {
    const routeSegs = toSegments(route);
    if (routeSegs.length !== targetSegs.length) return false;
    return routeSegs.every((seg, i) => seg === targetSegs[i] || seg === '*');
  });
}

/** Recursively collect .tsx/.ts files, skipping ignored directories. */
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

function scanFile(filePath: string, routes: string[]): Violation[] {
  const violations: Violation[] = [];
  const content = fs.readFileSync(filePath, 'utf-8');
  const lines = content.split('\n');
  const relativePath = path.relative(FRONTEND_DIR, filePath);

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const lineNumber = i + 1;

    for (const pattern of HREF_PATTERNS) {
      pattern.lastIndex = 0;
      const match = pattern.exec(line);
      if (match) {
        violations.push({
          file: relativePath,
          line: lineNumber,
          content: line.trim(),
          match: match[0],
          kind: 'placeholder',
        });
        break;
      }
    }

    for (const pattern of ROUTE_PATTERNS) {
      pattern.lastIndex = 0;
      let match: RegExpExecArray | null;
      while ((match = pattern.exec(line)) !== null) {
        const target = match[1];
        if (isExternal(target)) continue;
        if (!routeExists(routes, target)) {
          violations.push({
            file: relativePath,
            line: lineNumber,
            content: line.trim(),
            match: target,
            kind: 'route',
          });
        }
      }
    }
  }

  return violations;
}

function printViolation(v: Violation): void {
  if (v.kind === 'placeholder') {
    console.log(`  ${CYAN}${v.file}${RESET}:${v.line}  →  ${RED}placeholder ${v.match}${RESET}`);
  } else {
    console.log(
      `  ${RED}no page for${RESET} ${CYAN}${v.match}${RESET}  ← ${v.file}:${v.line}`
    );
  }
  console.log(`    ${v.content.substring(0, 100)}${v.content.length > 100 ? '...' : ''}`);
}

// ─── Main ───────────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  console.log(`\n${BOLD}Auditing hrefs and route targets...${RESET}\n`);

  const pagesFiles = collectFiles(PAGES_DIR);
  const componentsFiles = collectFiles(path.join(FRONTEND_DIR, 'components'));
  const allFiles = [...pagesFiles, ...componentsFiles];
  const routes = buildRoutes();

  console.log(`  Routes known: ${routes.length}`);
  console.log(
    `  Scanning ${allFiles.length} files (${pagesFiles.length} pages, ${componentsFiles.length} components)\n`
  );

  const allViolations: Violation[] = [];
  for (const file of allFiles) {
    allViolations.push(...scanFile(file, routes));
  }

  if (allViolations.length > 0) {
    const placeholders = allViolations.filter((v) => v.kind === 'placeholder');
    const broken = allViolations.filter((v) => v.kind === 'route');

    if (placeholders.length > 0) {
      console.log(`${BOLD}Placeholder hrefs:${RESET}\n`);
      placeholders.forEach(printViolation);
      console.log();
    }
    if (broken.length > 0) {
      console.log(`${BOLD}Links pointing at non-existent routes:${RESET}\n`);
      broken.forEach(printViolation);
      console.log();
    }

    console.log(`${'─'.repeat(80)}`);
    console.log(
      `${RED}${BOLD}❌ Found ${placeholders.length} placeholder href(s) and ${broken.length} broken route target(s)${RESET}\n`
    );
    process.exit(1);
  }

  console.log(
    `${GREEN}✅ No placeholder hrefs and every static link resolves to a page${RESET}\n`
  );
  process.exit(0);
}

main().catch((err) => {
  console.error(`${RED}Fatal error:${RESET}`, err);
  process.exit(1);
});
