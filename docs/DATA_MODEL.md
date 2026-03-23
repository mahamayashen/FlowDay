# FlowDay Data Model Reference

## Entity Relationship Overview

```
User 1──* Project 1──* Task 1──* ScheduleBlock
                           1──* TimeEntry
User 1──* WeeklyReview
User 1──* ExternalSync
```

## Core Entities

### User
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK, default gen | |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Login identity |
| name | VARCHAR(100) | NOT NULL | Display name |
| hashed_password | VARCHAR(255) | NULLABLE | NULL if OAuth-only |
| google_oauth_token | TEXT | NULLABLE | Fernet-encrypted |
| github_oauth_token | TEXT | NULLABLE | Fernet-encrypted |
| settings_json | JSONB | DEFAULT '{}' | Theme, timezone, defaults |
| created_at | TIMESTAMPTZ | NOT NULL | |
| updated_at | TIMESTAMPTZ | NOT NULL | Auto-updated |

### Project
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| user_id | UUID | FK → User, NOT NULL | |
| name | VARCHAR(100) | NOT NULL | |
| color | VARCHAR(7) | NOT NULL | Hex color code |
| client_name | VARCHAR(100) | NULLABLE | |
| hourly_rate | DECIMAL(10,2) | NULLABLE | For revenue tracking |
| status | ENUM | NOT NULL, DEFAULT 'active' | active / archived |
| created_at | TIMESTAMPTZ | NOT NULL | |

### Task
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| project_id | UUID | FK → Project, NOT NULL | |
| title | VARCHAR(255) | NOT NULL | |
| description | TEXT | NULLABLE | |
| estimate_minutes | INTEGER | NULLABLE | User's time estimate |
| priority | ENUM | NOT NULL, DEFAULT 'medium' | low / medium / high / urgent |
| status | ENUM | NOT NULL, DEFAULT 'todo' | todo / in_progress / done |
| due_date | DATE | NULLABLE | |
| created_at | TIMESTAMPTZ | NOT NULL | |
| completed_at | TIMESTAMPTZ | NULLABLE | Set when status → done |

### ScheduleBlock
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| task_id | UUID | FK → Task, NOT NULL | |
| date | DATE | NOT NULL | Which day |
| start_hour | DECIMAL(4,2) | NOT NULL | 0.00–23.99 (e.g., 9.5 = 9:30) |
| end_hour | DECIMAL(4,2) | NOT NULL | Must be > start_hour |
| source | ENUM | NOT NULL, DEFAULT 'manual' | manual / google_calendar |
| created_at | TIMESTAMPTZ | NOT NULL | |

### TimeEntry
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| task_id | UUID | FK → Task, NOT NULL | |
| started_at | TIMESTAMPTZ | NOT NULL | Timer start |
| ended_at | TIMESTAMPTZ | NULLABLE | NULL = timer running |
| duration_seconds | INTEGER | NULLABLE | Computed on stop |
| created_at | TIMESTAMPTZ | NOT NULL | |

### WeeklyReview
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| user_id | UUID | FK → User, NOT NULL | |
| week_start | DATE | NOT NULL | Monday of the review week |
| raw_data_json | JSONB | NOT NULL | Snapshot of input data for agents |
| insights_json | JSONB | NULLABLE | Structured agent outputs |
| narrative | TEXT | NULLABLE | Final human-readable review |
| scores_json | JSONB | NULLABLE | Judge scores {actionability, accuracy, coherence} |
| agent_metadata_json | JSONB | NULLABLE | Latency, token counts, retry info |
| status | ENUM | NOT NULL, DEFAULT 'pending' | pending / generating / complete / failed |
| created_at | TIMESTAMPTZ | NOT NULL | |

### ExternalSync
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| user_id | UUID | FK → User, NOT NULL | |
| provider | ENUM | NOT NULL | google_calendar / github |
| last_synced_at | TIMESTAMPTZ | NULLABLE | |
| sync_config_json | JSONB | DEFAULT '{}' | Provider-specific settings |
| status | ENUM | NOT NULL, DEFAULT 'active' | active / paused / error |
| created_at | TIMESTAMPTZ | NOT NULL | |

## Indexes

- `idx_task_project_status` on Task(project_id, status) — task list filtering
- `idx_schedule_block_date` on ScheduleBlock(date, task_id) — daily planner queries
- `idx_time_entry_task_started` on TimeEntry(task_id, started_at) — time tracking lookups
- `idx_weekly_review_user_week` on WeeklyReview(user_id, week_start) — unique per user per week
- `idx_external_sync_user_provider` on ExternalSync(user_id, provider) — unique per user per provider
