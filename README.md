# Articles

Written with [Zola](https://www.getzola.org/) and published to <https://florenzen.github.io/articles/> by GitHub Actions.

## Setup

1. Open the repo in VS Code and run *Dev Containers: Reopen in Container*. The image (`.devcontainer/Dockerfile`) installs a pinned Zola version from the [pkg.haus](https://pkg.haus) Debian archive, as listed in the [Zola installation docs](https://www.getzola.org/documentation/getting-started/installation/#debian).
2. One time only: in the GitHub repo, go to *Settings → Pages → Build and deployment → Source* and select *GitHub Actions*.

## Writing

- Add a Markdown file under `content/articles/`, e.g. `content/articles/my-topic.md`.
- `draft = true` keeps an article out of the published site but shows it in the local preview.
- Text before `<!-- more -->` is the summary.
- Put images next to an article by turning it into a folder: `content/articles/my-topic/index.md` and `content/articles/my-topic/diagram.png`, then link `![](diagram.png)`.
- Zola 0.23+ runs Tera templating on content, so literal `{{ ... }}` or `{% ... %}` in an article (outside code blocks) must be wrapped in `{% raw %}...{% endraw %}`.

## VS Code tasks

Use *Terminal → Run Task…*:

| Task                        | What it does                                             |
| --------------------------- | -------------------------------------------------------- |
| Zola: serve (with drafts)   | Live preview at <http://localhost:1111>, drafts included |
| Zola: serve                 | Live preview of exactly what will be published           |
| Zola: build                 | Build into `public/`                                     |
| Zola: check                 | Check the site, including internal and external links    |

## Linting and formatting

| Files                                                  | Linter / formatter                | Config                     |
| ------------------------------------------------------ | --------------------------------- | -------------------------- |
| Markdown                                               | markdownlint                      | `.markdownlint.json`       |
| SCSS (`sass/`)                                         | stylelint, Prettier (format)      | `.stylelintrc.json`        |
| JavaScript (`static/js/`, `eslint.config.mjs`)         | ESLint, Prettier (format)         | `eslint.config.mjs`        |
| HTML (`templates/`)                                    | djLint (lint and format)          | `.djlintrc`                |
| JSON and YAML (also `.djlintrc`, `.nsprc`)             | Prettier (format)                 | Prettier defaults          |
| TOML (`config.toml`, `ruff.toml`)                      | Taplo (lint and format)           | Taplo defaults             |
| GitHub workflows (`.github/workflows/`)                | actionlint                        | none                       |
| Shell scripts (`.devcontainer/*.sh`)                   | ShellCheck (lint), shfmt (format) | `.editorconfig` (shfmt)    |
| Dockerfile (`.devcontainer/Dockerfile`)                | hadolint                          | `.hadolint.yaml`           |
| Python (`scripts/`)                                    | Ruff (lint), Black (format)       | `ruff.toml`                |
| Images (`content/`)                                    | `scripts/image-metadata.py`       | `[extra]` in `config.toml` |
| npm dependencies (`package.json`, `package-lock.json`) | npm audit (via better-npm-audit)  | `.nsprc` (exceptions)      |

The tool versions are pinned in `package.json` and `requirements-dev.txt`. The devcontainer installs them, and the VS Code extensions, the pre-commit hook and CI all use these same versions. The checks run automatically on every `git commit` (installed by `pre-commit install` in `.devcontainer/post-create.sh`). Formatting a file in VS Code gives the same result as the commands below.

### Check for all issues

```sh
pre-commit run --all-files
```

This runs every check on the whole repo, the same way CI does. pre-commit only sees files git knows about, so `git add` new files first.

### Auto-fix issues

```sh
npx markdownlint-cli2 "**/*.md" "#node_modules" --fix       # Markdown
npx stylelint "sass/**/*.scss" --fix                        # SCSS lint issues
npx eslint . --fix                                          # JavaScript lint issues
npx prettier --write "sass/**/*.scss" "**/*.{js,mjs,json,yml,yaml}" "!**/*-lock.json" .djlintrc .nsprc  # SCSS, JavaScript, JSON and YAML formatting
npx taplo fmt                                               # TOML formatting
shfmt --write .devcontainer                                 # shell script formatting
ruff check --fix scripts                                    # Python lint issues
black scripts                                               # Python formatting
djlint templates --reformat                                 # template formatting
```

Anything these commands can't repair has to be fixed by hand, including all findings of `djlint --lint`, Taplo lint, actionlint, ShellCheck and hadolint, and many ESLint ones (e.g. unused variables). For a vulnerable npm package, update it or, if it can't be reached, add a documented exception with an expiry date to `.nsprc`. Afterwards, run `pre-commit run --all-files` again.

### JavaScript

The scripts in `static/js/` are plain browser scripts without a build step: they are copied to the site as they are and loaded with `<script>`. `eslint.config.mjs` lints them as browser scripts with ESLint's recommended rules; Prettier does the formatting. In VS Code, the ESLint extension shows problems while you type and *Format Document* uses Prettier.

### Python

Ruff lints the scripts in `scripts/`; the rules are selected in `ruff.toml`. Black formats them, with its default settings. In VS Code, the Ruff extension shows problems while you type and *Format Document* uses the Black extension. Both extensions are set to use the versions pinned in `requirements-dev.txt` (see `.vscode/settings.json`), not the ones bundled with them.

### Images

Two pre-commit checks cover the images in `content/` (JPEG, PNG, WebP, GIF, TIFF and SVG):

- **SVGs must not contain text.** Text would be drawn with fonts the visitor may not have. The check prints how to convert text to paths in Inkscape (*Edit → Select All in All Layers*, then *Path → Object to Path*).
- **Raster images must not contain location data** (GPS coordinates and similar), and **every image must carry a copyright and license entry** matching the site footer: author, `license` and `license_url` from `[extra]` in `config.toml`.

To remove location data and add the missing copyright and license entries:

```sh
python3 scripts/image-metadata.py fix content/articles/my-topic/*.jpg content/articles/my-topic/*.svg
```

Existing copyright entries are kept. The copyright year is taken from the photo's recorded date, otherwise the current year (change it with `--year 2025`). Raster images are edited with exiftool (installed in the devcontainer and in CI); only the metadata changes, not the image itself. In SVGs, the entry is added in the format Inkscape shows under *File → Document Properties → Metadata*.

### Format a single file

```sh
npx prettier --write sass/style.scss
npx prettier --write static/js/lightbox.js
djlint templates/page.html --reformat
```

## CI

- **Push to `main`:** `.github/workflows/deploy.yml` runs the lint workflow (`.github/workflows/lint.yml`, which runs `pre-commit run --all-files`). Only if it passes does it run `zola check --skip-external-links`, build the site and deploy it to GitHub Pages. External links are left out so that a site that is down, or blocks CI, can't stop a deploy.
- **Push to any other branch:** `.github/workflows/check.yml` runs the same lint workflow and, alongside it, `zola check --drafts`, including external links.

Sites that block requests from CI are excluded from the link check in `[link_checker]` in `config.toml`.

## Updating Zola

The version is set once, in `ZOLA_VERSION` in `.devcontainer/install-zola.sh`. The devcontainer and both workflows (which run in a `debian:trixie` container) use that script. After changing it, run *Dev Containers: Rebuild Container*.
