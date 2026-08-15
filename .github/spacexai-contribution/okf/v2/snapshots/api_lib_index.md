# Building a Python library for an API

Source: https://developers.home-assistant.io/docs/api_lib_index
Retrieved: 2026-08-15

One of the foundational rules of Home Assistant is that we do not include
any protocol specific code. Instead, this code should be put into a
standalone Python library and published to PyPI.

## Basic library requirements

* The library must have source distribution packages available.
* The library versions published on PyPI should correspond to tagged
  releases in a public online repository.
* The publishing on PyPI must be automated.
* Issue trackers must be enabled.
* The library and possible subdependencies must use an OSI-approved
  license, reflected in package metadata.

The library should split authentication (the only code that talks to the
API) from data models.
