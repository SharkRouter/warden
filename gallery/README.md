# Warden Gallery

Static site of automated governance audits for popular open-source
AI-agent frameworks. Each target gets a landing page with its Warden
score, level, and a link to the full HTML report.

The gallery is purely a marketing / credibility artifact — it does not
ship with the `warden-ai` PyPI package. It lives here so the build
script stays in sync with the scanner it invokes.

## What's in here

```
gallery/
├── targets.toml        # List of OSS projects to scan
├── build.py            # Clone + scan + assemble (idempotent, stdlib-only)
├── README.md           # You are here
├── out/                # Generated output (gitignored)
│   ├── index.html
│   ├── assets/gallery.css
│   └── <slug>/
│       ├── index.html  # SEO landing (title, meta, OG, JSON-LD)
│       ├── report.html # Full warden report
│       ├── report.json
│       └── report.sarif
└── repos/              # Shallow clones of target repos (gitignored)
```

## Quick start

```bash
# From the warden repo root, with the project's venv active:
.venv/Scripts/python.exe gallery/build.py              # Build everything
.venv/Scripts/python.exe gallery/build.py --only crewai,langgraph  # Specific targets
.venv/Scripts/python.exe gallery/build.py --no-clone   # Skip git fetch (fast iteration)
.venv/Scripts/python.exe gallery/build.py --clean      # Wipe out/ and repos/ first
```

On Linux/macOS, use `python gallery/build.py ...` instead.

The build is idempotent. Re-running only re-clones (`git fetch --depth=1 && reset --hard`)
and re-scans — no extra work if nothing changed upstream. Per-target failures
are isolated: one bad clone or crash does not take down the rest of the run.

## Adding a target

Append a `[[target]]` block to [`targets.toml`](./targets.toml):

```toml
[[target]]
slug = "my-framework"              # URL-safe, lowercase, hyphenated
name = "My Framework"              # Display name
repo = "owner/repo"                # GitHub path (used for clone + links)
category = "Framework"             # Displayed in the table
description = "One-line pitch."
scan_path = "packages/core"        # Optional: scan a subdirectory
homepage = "https://example.com/"  # Optional: link from the landing page
```

**Selection guidelines:**

- **Popular** — only frameworks with >5k stars that people actually search for.
- **Active** — commits in the last 6 months.
- **Searchable** — someone types "{name} security" into Google and finds nothing good.
- **Bounded scan time** — under ~5 minutes on a modest laptop. For huge monorepos,
  use `scan_path` to focus on the core package.
- **Distinct category** — avoid three flavors of the same thing.

## Deploying the gallery

The generated site is fully static. Three deployment options:

### 1. GitHub Pages (recommended — free, automatic HTTPS)

Push the contents of `gallery/out/` to a `gh-pages` branch or `docs/`
directory of a separate repo, then enable Pages in Settings. The site
is entirely static so there's no build step on GitHub's end.

### 2. `warden.whitefin.ai/gallery/`

Upload `gallery/out/` to the Caddy host at `/opt/sharkagent/gallery/`
(via scp, following the landing-v2 deploy pattern documented in the
project root `CLAUDE.md`). Caddy already serves static content from
that path — no container rebuild needed.

### 3. Any static host

Netlify, Vercel, Cloudflare Pages, S3 + CloudFront all work. Point them
at `gallery/out/` as the publish directory.

## Rebuild cadence

Manual quarterly refresh is fine. Automate only when:

- A target cuts a major version (e.g. LangChain 1.0 → 2.0).
- Warden's scoring model bumps (v4.3 → v5.0 would invalidate all scores).
- CI starts catching regressions the gallery would have surfaced.

**Do not wire this into the main CI pipeline.** A full rebuild clones
10+ repos and scans each one. That's appropriate for a scheduled nightly
or manual workflow, not for every push.

## Attribution + vendor neutrality

Every landing page:

- Links back to the source repository and homepage.
- States clearly that the scan is automated.
- Points to Warden's methodology and scoring model.
- Invites framework maintainers to open an issue with corrections.

Warden is vendor-neutral. If a framework maintainer disputes a finding,
their PR or issue gets the same priority as any other. Keep it that way.
