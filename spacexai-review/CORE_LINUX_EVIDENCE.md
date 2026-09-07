# Native Linux verification of the prepared Core stack

Verified 2026-09-07 UTC (2026-09-06 America/Chicago).

All seven canonical ready layers pass their own integration tests against the
matching committed client version on Ubuntu 24.04, Python 3.14.5. Every run passed
Ruff, formatting, MyPy, and Pylint. JUnit reports contain zero failures, errors, or
skipped tests. Every integration Python module exceeds 95% coverage in every
layer; percentages below are the unrounded report values rounded only for display.

These are native Linux runs using the original pytest-socket protections. The
earlier Windows compatibility shims are not part of this evidence. The workflow
checks out exact source commits, installs the corresponding client source, checks
its installed version against the integration manifest, and generates English
translations before running Home Assistant's tests.

## Exact source pairs and results

1. Initial OAuth conversation — **39 tests**, aggregate **99.1701%**.
   - Core: `c9e6db462a36cd5a70e12672d09579bd757f0e1b`
   - Client 0.1.0: `c4fd662c281b5700a5c5d547b4afe097c8e5be22`
   - `__init__.py`, `config_flow.py`, and `const.py`: 100% each.
   - `conversation.py`: 97.7011%.
   - [Native run 34078831785](https://github.com/jeffglousher/core/actions/runs/34078831785)

2. Conversation tools and attachments — **53 tests**, aggregate **99.0964%**.
   - Core: `a27a9ff9af041d1ae48b41a89f3f85466ec62506`
   - Client 0.2.0: `25952c5f839a30cd26e374d1eae6408fa46392c1`
   - `__init__.py`, `config_flow.py`, and `const.py`: 100% each.
   - `conversation.py`: 97.6378%.
   - [Native run 34079227294](https://github.com/jeffglousher/core/actions/runs/34079227294)

3. AI Task and image generation — **85 tests**, aggregate **99.5624%**.
   - Core: `53b75924a577da6aee2a35ddba13d617e094d83f`
   - Client 0.3.0: `80e36af0863d5b31742fddd6edd0ccdb306f1bcc`
   - `__init__.py`, `ai_task.py`, `config_flow.py`, and `const.py`: 100% each.
   - `conversation.py`: 98.4252%.
   - [Native run 34080052271](https://github.com/jeffglousher/core/actions/runs/34080052271)

4. Speech-to-text and text-to-speech — **101 tests**, aggregate **99.6820%**.
   - Core: `9f96bf6adc9ccc6dbc23ae66b099c86f4ca1831e`
   - Client 0.4.0: `9133ea56b89e6b35081f2bb19826bb83088582c8`
   - `__init__.py`, `ai_task.py`, `config_flow.py`, `const.py`, `entity.py`,
     `stt.py`, and `tts.py`: 100% each.
   - `conversation.py`: 98.4252%.
   - [Native run 34081052741](https://github.com/jeffglousher/core/actions/runs/34081052741)

5. Video and local media actions — **123 tests**, aggregate **99.2500%**.
   - Core: `b64085011ba8309005ec645d9500d76c45ba8c64`
   - Client 0.5.0: `b2d823452e5054ece8b7a90fb7b172f5ac1d1a7c`
   - `__init__.py`, `ai_task.py`, `config_flow.py`, `const.py`, `entity.py`,
     `models.py`, `services.py`, `stt.py`, and `tts.py`: 100% each.
   - `conversation.py`: 98.4252%; `media.py`: 96.2264%.
   - [Native run 34081054381](https://github.com/jeffglousher/core/actions/runs/34081054381)

6. Account reauthentication and reconfiguration — **134 tests**, aggregate **99.2736%**.
   - Core: `99c30c08fb74e97ba1fdba02b809ebb966d0a91b`
   - Client 0.5.0: `b2d823452e5054ece8b7a90fb7b172f5ac1d1a7c`
   - `__init__.py`, `ai_task.py`, `config_flow.py`, `const.py`, `entity.py`,
     `models.py`, `services.py`, `stt.py`, and `tts.py`: 100% each.
   - `conversation.py`: 98.4375%; `media.py`: 96.2264%.
   - [Native run 34081055760](https://github.com/jeffglousher/core/actions/runs/34081055760)

7. Diagnostics — **137 tests and 3 snapshots**, aggregate **99.2814%**.
   - Core: `2315fa45b978aa1ebf637c111d0c1410d68d12ea`
   - Client 0.5.0: `b2d823452e5054ece8b7a90fb7b172f5ac1d1a7c`
   - `__init__.py`, `ai_task.py`, `config_flow.py`, `const.py`, `diagnostics.py`,
     `entity.py`, `models.py`, `services.py`, `stt.py`, and `tts.py`: 100% each.
   - `conversation.py`: 98.4375%; `media.py`: 96.2264%.
   - [Native run 34081057144](https://github.com/jeffglousher/core/actions/runs/34081057144)

## Repairs validated in their introducing layers

Wave 3 now tests failed refreshes (HTTP 400, 401, 429, and 500) and unusable stored
tokens through the public AI data and image APIs. It verifies translated errors,
no inference calls with unusable credentials, and the absence of reauthentication
before Wave 6. These tests cover the shared token helper after its extraction in
Wave 4. Wave 6 adjusts the expectations for its new reauthentication behavior.

Wave 5 verifies the actual registered admin guard without treating Home
Assistant's own untranslated `Unauthorized` exception as an integration exception.
The test checks the denied user identity and absence of signing/provider effects.
Its deterministic filename mocks replace only the integration's `secrets` module
binding, preserving Home Assistant's real signing secret. The previous short-HMAC
warning is absent from the passing native runs.

The Wave 4 client now consumes text-to-speech response chunks through EOF while
enforcing the combined audio-size limit. The repair is inherited by client 0.5.0.
All four affected Core layers were rerun against those exact repaired client
commits; the source pairs above replace the earlier pre-repair pairs. Client tests
use a real aiohttp StreamReader with later chunks or errors scheduled on the next
event-loop turn, so returning only the first available chunk cannot pass.
An independent read-only runtime audit also confirmed exact-limit acceptance,
cancellation propagation, and response-context cleanup. These are package behavior
checks, separate from the integration coverage percentages above.

## Repeatable coverage gate

Fork-only validation commit `9eba219c3ecd1651152ce168759f4d268b98fe09` adds
`script/spacexai_check_coverage.py`. It checks every integration `.py` file is
present in the JSON report and requires a strictly greater-than-95% unrounded
coverage value. Missing files, empty reports, invalid mappings, absent source
trees, non-numeric values, and NaN cannot pass.

Deterministic verification accepted actual native reports from Waves 1, 3, and 7.
It rejected synthetic 94%, exactly 95%, NaN, a missing module, missing/empty/invalid
report mappings, an absent report file, and an absent source tree. The passing
suite results above were also inspected directly rather than inferred from an
aggregate percentage.

The gate also passed end-to-end in [native run 34080509382](https://github.com/jeffglousher/core/actions/runs/34080509382)
against the same canonical Wave 1 Core/client pair. Its `coverage-gate.txt`
confirms every integration Python module is present and above the threshold.

The applicable [Home Assistant coverage rule](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-coverage/)
requires above 95% for every integration module and has no exceptions.

Artifacts are retained by each linked GitHub run and downloaded under
`.worktrees/spacexai-validation/evidence/<run-id>/`. Each directory contains
`validation-sources.txt`, JUnit results, coverage JSON/XML, pytest output, and
lint/type output. This document records integration-scoped tests and static checks;
it does not assert a full Home Assistant repository test-suite run or publication
of the client to PyPI.
