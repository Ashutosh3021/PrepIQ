-- =============================================================================
-- PrepIQ — Row Level Security Policies
-- rls.sql
--
-- Run AFTER global.sql.
-- Idempotent: drops and recreates every policy so re-runs are safe.
--
-- Design principles:
--   1. Every table is locked down — no implicit public access.
--   2. Policies use direct column comparisons (user_id = auth.uid()) wherever
--      possible. Subquery chains are replaced with a single helper function
--      that caches the ownership check, avoiding repeated full-table scans.
--   3. The FastAPI backend uses the service_role key which bypasses RLS
--      entirely — these policies protect direct Supabase client access only.
--   4. anon role gets zero access to all tables.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 0. Enable RLS on every table
-- ---------------------------------------------------------------------------

ALTER TABLE public.users           ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subjects        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.question_papers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.questions       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.predictions     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mock_tests      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_history    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.study_plans     ENABLE ROW LEVEL SECURITY;

-- Force RLS even for table owners (prevents accidental bypass)
ALTER TABLE public.users           FORCE ROW LEVEL SECURITY;
ALTER TABLE public.subjects        FORCE ROW LEVEL SECURITY;
ALTER TABLE public.question_papers FORCE ROW LEVEL SECURITY;
ALTER TABLE public.questions       FORCE ROW LEVEL SECURITY;
ALTER TABLE public.predictions     FORCE ROW LEVEL SECURITY;
ALTER TABLE public.mock_tests      FORCE ROW LEVEL SECURITY;
ALTER TABLE public.chat_history    FORCE ROW LEVEL SECURITY;
ALTER TABLE public.study_plans     FORCE ROW LEVEL SECURITY;

-- ---------------------------------------------------------------------------
-- 1. Helper: owns_subject(subject_id)
--    Returns TRUE when the calling user owns the given subject.
--    STABLE + SECURITY DEFINER lets Postgres cache the result within a
--    single statement, so policies on question_papers / questions / etc.
--    don't re-execute the subquery for every row.
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.owns_subject(p_subject_id UUID)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT EXISTS (
        SELECT 1 FROM public.subjects
        WHERE id = p_subject_id
          AND user_id = auth.uid()
    );
$$;

-- ---------------------------------------------------------------------------
-- 2. Helper: owns_paper(paper_id)
--    Returns TRUE when the calling user owns the paper's parent subject.
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION public.owns_paper(p_paper_id UUID)
RETURNS BOOLEAN
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT EXISTS (
        SELECT 1
        FROM public.question_papers qp
        JOIN public.subjects s ON s.id = qp.subject_id
        WHERE qp.id = p_paper_id
          AND s.user_id = auth.uid()
    );
$$;

-- ---------------------------------------------------------------------------
-- 3. users
--    Users can only see and edit their own row.
--    INSERT is handled by the auth trigger (service_role) — no user INSERT.
-- ---------------------------------------------------------------------------

DROP POLICY IF EXISTS "users_select_own"  ON public.users;
DROP POLICY IF EXISTS "users_update_own"  ON public.users;
DROP POLICY IF EXISTS "users_delete_own"  ON public.users;

CREATE POLICY "users_select_own"
    ON public.users FOR SELECT
    USING (id = auth.uid());

CREATE POLICY "users_update_own"
    ON public.users FOR UPDATE
    USING (id = auth.uid())
    WITH CHECK (id = auth.uid());

-- Soft-delete only — the application sets deleted_at; hard deletes go via service_role
CREATE POLICY "users_delete_own"
    ON public.users FOR DELETE
    USING (id = auth.uid());

-- ---------------------------------------------------------------------------
-- 4. subjects
-- ---------------------------------------------------------------------------

DROP POLICY IF EXISTS "subjects_select_own"  ON public.subjects;
DROP POLICY IF EXISTS "subjects_insert_own"  ON public.subjects;
DROP POLICY IF EXISTS "subjects_update_own"  ON public.subjects;
DROP POLICY IF EXISTS "subjects_delete_own"  ON public.subjects;

