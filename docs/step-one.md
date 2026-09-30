# Step One: wiki scaffolding

Step One provides isolated filesystem wiki projects with per-project conventions.

## Commands

```powershell
.venv/Scripts/python.exe -m llm_wiki wiki create "Property & Casualty Insurance"
.venv/Scripts/python.exe -m llm_wiki wiki list
.venv/Scripts/python.exe -m llm_wiki wiki inspect property-casualty-insurance
```

Create another wiki with Markdown links and an additional required frontmatter field:

```powershell
.venv/Scripts/python.exe -m llm_wiki wiki create "Regulatory Research" `
  --link-style markdown `
  --extra-field jurisdiction
```

Projects default to `data/wikis`, controlled by `WIKI_PROJECTS_DIR`. Generated local projects are ignored by Git because `data/` is ignored.

## Generated structure

```text
property-casualty-insurance/
├── .wiki-project.json
├── SCHEMA.md
├── concepts/
├── entities/
├── raw/
├── summaries/
└── topics/
```

`overview` pages live in `topics/`. Each project owns its link style and required metadata. Every page requires `title`, `type`, `date_created`, `date_updated`, `tags`, and `sources`. Project-specific fields are exact: missing and unknown fields are rejected.

The page store in `storage/markdown.py` provides atomic create/update operations, preserves creation timestamps, restricts paths to registered page directories, enforces that page type matches its directory, parses strict YAML without duplicate keys, and resolves either wikilinks or relative Markdown links. Inspection reports directory/page counts and broken or ambiguous links. Files in `raw/` are never modified by page operations.

The CLI deliberately has no delete command. Manually deleting a project directory removes it from subsequent listings, as required by the challenge.
