# Pyronites schema expectations (PrepIQ)

Create these tables in your Pyronites dashboard (field types flexible; app uses JSON-ish storage for complex columns).

## users
| Column | Notes |
|--------|--------|
| id | string (auth user id) PK |
| email | string |
| full_name | string optional |
| college_name | string optional |
| program | string optional |
| year_of_study | string/int optional |
| wizard_completed | bool |
| exam_name, days_until_exam, focus_subjects, study_hours_per_day, target_score, preparation_level, exam_date | optional wizard fields |
| created_at, updated_at | ISO timestamps |

## subjects
| Column | Notes |
|--------|--------|
| id | string PK |
| user_id | string |
| name | string |
| code, semester, academic_year, total_marks, exam_date, exam_duration_minutes | optional |
| syllabus_json | object/json optional |
| papers_uploaded, predictions_generated, mock_tests_created | optional counters |
| created_at, updated_at | |

## question_papers
| Column | Notes |
|--------|--------|
| id | string PK |
| subject_id | string |
| file_name | string |
| file_path | **relative path under UPLOAD_ROOT** (local disk) |
| file_size_bytes | int optional |
| exam_year, exam_semester, total_marks, duration_minutes | optional |
| raw_text | long text optional |
| metadata_json | object optional |
| extraction_confidence, extraction_method | optional |
| processing_status | `pending` \| `processing` \| `completed` \| `failed` |
| error_message | optional |
| processed_at, created_at, updated_at | |

## questions
| Column | Notes |
|--------|--------|
| id | string PK |
| paper_id | string |
| subject_id | string |
| question_text | string |
| question_number | int optional |
| marks | int |
| unit_name | string |
| question_type | string |
| difficulty | string |
| correct_answer | string optional (needed for scored mock tests) |
| topics_json | optional |
| text_length | optional |
| created_at | |

## predictions
| Column | Notes |
|--------|--------|
| id | string PK |
| user_id | string |
| subject_id | string |
| predicted_questions_json | JSON array of predicted questions |
| total_questions | int |
| total_predicted_marks | int |
| unit_coverage_json | object |
| ml_analysis_json | object |
| prediction_accuracy_score | float |
| created_at, updated_at | |

## mock_tests
| Column | Notes |
|--------|--------|
| id | string PK |
| user_id | string |
| subject_id | string |
| total_questions, total_marks, duration_minutes | |
| difficulty_level | string |
| questions_json | JSON array |
| start_time, end_time | |
| is_completed | bool |
| user_answers_json | object |
| score | number |
| percentage | number **or null** |
| correct_count, incorrect_count, skipped_count | |
| weak_topics_json, strong_topics_json | |
| created_at | |

## Auth
Pyronites `auth.sign_up` / `auth.sign_in` — password is **not** stored in the `users` table by PrepIQ.
