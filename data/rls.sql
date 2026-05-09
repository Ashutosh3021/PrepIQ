-- ============================================================
-- PrepIQ — Row-Level Security Policies
-- Run this in the Supabase SQL editor (or psql as superuser).
-- Safe to re-run: uses IF NOT EXISTS / OR REPLACE patterns.
-- ============================================================

-- ── Enable RLS on every user-scoped table ────────────────────

ALTER TABLE public.users              ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subjects           ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.question_papers    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.questions          ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.predictions        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_history       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mock_tests         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.study_plans        ENABLE ROW LEVEL SECURITY;

-- ── Helper: drop a policy if it already exists ───────────────
-- (Supabase does not support CREATE POLICY IF NOT EXISTS before PG 15)

DO $$ BEGIN
  -- users
  DROP POLICY IF EXISTS "users_select_own"  ON public.users;
  DROP POLICY IF EXISTS "users_insert_own"  ON public.users;
  DROP POLICY IF EXISTS "users_update_own"  ON public.users;
  DROP POLICY IF EXISTS "users_delete_own"  ON public.users;

  -- subjects
  DROP POLICY IF EXISTS "subjects_select_own"  ON public.subjects;
  DROP POLICY IF EXISTS "subjects_insert_own"  ON public.subjects;
  DROP POLICY IF EXISTS "subjects_update_own"  ON public.subjects;
  DROP POLICY IF EXISTS "subjects_delete_own"  ON public.subjects;

  -- question_papers
  DROP POLICY IF EXISTS "papers_select_own"  ON public.question_papers;
  DROP POLICY IF EXISTS "papers_insert_own"  ON public.question_papers;
  DROP POLICY IF EXISTS "papers_update_own"  ON public.question_papers;
  DROP POLICY IF EXISTS "papers_delete_own"  ON public.question_papers;

  -- questions
  DROP POLICY IF EXISTS "questions_select_own"  ON public.questions;
  DROP POLICY IF EXISTS "questions_insert_own"  ON public.questions;
  DROP POLICY IF EXISTS "questions_update_own"  ON public.questions;
  DROP POLICY IF EXISTS "questions_delete_own"  ON public.questions;

  -- predictions
  DROP POLICY IF EXISTS "predictions_select_own"  ON public.predictions;
  DROP POLICY IF EXISTS "predictions_insert_own"  ON public.predictions;
  DROP POLICY IF EXISTS "predictions_update_own"  ON public.predictions;
  DROP POLICY IF EXISTS "predictions_delete_own"  ON public.predictions;

  -- chat_history
  DROP POLICY IF EXISTS "chat_select_own"  ON public.chat_history;
  DROP POLICY IF EXISTS "chat_insert_own"  ON public.chat_history;
  DROP POLICY IF EXISTS "chat_update_own"  ON public.chat_history;
  DROP POLICY IF EXISTS "chat_delete_own"  ON public.chat_history;

  -- mock_tests
  DROP POLICY IF EXISTS "tests_select_own"  ON public.mock_tests;
  DROP POLICY IF EXISTS "tests_insert_own"  ON public.mock_tests;
  DROP POLICY IF EXISTS "tests_update_own"  ON public.mock_tests;
  DROP POLICY IF EXISTS "tests_delete_own"  ON public.mock_tests;

  -- study_plans
  DROP POLICY IF EXISTS "plans_select_own"  ON public.study_plans;
  DROP POLICY IF EXISTS "plans_insert_own"  ON public.study_plans;
  DROP POLICY IF EXISTS "plans_update_own"  ON public.study_plans;
  DROP POLICY IF EXISTS "plans_delete_own"  ON public.study_plans;
END $$;

-- ── users ─────────────────────────────────────────────────────
-- The users table uses the Supabase auth.uid() as its primary key.

CREATE POLICY "users_select_own"
  ON public.users FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "users_insert_own"
  ON public.users FOR INSERT
  WITH CHECK (auth.uid() = id);

CREATE POLICY "users_update_own"
  ON public.users FOR UPDATE
  USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

CREATE POLICY "users_delete_own"
  ON public.users FOR DELETE
  USING (auth.uid() = id);

-- ── subjects ──────────────────────────────────────────────────