CREATE POLICY "subjects_select_own"
    ON public.subjects FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "subjects_insert_own"
    ON public.subjects FOR INSERT
    WITH CHECK (user_id = auth.uid());

CREATE POLICY "subjects_update_own"
    ON public.subjects FOR UPDATE
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

CREATE POLICY "subjects_delete_own"
    ON public.subjects FOR DELETE
    USING (user_id = auth.uid());

-- ---------------------------------------------------------------------------
-- 5. question_papers
--    Ownership is derived from the parent subject.
--    Uses owns_subject() helper to avoid repeated subquery expansion.
-- ---------------------------------------------------------------------------

DROP POLICY IF EXISTS "qp_select_own"  ON public.question_papers;
DROP POLICY IF EXISTS "qp_insert_own"  ON public.question_papers;
DROP POLICY IF EXISTS "qp_update_own"  ON public.question_papers;
DROP POLICY IF EXISTS "qp_delete_own"  ON public.question_papers;

CREATE POLICY "qp_select_own"
    ON public.question_papers FOR SELECT
    USING (public.owns_subject(subject_id));

CREATE POLICY "qp_insert_own"
    ON public.question_papers FOR INSERT
    WITH CHECK (public.owns_subject(subject_id));

CREATE POLICY "qp_update_own"
    ON public.question_papers FOR UPDATE
    USING (public.owns_subject(subject_id))
    WITH CHECK (public.owns_subject(subject_id));

CREATE POLICY "qp_delete_own"
    ON public.question_papers FOR DELETE
    USING (public.owns_subject(subject_id));

-- ---------------------------------------------------------------------------
-- 6. questions
--    Ownership is derived from the parent paper → subject.
--    Uses owns_paper() helper.
-- ---------------------------------------------------------------------------

DROP POLICY IF EXISTS "questions_select_own"  ON public.questions;
DROP POLICY IF EXISTS "questions_insert_own"  ON public.questions;
DROP POLICY IF EXISTS "questions_update_own"  ON public.questions;
DROP POLICY IF EXISTS "questions_delete_own"  ON public.questions;

CREATE POLICY "questions_select_own"
    ON public.questions FOR SELECT
    USING (public.owns_paper(paper_id));

CREATE POLICY "questions_insert_own"
    ON public.questions FOR INSERT
    WITH CHECK (public.owns_paper(paper_id));

CREATE POLICY "questions_update_own"
    ON public.questions FOR UPDATE
    USING (public.owns_paper(paper_id))
    WITH CHECK (public.owns_paper(paper_id));

CREATE POLICY "questions_delete_own"
    ON public.questions FOR DELETE
    USING (public.owns_paper(paper_id));

-- ---------------------------------------------------------------------------
-- 7. predictions
--    Direct user_id column — no helper needed.
-- ---------------------------------------------------------------------------

DROP POLICY IF EXISTS "predictions_select_own"  ON public.predictions;
DROP POLICY IF EXISTS "predictions_insert_own"  ON public.predictions;
DROP POLICY IF EXISTS "predictions_update_own"  ON public.predictions;
DROP POLICY IF EXISTS "predictions_delete_own"  ON public.predictions;

CREATE POLICY "predictions_select_own"
    ON public.predictions FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "predictions_insert_own"
    ON public.predictions FOR INSERT
    WITH CHECK (
        user_id = auth.uid()
        AND public.owns_subject(subject_id)
    );

CREATE POLICY "predictions_update_own"
    ON public.predictions FOR UPDATE
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

CREATE POLICY "predictions_delete_own"
    ON public.predictions FOR DELETE
    USING (user_id = auth.uid());

-- ---------------------------------------------------------------------------
-- 8. mock_tests
-- ---------------------------------------------------------------------------

