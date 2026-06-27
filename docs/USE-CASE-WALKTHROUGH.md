# Use-case walkthrough — a company adopts the mechanism end to end

A concrete, fictional example of the whole mechanism, so it's clear **what** each piece
does and **how** — and, crucially, what is *generic code* vs *the company's own data*.

> The golden rule: **the code is domain-agnostic; the company brings the data** (corpus,
> identities, and the *classification* of who-can-see-what). Nothing about the company
> lives in the mechanism's source.

---

## The company

**Meridian Freight** — a logistics platform. Its system spans **6 repositories**, and
(like any real org) each repo already has an access group in their Entra/AD: the people
who can clone/read that repo. That existing access **is** the classification — we don't
invent one.

| Repo | Stack | Who can read it today (existing AD group) | Sensitivity |
| --- | --- | --- | --- |
| `mf-developer-portal` | Next.js | `all-employees` | public |
| `mf-tracking-api` | .NET | `eng-platform` | internal |
| `mf-routing-service` | Go | `eng-platform` | internal |
| `mf-pricing-engine` | Python | `eng-pricing-restricted` | confidential |
| `mf-fraud-rules` | Python | `sec-fraud-restricted` | confidential |
| `mf-public-sdk` | TypeScript | `all-employees` | public |

The sensitivity column is **not a label someone made up** — it mirrors the repo's real
reader group. That's the professional basis: *access follows the source*.

---

## The flow (what + how)

### 1. Provision the cloud (generic code, their cloud)

```bash
azd up
```

Stands up **Meridian's own** Foundry project, Azure AI Search, Storage, Container Apps —
all from the template's Bicep. Nothing from anyone else's environment carries over.

### 2. Wire identities (their groups)

Meridian already has `eng-platform`, `eng-pricing-restricted`, etc. They map their tiers
to those groups in config (no code change):

```
COCKPIT_ACL_PUBLIC_GROUP=<object-id of all-employees>
COCKPIT_ACL_INTERNAL_GROUP=<object-id of eng-platform>
COCKPIT_ACL_CONFIDENTIAL_GROUP=<object-id of eng-pricing-restricted + sec-fraud-...>
```

> If they *didn't* have groups, `infra/entra/entra.bicep` creates the three tiers — but a
> real org plugs in groups it already manages.

### 3. Generate the wiki — access is **inherited from each repo**

```bash
uv run python -m app.knowledge.wiki_builder --repo ../mf-pricing-engine --component mf-pricing-engine --version v1.0.0 --out ./wiki-out
```

The generator reads the **real source** and writes a faithful, cited wiki. As it does, it
records **which group can read the source repo** into the bundle manifest — so the wiki
page inherits the repo's access. Meridian's `mf-pricing-engine` was readable only by
`eng-pricing-restricted`, so its bundle is born `confidential`:

```jsonc
// wiki-out/mf-pricing-engine/v1.0.0/manifest.json  ← DATA, produced from the repo
{
  "key": "mf-pricing-engine-v1.0.0",
  "component": "mf-pricing-engine",
  "classification": "confidential",   // ← inherited from the repo's reader group
  "pages": [ ... ]
}
```

No markers, no guessing — the manifest's `classification` came from the repo's ACL.

### 4. (Or) the owner declares it explicitly — still data, never code

If the access can't be auto-inherited, the data owner provides one external file
(gitignored, like the corpus). The mechanism reads it; the code stays generic:

```jsonc
// meridian-classification.json   (path → COCKPIT_ACL_CLASSIFICATION; gitignored)
{
  "mf-developer-portal": "public",
  "mf-public-sdk":       "public",
  "mf-tracking-api":     "internal",
  "mf-routing-service":  "internal",
  "mf-pricing-engine":   "confidential",
  "mf-fraud-rules":      "confidential"
}
```

Anything **not** listed falls to `cockpit_acl_default_tier` — **fail-closed**
(`confidential`), so an unclassified doc never leaks by omission.

### 5. Ingest — the mechanism just reads the declared tier and stamps

```bash
COCKPIT_ACL_CLASSIFICATION=./meridian-classification.json uv run python -m app.knowledge.ingest_cockpit
```

For every document it reads the **owner-declared tier** (manifest or the file), maps the
tier → Meridian's group via config, and stamps the index `groups` field + enables
query-time trimming. **`acl_setup.py` contains zero classification logic** — it's pure
read-the-data-and-enforce.

### 6. Consume — each person sees only their entitlement

Meridian devs use the chat. The agent retrieves **as the signed-in user** (their token is
passed to the KB), and Azure AI Search trims to what that user can read:

| Who asks "explain the pricing algorithm" | What the KB returns | Why |
| --- | --- | --- |
| Dana (in `eng-pricing-restricted`) | the real pricing-engine docs, cited | entitled |
| Sam (only `eng-platform`) | "I don't have that in the knowledge I can access" | `mf-pricing-engine` is confidential; Sam isn't in the group |
| Public contractor (`all-employees`) | only the developer-portal / SDK docs | public tier only |

Same question, same agent — **different answers by identity**. The agent literally cannot
surface what the caller isn't cleared for.

### 7. Measure — the gates (their golden, gitignored)

- **Quality**: groundedness + completeness + retrieval-recall gates in CI (`eval/run_eval.py`).
- **Security**: the access-control gate (`eval/access_control_test.py`) asserts Sam never
  retrieves a confidential pricing doc — a single leak fails the build
  (`access_control_violations_max: 0`).

### 8. Defend (Phase 5) — red-team

The AI Red Teaming Agent throws prompt-injection / exfiltration at the chat; a poisoned
doc can't make it leak across tiers. The Attack-Success-Rate gate keeps merges honest.

---

## What was *generic code* vs *Meridian's data*

| Generic code (in the template repo) | Meridian's data (external, gitignored) |
| --- | --- |
| `wiki_builder.py`, `ingest_cockpit.py`, `acl_setup.py`, the secure provider, the eval/red-team harness | the **corpus** (their wikis) |
| tier→group **mapping mechanism** (reads config) | the **group object-IDs** (`.env`) |
| read-classification-and-enforce | the **classification** (manifest `classification` / `meridian-classification.json`) |
| the agent, prompts, gates | their **golden set** + thresholds |

Meridian cloned the template, pointed it at **their** repos, plugged in **their** groups
and classification, and shipped — **without editing a line of the mechanism**. That's the
whole point: the crazy, fixed bits are gone; the company supplies the data, the mechanism
supplies the guarantees.
