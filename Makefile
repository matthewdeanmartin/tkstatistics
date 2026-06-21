UV ?= uv
MAKEFLAGS += --no-print-directory
export PYTHONUTF8 := 1

PACKAGE := tkstatistics
PYTHON_TARGETS := tkstatistics tests
PYLINT_MAIN_TARGETS := tkstatistics
PYLINT_TEST_TARGETS := tests
PYLINT_SCRIPTS_TARGETS := scripts
MARKDOWN_TARGETS := README.md CHANGELOG.md docs
YAML_TARGETS := .github
GHA_WORKFLOWS := .github/workflows
ABOUT_FILE := tkstatistics/__about__.py
CHANGELOG := CHANGELOG.md
COV_FAIL_UNDER := 35

.PHONY: \
	sync \
	pre-commit-install \
	format format-python format-yaml format-markdown \
	format-check format-check-python format-check-yaml format-check-markdown \
	lint lint-check ruff-fix ruff-check pylint pylint-tests pylint-scripts \
	spell \
	docs-check docs-check-docstrings docs-check-pydoctest docs-check-links changelog-verify \
	dead-code vulture \
	security bandit audit \
	run smoke test test-ci tox \
	typecheck typecheck-mypy \
	metadata metadata-check version-check dev-status \
	gha-validate gha-pin gha-upgrade publish-gha \
	prerelease publish-check publish \
	check check-ci \
	help

help:
	@echo "Targets:"
	@echo "  sync                   Install / refresh dependencies"
	@echo "  pre-commit-install     Install pre-commit hooks into .git/hooks"
	@echo ""
	@echo "  format                 Auto-format all code and markup"
	@echo "  format-check           Check formatting without changes"
	@echo "  lint                   Ruff fix + pylint (main + tests + scripts)"
	@echo "  lint-check             Ruff check + pylint (read-only)"
	@echo "  spell                  Spell-check code, docs, and README"
	@echo ""
	@echo "  run                    Launch the tkinter app"
	@echo "  smoke                  CLI smoke check (--help)"
	@echo "  test                   Run pytest suite with coverage"
	@echo "  test-ci                Run pytest -n auto (parallel, for CI)"
	@echo "  tox                    Run tests across py311-py314 via tox"
	@echo ""
	@echo "  typecheck              Run mypy"
	@echo "  security               Run bandit + uv audit"
	@echo ""
	@echo "  metadata               Regenerate __about__.py from pyproject.toml"
	@echo "  metadata-check         Verify __about__.py is in sync"
	@echo "  version-check          Verify version consistency (jiggle_version)"
	@echo "  dev-status             Verify Development Status classifier"
	@echo ""
	@echo "  docs-check             All doc checks (docstrings + links + pydoctest + changelog)"
	@echo "  docs-check-docstrings  interrogate docstring coverage"
	@echo "  docs-check-pydoctest   pydoctest docstring example tests"
	@echo "  docs-check-links       linkcheckMarkdown"
	@echo "  changelog-verify       kacl-cli verify CHANGELOG.md"
	@echo ""
	@echo "  dead-code              vulture (advisory, non-blocking)"
	@echo ""
	@echo "  gha-validate           YAML parse + zizmor"
	@echo "  gha-pin                Pin GHA action refs to commit SHAs"
	@echo "  gha-upgrade            Pin + validate (gha-pin then gha-validate)"
	@echo "  publish-gha            Dispatch the GitHub Actions publish workflow"
	@echo ""
	@echo "  check                  Full local quality gate"
	@echo "  check-ci               CI quality gate (no formatting mutations)"
	@echo "  prerelease             All checks before publishing"
	@echo "  publish-check          Build wheel and list dist/ contents"
	@echo "  publish                Publish via uv (OIDC or UV_PUBLISH_TOKEN)"

sync:
	@$(UV) sync --all-extras --all-groups

pre-commit-install:
	@$(UV) run pre-commit install

# ── Formatting ────────────────────────────────────────────────────────────────

format: format-python format-yaml format-markdown

format-python:
	@$(UV) run isort $(PYTHON_TARGETS)
	@$(UV) run black $(PYTHON_TARGETS)
	@$(UV) run ruff check --fix --quiet $(PYTHON_TARGETS)
	@$(UV) run black $(PYTHON_TARGETS)

format-yaml:
	@$(UV) run yamlfix $(YAML_TARGETS)

format-markdown:
	@$(UV) run mdformat $(MARKDOWN_TARGETS)

format-check: format-check-python format-check-yaml format-check-markdown

format-check-python:
	@$(UV) run isort --check-only $(PYTHON_TARGETS)
	@$(UV) run black --check $(PYTHON_TARGETS)
	@$(UV) run ruff check --quiet $(PYTHON_TARGETS)

format-check-yaml:
	@$(UV) run yamlfix --check $(YAML_TARGETS)

format-check-markdown:
	@$(UV) run mdformat --check $(MARKDOWN_TARGETS)

# ── Linting ───────────────────────────────────────────────────────────────────

lint: ruff-fix pylint pylint-tests pylint-scripts

lint-check: ruff-check pylint pylint-tests pylint-scripts

ruff-fix:
	@$(UV) run ruff check --fix --quiet $(PYTHON_TARGETS)

