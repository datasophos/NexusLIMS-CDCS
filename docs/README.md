# Building the CDCS documentation

The frontend guide lives in this repository. Update it in the same pull request
as user-facing behavior, configuration, and deployment changes. The compatibility
matrix remains in the NexusLIMS backend repository.

To build the guide locally:

```sh
python -m venv /tmp/cdcs-docs-venv
/tmp/cdcs-docs-venv/bin/pip install -r docs/requirements.txt
/tmp/cdcs-docs-venv/bin/sphinx-build -b html -n -W --keep-going docs docs/_build/html
```

Open `docs/_build/html/index.html`. Cloudflare Pages builds branch previews
using `scripts/build_cloudflare_docs.sh` and posts preview links to pull requests.
Its project connects to `datasophos/NexusLIMS-CDCS`, uses Python 3.13, runs
`bash scripts/build_cloudflare_docs.sh`, and publishes `docs/_build/html`.
The Cloudflare project is for previews; production-branch deployments are disabled.

GitHub Actions builds every pull request and publishes main to `latest/` and
published CDCS releases to `v<version>-nx<n>/` and `stable/` (prereleases do not
replace `stable/`). The `gh-pages` branch must be configured as the GitHub Pages
source. Fork PRs receive a GitHub Actions build artifact; Cloudflare Git integration
preview availability depends on its repository integration and permissions.
