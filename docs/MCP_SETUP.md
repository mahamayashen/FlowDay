# FlowDay — MCP Server Setup Guide

## Overview

MCP (Model Context Protocol) servers extend Claude Code with direct access to external tools. This document covers how to connect the Supabase MCP server so that Claude Code can query schema, validate migrations, manage tables, and debug data without leaving the terminal.

## Prerequisites

- Node.js 18+ (for `npx`)
- A Supabase project (project ref: `kbdzluafqnfaglycyfho`)
- Claude Code CLI installed
- Supabase access token (generated from Dashboard)

## Supabase MCP Server

### Why Supabase MCP?

FlowDay uses PostgreSQL (hosted on Supabase) as its primary datastore, with SQLAlchemy 2.0 async and Alembic for migrations. The official Supabase MCP server (`@supabase/mcp-server-supabase`) connects Claude Code to the database via Supabase's management API, enabling:

- Inspecting table schema before writing Alembic migrations
- Verifying migration results after `alembic upgrade head`
- Querying test data during TDD GREEN phase
- Debugging data issues without switching to `psql` or the Supabase dashboard
- Managing tables, RLS policies, and auth directly from Claude Code

> **Note:** We chose the Supabase MCP over the generic PostgreSQL MCP (`@modelcontextprotocol/server-postgres`) because the latter has compatibility issues with Supabase's connection pooler. The Supabase MCP uses the management API instead of direct PostgreSQL connections, which is more reliable and feature-rich.

### Setup

**1. Generate a Supabase access token**

Go to [Supabase Dashboard → Account → Access Tokens](https://supabase.com/dashboard/account/tokens) and generate a new token. Save it securely.

**2. Store credentials in `.env.mcp`**

Create `.env.mcp` in the project root (this file is gitignored):

```bash
# .env.mcp
SUPABASE_ACCESS_TOKEN=[YOUR-ACCESS-TOKEN]
```

> **Security note:** `.env.mcp` is listed in `.gitignore`. Never commit access tokens to version control.

**3. Add the MCP server to Claude Code**

From the project root:

```bash
claude mcp add supabase -- npx -y @supabase/mcp-server-supabase \
  --access-token [YOUR-ACCESS-TOKEN] \
  --project-ref kbdzluafqnfaglycyfho
```

Key flags:

| Flag              | Value                          | Description                          |
|-------------------|--------------------------------|--------------------------------------|
| `--access-token`  | Your Supabase access token     | Authenticates with Supabase API      |
| `--project-ref`   | `kbdzluafqnfaglycyfho`         | Identifies the FlowDay project       |

**4. Verify the connection**

```bash
claude mcp list
```

You should see `supabase` with status `✓ Connected`.

**5. Test with a query**

In Claude Code, ask:
> "List all tables in the public schema"

Expected output: `users` and `projects` tables with their columns and types.

### Verified Output

The MCP connection has been tested and returns the following schema:

**users** (RLS enabled):

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

**projects** (RLS enabled):

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

### Usage Examples

Once connected, you can ask Claude Code to interact with the database directly during development:

**Inspect schema before writing a migration:**
> "Show me the current columns in the `users` table"

**Validate a migration ran correctly:**
> "After I run `alembic upgrade head`, check if the `preferences` column was added to the `users` table"

**Query test data during TDD:**
> "Query the `tasks` table to verify my test created the expected record"

**Debug data issues:**
> "Show me all tasks where `status = 'stuck'` and the `updated_at` is older than 7 days"

### Demo Workflow: Migration + Verification

A complete task demonstrating MCP value within the 4-phase TDD workflow:

**Step 1 — Explore (MCP queries real schema)**

Ask Claude Code:
> "Show me the current columns, types, and constraints of the `users` table"

Claude Code queries the live Supabase database and returns the full schema.

**Step 2 — Plan (decisions based on real data)**

> "I want to add a `timezone` column to `users`, default 'UTC'. Based on the schema you just queried, are there any conflicts? Write a plan."

Claude Code makes informed decisions from live schema — no guessing.

**Step 3 — Implement (write migration + verify)**

Claude Code generates the Alembic migration, then:
```bash
cd backend && alembic upgrade head
```

Then verify via MCP:
> "Confirm the `timezone` column now exists on the `users` table"

**Step 4 — TDD GREEN (validate data)**

> "Query `users` to confirm all existing rows have `timezone = 'UTC'`"

**Value comparison:**

| Operation         | Without MCP                            | With MCP                              |
|-------------------|----------------------------------------|---------------------------------------|
| Check schema      | Open Supabase dashboard or `psql`      | Claude Code queries directly          |
| Verify migration  | Switch to dashboard → inspect table    | One prompt, stays in context          |
| Debug data        | Write SQL manually → copy results back | Claude queries and analyzes in-place  |

### Workflow Integration

The Supabase MCP fits naturally into the 4-phase development workflow:

| Phase              | How MCP helps                                               |
|--------------------|-------------------------------------------------------------|
| **Explore**        | Inspect existing schema to understand current data model    |
| **Plan**           | Verify assumptions about table structures and relationships |
| **Implement (TDD)**| GREEN — validate data writes; REFACTOR — check queries      |
| **Commit**         | Final sanity check that migrations and data are correct     |

### Troubleshooting

**MCP shows "Connected" but queries fail:**
- Ensure both `--access-token` and `--project-ref` flags are provided
- Verify the access token hasn't expired at [Account → Access Tokens](https://supabase.com/dashboard/account/tokens)
- Regenerate the token if needed and re-run `claude mcp add`

**"Tenant or user not found" (if using PostgreSQL MCP instead):**
- This is a known compatibility issue between `@modelcontextprotocol/server-postgres` and Supabase's connection pooler
- Solution: use the Supabase MCP (`@supabase/mcp-server-supabase`) instead

**MCP server not appearing in `claude mcp list`:**
- Re-run the `claude mcp add` command
- Check `~/.claude/settings.json` for the MCP entry

**Supabase project paused:**
- Free tier projects pause after 7 days of inactivity
- Go to Supabase Dashboard and click "Restore" to resume

### Removing the MCP Server

```bash
claude mcp remove supabase
```

## Other Recommended MCP Servers

For future consideration:

| Server         | Use case                              | Add command                                                                 |
|----------------|---------------------------------------|-----------------------------------------------------------------------------|
| **GitHub**     | PR creation, issue linking, CI status | `claude mcp add github -- npx -y @modelcontextprotocol/server-github`       |
| **Playwright** | Browser-based E2E testing             | `claude mcp add playwright -- npx -y @anthropic-ai/mcp-server-playwright`   |