DROP POLICY IF EXISTS "mock_tests_select_own"  ON public.mock_tests;
DROP POLICY IF EXISTS "mock_tests_insert_own"  ON public.mock_tests;
DROP POLICY IF EXISTS "mock_tests_update_own"  ON public.mock_tests;
DROP POLICY IF EXISTS "mock_tests_delete_own"  ON public.mock_tests;

CREATE POLICY "mock_tests_select_own"
    ON public.mock_tests FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "mock_tests_insert_own"
    ON public.mock_tests FOR INSERT
    WITH CHECK (
        user_id = auth.uid()
        AND public.owns_subject(subject_id)
    );

CREATE POLICY "mock_tests_update_own"
    ON public.mock_tests FOR UPDATE
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

CREATE POLICY "mock_tests_delete_own"
    ON public.mock_tests FOR DELETE
    USING (user_id = auth.uid());

-- ---------------------------------------------------------------------------
-- 9. chat_history
-- ---------------------------------------------------------------------------

DROP POLICY IF EXISTS "chat_select_own"  ON public.chat_history;
DROP POLICY IF EXISTS "chat_insert_own"  ON public.chat_history;
DROP POLICY IF EXISTS "chat_update_own"  ON public.chat_history;
DROP POLICY IF EXISTS "chat_delete_own"  ON public.chat_history;

CREATE POLICY "chat_select_own"
    ON public.chat_history FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "chat_insert_own"
    ON public.chat_history FOR INSERT
    WITH CHECK (user_id = auth.uid());

-- Chat messages are immutable — no UPDATE policy
-- (application never updates chat rows; only inserts and deletes)

CREATE POLICY "chat_delete_own"
    ON public.chat_history FOR DELETE
    USING (user_id = auth.uid());

-- ---------------------------------------------------------------------------
-- 10. study_plans
-- ---------------------------------------------------------------------------

DROP POLICY IF EXISTS "plans_select_own"  ON public.study_plans;
DROP POLICY IF EXISTS "plans_insert_own"  ON public.study_plans;
DROP POLICY IF EXISTS "plans_update_own"  ON public.study_plans;
DROP POLICY IF EXISTS "plans_delete_own"  ON public.study_plans;

CREATE POLICY "plans_select_own"
    ON public.study_plans FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "plans_insert_own"
    ON public.study_plans FOR INSERT
    WITH CHECK (
        user_id = auth.uid()
        AND public.owns_subject(subject_id)
    );

CREATE POLICY "plans_update_own"
    ON public.study_plans FOR UPDATE
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

CREATE POLICY "plans_delete_own"
    ON public.study_plans FOR DELETE
    USING (user_id = auth.uid());

-- ---------------------------------------------------------------------------
-- 11. Grants for the authenticated role
--     anon gets nothing. authenticated gets DML on all tables.
--     service_role bypasses RLS entirely (no grant needed).
-- ---------------------------------------------------------------------------

GRANT USAGE ON SCHEMA public TO authenticated;

GRANT SELECT, INSERT, UPDATE, DELETE ON public.users           TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.subjects        TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.question_papers TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.questions       TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.predictions     TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.mock_tests      TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.chat_history    TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.study_plans     TO authenticated;

-- Execute permission on helper functions
GRANT EXECUTE ON FUNCTION public.owns_subject(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION public.owns_paper(UUID)   TO authenticated;

-- Revoke all from anon explicitly (belt-and-suspenders)
REVOKE ALL ON public.users           FROM anon;
REVOKE ALL ON public.subjects        FROM anon;
REVOKE ALL ON public.question_papers FROM anon;
REVOKE ALL ON public.questions       FROM anon;
REVOKE ALL ON public.predictions     FROM anon;
REVOKE ALL ON public.mock_tests      FROM anon;
REVOKE ALL ON public.chat_history    FROM anon;
REVOKE ALL ON public.study_plans     FROM anon;
