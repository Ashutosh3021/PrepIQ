-- Add prediction_accuracy_score column to predictions table
ALTER TABLE predictions ADD COLUMN IF NOT EXISTS prediction_accuracy_score VARCHAR(5) DEFAULT NULL;

-- Update existing column to have proper name
ALTER TABLE questions RENAME COLUMN difficulty TO difficulty_level;