ruff-check:
	@$(UV) run ruff check --quiet $(PYTHON_TARGETS)

pylint:
	@$(UV) run pylint --fail-under 9.5 --rcfile=.pylintrc $(PYLINT_MAIN_TARGETS)

pylint-tests:
	@$(UV) run pylint --fail-under 9.5 --rcfile=.pylintrc_tests $(PYLINT_TEST_TARGETS)

pylint-scripts:
	@$(UV) run pylint --fail-under 8.5 --rcfile=.pylintrc_scripts $(PYLINT_SCRIPTS_TARGETS)

# ── Spell check ───────────────────────────────────────────────────────────────

spell:
	@$(UV) run pylint --enable C0401,C0402,C0403 --rcfile=.pylintrc_spell $(PYLINT_MAIN_TARGETS)
	@$(UV) run codespell README.md --ignore-words=private_dictionary.txt
	@$(UV) run codespell $(PACKAGE) --ignore-words=private_dictionary.txt

# ── Documentation checks ─────────────────────────────────────────────────────

docs-check: docs-check-docstrings docs-check-pydoctest docs-check-links changelog-verify

docs-check-docstrings:
	@$(UV) run interrogate $(PACKAGE) --verbose

docs-check-pydoctest:
	@$(UV) run pydoctest --config .pydoctest.json \
		| grep -v "__init__" | grep -v "__main__" | grep -v "Unable to parse" || true

docs-check-links:
	@$(UV) run mdformat --check README.md docs/*.md || true

changelog-verify:
	@$(UV) run changelogmanager validate

# ── Dead code analysis (advisory — non-blocking) ─────────────────────────────

dead-code: vulture

vulture:
	@echo "=== vulture (advisory) ==="
	@$(UV) run vulture $(PACKAGE) --min-confidence 80 || true

# ── Security ──────────────────────────────────────────────────────────────────

security: bandit audit

bandit:
	@$(UV) run bandit -q -c pyproject.toml -r $(PACKAGE)

audit:
	@echo "=== uv audit ==="
	@$(UV) audit

# ── Run / Tests ───────────────────────────────────────────────────────────────

run:
	@$(UV) run tkstatistics

smoke:
	@$(UV) run bash scripts/bash_help.sh

test:
	@$(UV) run pytest -q -p no:sugar \
		--cov=$(PACKAGE) \
		--cov-report=html \
		--cov-report=term-missing \
		--cov-fail-under=$(COV_FAIL_UNDER) \
		--junitxml=junit.xml \
		--timeout=60

test-ci:
	@$(UV) run pytest -q -p no:sugar -n auto --dist=loadfile \
		--cov=$(PACKAGE) \
		--cov-report=xml \
		--cov-fail-under=$(COV_FAIL_UNDER) \
		--junitxml=junit.xml \
		--timeout=60

tox:
	@$(UV) run tox

# ── Type checking ─────────────────────────────────────────────────────────────

typecheck: typecheck-mypy

typecheck-mypy:
	@$(UV) run mypy --hide-error-context $(PACKAGE)

# ── Metadata / version ───────────────────────────────────────────────────────

metadata:
	@$(UV) run metametameta pep621 --name $(PACKAGE) --source pyproject.toml --output $(ABOUT_FILE)

metadata-check:
	@$(UV) run metametameta sync-check --output __about__.py

version-check:
	@$(UV) run jiggle_version check

dev-status:
	@$(UV) run troml-dev-status validate .

# ── GitHub Actions maintenance ───────────────────────────────────────────────

gha-validate:
	@echo "Validating GitHub Actions workflows"
	@$(UV) run python -c "import pathlib, yaml; [yaml.safe_load(p.read_text(encoding='utf-8')) for p in pathlib.Path('$(GHA_WORKFLOWS)').glob('*.yml')]; print('YAML parse OK')"
	@uvx zizmor --no-progress --no-exit-codes .

gha-pin:
	@echo "Pinning GitHub Actions to current commit SHAs"
	@$(UV) run python -c "import os, subprocess, sys; \
token=os.environ.get('GITHUB_TOKEN') or subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True).stdout.strip(); \
assert token, 'Set GITHUB_TOKEN or run: gh auth login'; \
env=dict(os.environ, GITHUB_TOKEN=token); \
raise SystemExit(subprocess.run(['gha-update'], env=env).returncode)"

gha-upgrade: gha-pin gha-validate
	@echo "GitHub Actions upgrade complete"

publish-gha:
	@echo "Dispatching GitHub Actions publish workflow"
	gh workflow run release.yml --ref main

# ── Release gates ─────────────────────────────────────────────────────────────

publish-check:
	@$(UV) build
	@echo "Distribution built — inspect dist/ before publishing."
	@ls -lh dist/

publish:
	@echo "Publishing via uv (set UV_PUBLISH_TOKEN or configure OIDC trusted publishing)"
	@$(UV) publish

check: format-check lint-check security test typecheck metadata-check version-check
	@echo "All checks passed."

check-ci: lint-check security test-ci typecheck metadata-check version-check
	@echo "CI checks passed."

prerelease: check dev-status docs-check smoke spell publish-check
	@echo "Pre-release checks complete — ready to publish."
