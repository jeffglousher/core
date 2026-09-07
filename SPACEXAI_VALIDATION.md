# SpaceXAI staging validation

This branch contains fork-only test infrastructure. It is not part of the Home
Assistant contribution stack. The workflow runs unmodified Home Assistant tests on
Ubuntu with the exact Core and Python client commits recorded in its artifacts.
Home Assistant's normal socket protections remain enabled.

The package has not been published to PyPI. The full `script/setup` dependency
installation therefore cannot resolve `requirements_all.txt` against PyPI. This
workflow installs Core's pinned runtime and testing requirements, the selected
client source, and the integration/platform dependencies needed by the tests. It
does not alter the integration's manifest requirement or test bootstrap.

Pushes validate the pinned first-wave commits. Manual runs accept another pair of
Core/client commits so each layer can be tested against its matching package.
Artifacts contain commit identities, installed package version, test results,
coverage, and lint/type-check results. Publishing and validating the actual PyPI
release remain separate release gates.
