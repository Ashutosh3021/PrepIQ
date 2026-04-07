/**
 * check-types.ts (QUAL-02)
 *
 * Runs TypeScript type checking and reports any errors.
 * This is a thin wrapper around `npx tsc --noEmit` that provides
 * formatted output and consistent exit codes.
 *
 * Usage: npx tsx scripts/check-types.ts
 * Exit: 0 if no type errors, 1 if errors found
 */
import { execSync } from 'child_process';
import * as path from 'path';

// ANSI color codes
const GREEN = '\x1b[32m';
const RED = '\x1b[31m';
const BOLD = '\x1b[1m';
const RESET = '\x1b[0m';

// Resolve paths relative to the frontend/ directory
const FRONTEND_DIR = path.resolve(__dirname, '..');

async function main(): Promise<void> {
  console.log(`\n${BOLD}🔍 Running TypeScript type check...${RESET}\n`);

  try {
    const output = execSync('npx tsc --noEmit', {
      cwd: FRONTEND_DIR,
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'pipe'],
    });

    console.log(`${GREEN}${BOLD}✅ No TypeScript errors found${RESET}\n`);
    process.exit(0);
  } catch (error) {
    const execError = error as { stdout?: string; stderr?: string; status?: number };
    const output = execError.stdout || execError.stderr || '';

    if (output.trim()) {
      console.log(output);
    }

    console.log(`\n${RED}${BOLD}❌ TypeScript errors found${RESET}\n`);
    process.exit(1);
  }
}

main().catch((err) => {
  console.error(`${RED}Fatal error:${RESET}`, err);
  process.exit(1);
});
