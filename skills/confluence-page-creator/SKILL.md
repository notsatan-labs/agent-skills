---
name: confluence-page-creator
description: >
  Creates, updates, or edits technical Confluence pages. Use for technical content destined for Confluence. Also use when editing an existing Confluence page linked to.
---

# Confluence Page Creator

Produce a page a senior engineer can scan quickly, drill into on demand, and trust — every claim sourced, every detail collapsible.

---

## Step 1 — Research before writing

Spawn parallel subagents per source domain before writing a single word:

- **GitHub**: relevant classes, config, build files. Pin latest commit SHAs only — never `main`/branch refs.
- **Confluence**: existing pages, runbooks, policy docs.
- **Jira**: the driving ticket(s).
- **Internal catalogs** (dev portal, wise-brain, etc.): service ownership, topics, APIs.

Every factual claim needs a source. If you can't source it, put it in Open questions, not the body.

---

## Step 2 — GitHub permalinks

All code links use `https://github.com/<org>/<repo>/blob/<full-sha>/<path>`.

**Granularity:**

| Linking to | Anchor |
|---|---|
| File | No anchor — `.../Foo.java` |
| Single class in a file | No anchor — `.../Foo.java` |
| Class | `#L<start>-L<end>` — full body, from annotation/signature to closing `}` |
| Function / method | `#L<start>-L<end>` — full body, from annotation/signature to closing `}` |
| Specific block or single value/line | `#L<start>-L<end>` or `#L<n>` for the exact lines only |

**Verification:** After collecting links, verify each GitHub URL with `gh api 'repos/<org>/<repo>/contents/<path>?ref=<sha>'`.

A 404 response means the path is wrong — find and fix it. For non-GitHub URLs, HTTP-fetch to verify. Never mark a GitHub link as broken based on an HTTP redirect (private repos redirect unauthenticated requests to login).

---

## Step 3 — Page structure

| Section | Format | Purpose |
|---|---|---|
| Bottom line | `panel-note` | 3–5 bullets: what this is, the decision/finding, what's blocked. Readable without the rest of the page. |
| Context | 1–3 paragraphs | Why this work exists. What came before. Links to prior art. |
| Findings / Details | `<details>` expands, one per topic | Everything more than 2–3 sentences of technical detail. |
| Scope of change | Table or numbered workstreams | What changes, why, link to the relevant code/config. |
| Risks | `panel-warning` for irreversible items, bullet list otherwise | — |
| Open questions | Bullet list | Unresolved items needing a decision. |

---

## Implementation plan rules

All pages are implementation plans — written before code, to guide the implementation. Keep them that way.

**Update the doc only when the technical approach changes** — a class that doesn't exist, an API that works differently, a framework constraint that forces a different design. Update the relevant workstream to reflect the corrected approach.

**Never update the doc to record progress.** Completion status, branch names, PR links, "step Y is done", placeholder values replaced with real values — none of that belongs here. The code and git history are the record of what was implemented.

**Open questions** stay until externally answered (human decision, Privacy sign-off, partner confirmation). Do not remove a question because the implementation made a reasonable guess.

**Scope-of-change workstreams** describe what needs to happen, not what happened. They stay as written once the approach is set.

---

## Step 4 — Formatting

**Inline code** — wrap every named technical object: class, method, property key, YAML key, module, file path, config property, env var, table/column name, metric, topic.
- ✅ `TwPartnerDataManagementAutoConfiguration`, `tw-partner.data-management.enabled`
- ❌ "the auto-configuration class", "the enabled flag"

**Code blocks** — real newlines only, never literal `\n`. Single-line blocks need `data-wrap="true"` on `<pre>`. No links inside `<pre>` or `<code>`.

**Links** — inline at point of first mention. Never a sources table at the bottom. Max 3 occurrences of any single URL. Verified links only — if unverifiable, keep the text, drop the `<a>`.

**Expands** — `data-breakout="wide"` on all `<details>`. No nesting expands inside expands. No panels wrapping tables or expands.

---

## Step 5 — Publishing

Ask the user for `spaceId` and `parentId` if not provided. Use `contentFormat: html`, `status: current`.

When updating: fetch the existing page first (html format) and preserve all `data-local-id` attributes exactly — Confluence uses them for inline comments. Always include a `versionMessage`.

---

## Step 6 — Post-publish validation

After publishing, verify every unique URL in the page (parallel subagents). Fix any confirmed 404s and republish before declaring done.
