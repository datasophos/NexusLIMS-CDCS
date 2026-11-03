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

Open `docs/_build/html/index.html`. GitHub Actions builds pull requests and
publishes same-repository PR previews to `pr-<number>/`, main to `latest/`, and
published CDCS releases to `v<version>-nx<n>/` and `stable/` (prereleases do not
replace `stable/`). Fork PRs receive a build artifact instead of a Pages preview.
The `gh-pages` branch must be configured as the GitHub Pages source. PR previews
remain on that branch until they are removed by a maintainer.
