/**
 * Quick script to check and fix API URL configuration
 * Run this in the frontend directory: node fix-api-url.js
 */

const fs = require('fs');
const path = require('path');

const envLocalPath = path.join(__dirname, '.env.local');
const envExamplePath = path.join(__dirname, '.env.example');

console.log('🔍 Checking API URL configuration...\n');

// Check if .env.local exists
if (fs.existsSync(envLocalPath)) {
  console.log('✅ Found .env.local file');
  const content = fs.readFileSync(envLocalPath, 'utf8');
  
  // Check for incorrect port
  if (content.includes('8001')) {
    console.log('⚠️  Found port 8001 in .env.local - this should be 8000');
    const fixed = content.replace(/localhost:8001/g, 'localhost:8000').replace(/127\.0\.0\.1:8001/g, '127.0.0.1:8000');
    fs.writeFileSync(envLocalPath, fixed);
    console.log('✅ Fixed! Updated .env.local to use port 8000\n');
  } else if (content.includes('NEXT_PUBLIC_API_URL')) {
    console.log('✅ NEXT_PUBLIC_API_URL is configured');
    const match = content.match(/NEXT_PUBLIC_API_URL=(.+)/);
    if (match) {
      console.log(`   Current value: ${match[1]}`);
      if (match[1].includes('8001')) {
        console.log('⚠️  Port 8001 detected - fixing...');
        const fixed = content.replace(/8001/g, '8000');
        fs.writeFileSync(envLocalPath, fixed);
        console.log('✅ Fixed! Updated to port 8000\n');
      }
    }
  } else {
    console.log('⚠️  NEXT_PUBLIC_API_URL not found in .env.local');
    console.log('   Adding it now...');
    const newLine = '\n# Backend API URL\nNEXT_PUBLIC_API_URL=http://localhost:8000\n';
    fs.appendFileSync(envLocalPath, newLine);
    console.log('✅ Added NEXT_PUBLIC_API_URL=http://localhost:8000\n');
  }
} else {
  console.log('⚠️  .env.local file not found');
  console.log('   Creating it with correct configuration...');
  
  const envContent = `# PrepIQ Frontend Environment Variables

# Backend API URL - MUST match your backend server port
NEXT_PUBLIC_API_URL=http://localhost:8000

# Supabase Configuration (if using Supabase)
# NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
# NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key

# Google Gemini API Key (optional, for frontend AI features)
# NEXT_PUBLIC_GEMINI_API_KEY=your_gemini_api_key
`;
  
  fs.writeFileSync(envLocalPath, envContent);
  console.log('✅ Created .env.local with NEXT_PUBLIC_API_URL=http://localhost:8000\n');
}

console.log('📋 Summary:');
console.log('   - Backend should run on: http://localhost:8000');
console.log('   - Frontend API URL: http://localhost:8000');
console.log('\n🔄 Next steps:');
console.log('   1. Restart your Next.js dev server');
console.log('   2. Clear browser cache if needed');
console.log('   3. Try logging in again\n');
