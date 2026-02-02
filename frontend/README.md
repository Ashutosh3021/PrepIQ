# PrepIQ Frontend

This is the frontend for the PrepIQ AI-powered study assistant, built with Next.js.

## Features

- Modern React application with Next.js
- User authentication via Supabase
- Dashboard for managing study materials
- Upload and analyze PDF study materials
- View predictions and study plans
- AI chat interface

## Tech Stack

- Next.js 14+ with App Router
- React 18+
- TypeScript
- Tailwind CSS
- Radix UI Components
- Supabase (Authentication & Database)

## Getting Started

### Prerequisites

- Node.js 18+
- pnpm (or npm)

### Installation

1. Install dependencies:
   ```bash
   pnpm install
   ```

2. Create a `.env.local` file based on `.env.example`:
   ```bash
   cp .env.example .env.local
   # Edit .env.local to add your Supabase and other API keys
   ```

3. Run the development server:
   ```bash
   pnpm run dev
   ```

4. Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Environment Variables

- `NEXT_PUBLIC_SUPABASE_URL`: Your Supabase project URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`: Your Supabase anonymous key
- `NEXT_PUBLIC_GEMINI_API_KEY`: Google Gemini API key (if using frontend AI features)

## Project Structure

- `app/` - Next.js App Router pages
- `components/` - Reusable React components
- `hooks/` - Custom React hooks
- `lib/` - Utility functions and Supabase integration
- `styles/` - Global styles

## Available Scripts

- `pnpm run dev` - Start development server
- `pnpm run build` - Build for production
- `pnpm run start` - Start production server
- `pnpm run lint` - Run linter