CREATE POLICY "subjects_select_own"
  ON public.subjects FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "subjects_insert_own"
  ON public.subjects FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "subjects_update_own"
  ON public.subjects FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "subjects_delete_own"
  ON public.subjects FOR DELETE
  USING (auth.uid() = user_id);

-- ── question_papers ───────────────────────────────────────────
-- Papers are owned indirectly via subjects.user_id.

CREATE POLICY "papers_select_own"
  ON public.question_papers FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.subjects s
      WHERE s.id = question_papers.subject_id
        AND s.user_id = auth.uid()
    )
  );

CREATE POLICY "papers_insert_own"
  ON public.question_papers FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.subjects s
      WHERE s.id = question_papers.subject_id
        AND s.user_id = auth.uid()
    )
  );

CREATE POLICY "papers_update_own"
  ON public.question_papers FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM public.subjects s
      WHERE s.id = question_papers.subject_id
        AND s.user_id = auth.uid()
    )
  );

CREATE POLICY "papers_delete_own"
  ON public.question_papers FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM public.subjects s
      WHERE s.id = question_papers.subject_id
        AND s.user_id = auth.uid()
    )
  );

-- ── questions ─────────────────────────────────────────────────
-- Questions are owned indirectly via question_papers → subjects.user_id.

CREATE POLICY "questions_select_own"
  ON public.questions FOR SELECT
  USING (
    EXISTS (
      SELECT 1
      FROM public.question_papers qp
      JOIN public.subjects s ON s.id = qp.subject_id
      WHERE qp.id = questions.paper_id
        AND s.user_id = auth.uid()
    )
  );

CREATE POLICY "questions_insert_own"
  ON public.questions FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1
      FROM public.question_papers qp
      JOIN public.subjects s ON s.id = qp.subject_id
      WHERE qp.id = questions.paper_id
        AND s.user_id = auth.uid()
    )
  );

CREATE POLICY "questions_update_own"
  ON public.questions FOR UPDATE
  USING (
    EXISTS (
      SELECT 1
      FROM public.question_papers qp
      JOIN public.subjects s ON s.id = qp.subject_id
      WHERE qp.id = questions.paper_id
        AND s.user_id = auth.uid()
    )
  );

CREATE POLICY "questions_delete_own"
  ON public.questions FOR DELETE
  USING (
    EXISTS (
      SELECT 1
      FROM public.question_papers qp
      JOIN public.subjects s ON s.id = qp.subject_id
      WHERE qp.id = questions.paper_id
        AND s.user_id = auth.uid()
    )
  );

-- ── predictions ───────────────────────────────────────────────

CREATE POLICY "predictions_select_own"
  ON public.predictions FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "predictions_insert_own"
  ON public.predictions FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "predictions_update_own"
  ON public.predictions FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "predictions_delete_own"
  ON public.predictions FOR DELETE
  USING (auth.uid() = user_id);

-- ── chat_history ──────────────────────────────────────────────

CREATE POLICY "chat_select_own"
  ON public.chat_history FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "chat_insert_own"
  ON public.chat_history FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "chat_update_own"
  ON public.chat_history FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "chat_delete_own"
  ON public.chat_history FOR DELETE
  USING (auth.uid() = user_id);

-- ── mock_tests ────────────────────────────────────────────────

CREATE POLICY "tests_select_own"
  ON public.mock_tests FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "tests_insert_own"
  ON public.mock_tests FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "tests_update_own"
  ON public.mock_tests FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "tests_delete_own"
  ON public.mock_tests FOR DELETE
  USING (auth.uid() = user_id);

-- ── study_plans ───────────────────────────────────────────────

CREATE POLICY "plans_select_own"
  ON public.study_plans FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "plans_insert_own"
  ON public.study_plans FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "plans_update_own"
  ON public.study_plans FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "plans_delete_own"
  ON public.study_plans FOR DELETE
  USING (auth.uid() = user_id);

-- ── Service-role bypass ───────────────────────────────────────
-- The backend uses the service role key, which bypasses RLS by default.
-- No additional policy needed — Supabase service role always bypasses RLS.
-- Verify: SELECT current_setting('role'); should return 'service_role' in backend.

-- ── Verification query ────────────────────────────────────────
-- Run this after applying to confirm all tables have RLS enabled:
-- SELECT tablename, rowsecurity FROM pg_tables
-- WHERE schemaname = 'public'
-- ORDER BY tablename;
