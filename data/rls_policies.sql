-- Supabase RLS Policies for PrepIQ Application
-- Enables Row Level Security and sets up policies for data protection

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE subjects ENABLE ROW LEVEL SECURITY;
ALTER TABLE question_papers ENABLE ROW LEVEL SECURITY;
ALTER TABLE questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE mock_tests ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE study_plans ENABLE ROW LEVEL SECURITY;

-- Create policies for users table
CREATE POLICY "Users can view own profile" ON users
  FOR SELECT USING (auth.uid() = id OR auth.role() = 'authenticated');

CREATE POLICY "Users can update own profile" ON users
  FOR UPDATE USING (auth.uid() = id) WITH CHECK (auth.uid() = id);

-- Create policies for subjects table
CREATE POLICY "Users can view own subjects" ON subjects
  FOR SELECT USING (user_id = auth.uid() OR auth.role() = 'authenticated');

CREATE POLICY "Users can insert own subjects" ON subjects
  FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update own subjects" ON subjects
  FOR UPDATE USING (user_id = auth.uid());

CREATE POLICY "Users can delete own subjects" ON subjects
  FOR DELETE USING (user_id = auth.uid());

-- Create policies for question_papers table
CREATE POLICY "Users can view own question papers" ON question_papers
  FOR SELECT USING (
    subject_id IN (
      SELECT id FROM subjects WHERE user_id = auth.uid()
    ) OR auth.role() = 'authenticated'
  );

CREATE POLICY "Users can insert own question papers" ON question_papers
  FOR INSERT WITH CHECK (
    subject_id IN (
      SELECT id FROM subjects WHERE user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update own question papers" ON question_papers
  FOR UPDATE USING (
    subject_id IN (
      SELECT id FROM subjects WHERE user_id = auth.uid()
    )
  );

CREATE POLICY "Users can delete own question papers" ON question_papers
  FOR DELETE USING (
    subject_id IN (
      SELECT id FROM subjects WHERE user_id = auth.uid()
    )
  );

-- Create policies for questions table
CREATE POLICY "Users can view questions from own papers" ON questions
  FOR SELECT USING (
    paper_id IN (
      SELECT id FROM question_papers WHERE subject_id IN (
        SELECT id FROM subjects WHERE user_id = auth.uid()
      )
    ) OR auth.role() = 'authenticated'
  );

CREATE POLICY "Users can insert questions to own papers" ON questions
  FOR INSERT WITH CHECK (
    paper_id IN (
      SELECT id FROM question_papers WHERE subject_id IN (
        SELECT id FROM subjects WHERE user_id = auth.uid()
      )
    )
  );

CREATE POLICY "Users can update questions from own papers" ON questions
  FOR UPDATE USING (
    paper_id IN (
      SELECT id FROM question_papers WHERE subject_id IN (
        SELECT id FROM subjects WHERE user_id = auth.uid()
      )
    )
  );

CREATE POLICY "Users can delete questions from own papers" ON questions
  FOR DELETE USING (
    paper_id IN (
      SELECT id FROM question_papers WHERE subject_id IN (
        SELECT id FROM subjects WHERE user_id = auth.uid()
      )
    )
  );

-- Create policies for predictions table
CREATE POLICY "Users can view own predictions" ON predictions
  FOR SELECT USING (
    user_id = auth.uid() OR
    subject_id IN (
      SELECT id FROM subjects WHERE user_id = auth.uid()
    ) OR auth.role() = 'authenticated'
  );

CREATE POLICY "Users can insert own predictions" ON predictions
  FOR INSERT WITH CHECK (
    user_id = auth.uid() AND
    subject_id IN (
      SELECT id FROM subjects WHERE user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update own predictions" ON predictions
  FOR UPDATE USING (
    user_id = auth.uid() AND
    subject_id IN (
      SELECT id FROM subjects WHERE user_id = auth.uid()
    )
  );

CREATE POLICY "Users can delete own predictions" ON predictions
  FOR DELETE USING (
    user_id = auth.uid() AND
    subject_id IN (
      SELECT id FROM subjects WHERE user_id = auth.uid()
    )
  );

-- Create policies for mock_tests table
CREATE POLICY "Users can view own mock tests" ON mock_tests
  FOR SELECT USING (
    user_id = auth.uid() OR
    subject_id IN (
      SELECT id FROM subjects WHERE user_id = auth.uid()
    ) OR auth.role() = 'authenticated'
  );

CREATE POLICY "Users can insert own mock tests" ON mock_tests
  FOR INSERT WITH CHECK (
    user_id = auth.uid() AND
    subject_id IN (
      SELECT id FROM subjects WHERE user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update own mock tests" ON mock_tests
  FOR UPDATE USING (
    user_id = auth.uid() AND
    subject_id IN (
      SELECT id FROM subjects WHERE user_id = auth.uid()
    )
  );

CREATE POLICY "Users can delete own mock tests" ON mock_tests
  FOR DELETE USING (
    user_id = auth.uid() AND
    subject_id IN (
      SELECT id FROM subjects WHERE user_id = auth.uid()
    )
  );

-- Create policies for chat_history table
CREATE POLICY "Users can view own chat history" ON chat_history
  FOR SELECT USING (
    user_id = auth.uid() OR
    subject_id IN (
      SELECT id FROM subjects WHERE user_id = auth.uid()
    ) OR auth.role() = 'authenticated'
  );

CREATE POLICY "Users can insert own chat history" ON chat_history
  FOR INSERT WITH CHECK (
    user_id = auth.uid() AND
    subject_id IN (
      SELECT id FROM subjects WHERE user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update own chat history" ON chat_history
  FOR UPDATE USING (
    user_id = auth.uid() AND
    subject_id IN (
      SELECT id FROM subjects WHERE user_id = auth.uid()
    )
  );

CREATE POLICY "Users can delete own chat history" ON chat_history
  FOR DELETE USING (
    user_id = auth.uid() AND
    subject_id IN (
      SELECT id FROM subjects WHERE user_id = auth.uid()
    )
  );

-- Create policies for study_plans table
CREATE POLICY "Users can view own study plans" ON study_plans
  FOR SELECT USING (
    user_id = auth.uid() OR
    subject_id IN (
      SELECT id FROM subjects WHERE user_id = auth.uid()
    ) OR auth.role() = 'authenticated'
  );

CREATE POLICY "Users can insert own study plans" ON study_plans
  FOR INSERT WITH CHECK (
    user_id = auth.uid() AND
    subject_id IN (
      SELECT id FROM subjects WHERE user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update own study plans" ON study_plans
  FOR UPDATE USING (
    user_id = auth.uid() AND
    subject_id IN (
      SELECT id FROM subjects WHERE user_id = auth.uid()
    )
  );

CREATE POLICY "Users can delete own study plans" ON study_plans
  FOR DELETE USING (
    user_id = auth.uid() AND
    subject_id IN (
      SELECT id FROM subjects WHERE user_id = auth.uid()
    )
  );

-- Create a function to automatically set user_id for new records
CREATE OR REPLACE FUNCTION public.set_current_user_id()
RETURNS uuid AS $$
BEGIN
  RETURN auth.uid();
EXCEPTION
  WHEN OTHERS THEN
    RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;