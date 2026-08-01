# Pyronites schema expectations (PrepIQ)

Create these tables in your Pyronites dashboard (field types flexible; app uses JSON-ish storage for complex columns).

Phase 0 two-track prediction fields are included below. **Adding columns to an existing PyroCore table** may require recreating the table or a dashboard migration — the Python repositories already send the new fields; the remote schema must accept them.

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

**Note:** PyroCore treats `users` as a **reserved** system table for auth. Dynamic `/tables/users` may 404. PrepIQ profile upsert is best-effort.

## subjects
| Column | Notes |
|--------|--------|
| id | string PK |
| user_id | string |
| name | string |
| code, semester, academic_year, total_marks, exam_date, exam_duration_minutes | optional |
| syllabus_json | object/json optional |
| **exam_type** | `government` \| `university` (nullable until wizard) |
| **exam_name** | `NEET` / `JEE` (govt) or free text (university) |
| **university_name** | nullable, university track |
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
| **exam_year** | int optional — **see reliability note below** |
| exam_semester, total_marks, duration_minutes | optional |
| raw_text | long text optional |
| metadata_json | object optional |
| extraction_confidence, extraction_method | optional |
| processing_status | `pending` \| `processing` \| `completed` \| `failed` |
| error_message | optional |
| processed_at, created_at, updated_at | |

### exam_year reliability (Phase 0 audit)

| Path | Sets `exam_year`? |
|------|-------------------|
| `POST /api/v1/papers/upload` (`Form exam_year`) | **Yes** — optional form field passed into `papers_repo.create` |
| `POST /api/v1/upload` (primary FE path today) | **No** — create payload omits `exam_year` |

Field **exists** on the table and in `papers_repo`. It is **not reliably populated** on the main upload flow. Recency / marks-trend / last-asked-gap must not assume every paper has a year until upload is fixed in a later phase.

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
| **tagged_unit** | nullable string — government syllabus unit (later phase) |
| **tagging_confidence** | nullable float 0–1 |
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
| **source_type** | `government_ml` \| `university_llm` |
| **model_version** | nullable string (govt track traceability) |
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

## syllabus (new — government track)
| Column | Notes |
|--------|--------|
| id | string PK |
| subject_id | string (one logical syllabus per subject) |
| raw_pdf_ref | relative path under UPLOAD_ROOT or storage ref |
| extracted_taxonomy | JSON — ordered list of Unit names (filled after OCR/LLM) |
| extracted_at | ISO timestamp, null until processed |
| created_at, updated_at | |

## unit_features (new — government track)
| Column | Notes |
|--------|--------|
| id | string PK |
| subject_id | string |
| unit_name | string |
| recurrence_count | int |
| recency_weight | float |
| **marks_trend** | **float** — slope-style: `>0` increasing marks over years, `0` flat/unknown, `<0` decreasing |
| last_asked_gap | int (years since last appearance) |
| computed_at | ISO timestamp |
| created_at, updated_at | |

## exam_context_cache (new — shared, not per-user)
| Column | Notes |
|--------|--------|
| id | string PK |
| exam_name | string key (`NEET`, `JEE`) — **not** user- or subject-scoped |
| context_summary | text (LLM+search output, later phase) |
| fetched_at | ISO timestamp |
| created_at, updated_at | |

## Auth
Pyronites `auth.sign_up` / `auth.sign_in` — password is **not** stored in the `users` table by PrepIQ.

## Phase 0 local apply (PyroCore)

New tables: create via `POST /tables` (see dashboard or PowerShell create scripts).

Existing tables (`subjects`, `questions`, `predictions`): add columns in the PyroCore UI if supported, or recreate tables with the full column list. Until remote columns exist, inserts that send unknown fields may error depending on PyroCore strictness — repositories are forward-compatible (send new keys when present).
