# MCP Integration: Configuration & Usage Demonstration

## 1. Server Selection

**Chosen server:** Supabase MCP (`@supabase/mcp-server-supabase`)

**Rationale:** FlowDay uses PostgreSQL hosted on Supabase as its primary datastore, with SQLAlchemy 2.0 async and Alembic for schema migrations. Connecting Claude Code directly to the database allows schema inspection, migration verification, and data debugging — all without context-switching out of the terminal.

**Alternative considered:** The generic PostgreSQL MCP (`@modelcontextprotocol/server-postgres`) was attempted first, but encountered a persistent "Tenant or user not found" error caused by incompatibility with Supabase's connection pooler (Supavisor). The official Supabase MCP, which communicates through Supabase's management API rather than raw PostgreSQL connections, resolved this issue entirely.

## 2. Configuration with `claude mcp add`

### Step 1: Generate an access token

Navigate to [Supabase Dashboard → Account → Access Tokens](https://supabase.com/dashboard/account/tokens) and generate a new personal access token.

### Step 2: Store credentials securely

Create `.env.mcp` in the project root (already listed in `.gitignore`):

```bash
# .env.mcp — gitignored, never committed
SUPABASE_ACCESS_TOKEN=[YOUR-ACCESS-TOKEN]
```

### Step 3: Add the MCP server

```bash
claude mcp add supabase -- npx -y @supabase/mcp-server-supabase \
  --access-token [YOUR-ACCESS-TOKEN] \
  --project-ref kbdzluafqnfaglycyfho
```

### Step 4: Verify

```bash
$ claude mcp list
supabase: npx -y @supabase/mcp-server-supabase --access-token *** --project-ref kbdzluafqnfaglycyfho - ✓ Connected
```

## 3. Demonstrated Workflow: Schema Exploration

### Prompt

```
List all tables in the public schema
```

### MCP Response

The Supabase MCP queried the live database and returned the full schema for two tables:

**Table: `users`** (0 rows, RLS enabled)

| Column             | Type        | Notes                          |
|--------------------|-------------|--------------------------------|
| id                 | uuid        | PK, default uuid_generate_v4() |
| email              | varchar     | unique                         |
| name               | varchar     |                                |
| hashed_password    | varchar     | nullable                       |
| google_oauth_token | text        | nullable                       |
| github_oauth_token | text        | nullable                       |
| settings_json      | jsonb       | default {}                     |
| created_at         | timestamptz | default now()                  |
| updated_at         | timestamptz | default now()                  |

**Table: `projects`** (0 rows, RLS enabled)

| Column      | Type        | Notes                                     |
|-------------|-------------|-------------------------------------------|
| id          | uuid        | PK, default uuid_generate_v4()            |
| user_id     | uuid        | FK → users.id                             |
| name        | varchar     |                                           |
| color       | varchar     |                                           |
| client_name | varchar     | nullable                                  |
| hourly_rate | numeric     | nullable                                  |
| status      | varchar     | default 'active', check: active/archived  |
| created_at  | timestamptz | default now()                             |

### What This Demonstrates

This single prompt replaced what would normally require opening the Supabase dashboard, navigating to the Table Editor, and manually inspecting each table. Claude Code retrieved live schema data, formatted it clearly, and kept the developer in the terminal — ready to immediately write an Alembic migration or plan a new feature based on the real data model.

## 4. What the MCP Connection Enables

### Development Workflow Integration

The Supabase MCP integrates into FlowDay's 4-phase TDD workflow:

| Phase              | Without MCP                                  | With MCP                                      |
|--------------------|----------------------------------------------|-----------------------------------------------|
| **Explore**        | Open Supabase dashboard, manually inspect tables | Ask Claude Code to show schema directly     |
| **Plan**           | Assume table structures from code/docs       | Query live schema to verify assumptions       |
| **Implement (TDD)**| Switch to psql/dashboard to check data       | Claude validates data writes inline           |
| **Commit**         | Hope migrations are correct                  | Claude confirms schema changes before commit  |

### Capabilities Beyond Raw SQL

Because the Supabase MCP uses the management API (not just a database connection), it can also:

- List and manage RLS (Row Level Security) policies
- Inspect auth configuration
- Query storage buckets
- Manage Edge Functions

This makes it a comprehensive development companion for Supabase-hosted projects.

## 5. Setup Documentation

Full reproducible setup guide with troubleshooting: [`docs/MCP_SETUP.md`](./MCP_SETUP.md)
