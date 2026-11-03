# Building the CDCS documentation

The frontend guide lives in this repository. Update it in the same pull request
as user-facing behavior, configuration, and deployment changes. The compatibility
matrix remains in the NexusLIMS backend repository.

To build the guide locally:

```sh
uv run --group docs sphinx-build -b html -n -W --keep-going docs docs/_build/html
```

Open `docs/_build/html/index.html`. The `nexuslims-cdcs-docs` Cloudflare Pages
project builds branch previews using `scripts/build_cloudflare_docs.sh` and posts
preview links to pull requests. It connects to `datasophos/NexusLIMS-CDCS`, uses Python 3.13, runs
`bash scripts/build_cloudflare_docs.sh`, and publishes `docs/_build/html`.
The Cloudflare project is for previews; production-branch deployments are disabled.

GitHub Actions builds every pull request and publishes main to `latest/` and
published CDCS releases to `v<version>-nx<n>/` and `stable/` (prereleases do not
replace `stable/`). The `gh-pages` branch must be configured as the GitHub Pages
source. Fork PRs receive a GitHub Actions build artifact; Cloudflare Git integration
preview availability depends on its repository integration and permissions.

To build the guide and automatically rebuild it as files change, run:

```sh
./scripts/watch_docs.sh
```

The preview is available at `http://127.0.0.1:8765/`. Pass additional
`sphinx-autobuild` options to the script, such as `--port 9000`. Stop it with
Ctrl+C.
