<!--
  You are amazing! Thanks for contributing to our project!
  Please, DO NOT DELETE ANY TEXT from this template! (unless instructed).
-->
## Breaking change
<!--
  If your PR contains a breaking change for existing users, it is important
  to tell them what breaks, how to make it work again and why we did this.
  This piece of text is published with the release notes, so it helps if you
  write it towards our users, not us.
  Note: Remove this section if this PR is NOT a breaking change.
-->

None. This adds a new integration.

## Proposed change
<!--
  Describe the big picture of your changes here to communicate to the
  maintainers why we should accept this pull request. If it fixes a bug
  or resolves a feature request, be sure to link to that issue in the
  additional information section.
-->

Add a community-maintained SpaceXAI integration so users can use Grok in Assist with their xAI subscription.

Browser-based OAuth device authorization creates one conversation agent per account. Setup validates account identity and available models; duplicate accounts are rejected. Assist access is selected by default, can be disabled during setup, and is limited to exposed entities. There is no API-key mode.

The unofficial `spacexai-subscription-client` library owns provider communication and OAuth protocol handling. Core supplies shared HTTP sessions and handles configuration, conversation tools, token persistence, and unloading.

This initial contribution targets Bronze and only the conversation platform. Attachments, provider-hosted tools, AI Task, media generation, speech, diagnostics, reauthentication, and reconfiguration are excluded.

Tests cover completed login retries, cancellation, account validation, token rotation across reload, conversation responses, real Assist exposure controls, and provider failures. Permission denial is distinguished from invalid credentials. Token-endpoint timeout regressions verify normal setup retry, a translated conversation error, retained credentials, successful recovery, and cancellation.

## Type of change
<!--
  What type of change does your PR introduce to Home Assistant?
  NOTE: Please, check only 1! box!
  If your PR requires multiple boxes to be checked, you'll most likely need to
  split it into multiple PRs. This makes things easier and faster to code review.
-->

- [ ] Dependency upgrade
- [ ] Bugfix (non-breaking change which fixes an issue)
- [x] New integration (thank you!)
- [ ] New feature (which adds functionality to an existing integration)
- [ ] Deprecation (breaking change to happen in the future)
- [ ] Breaking change (fix/feature causing existing functionality to break)
- [ ] Code quality improvements to existing code or addition of tests

## Additional information
<!--
  Details are important, and help maintainers processing your PR.
  Please be sure to fill out additional details, if applicable.
-->

- This PR fixes or closes issue: Not applicable; this is a new integration.
- This PR is related to issue: [Previous contribution #178765](https://github.com/home-assistant/core/pull/178765). The author closed that PR; this replacement narrows the initial scope to Bronze conversation support and moves provider communication into a separate Python library.
- Link to documentation pull request: Not opened; [prepared incremental documentation](https://github.com/jeffglousher/home-assistant.io/compare/16ad324d9cbadf6d03b94f12ef278b00c7b9999f...codex/spacexai/staged-docs-01-initial).
- Link to developer documentation pull request: Not applicable.
- Link to frontend pull request: Not applicable.
- Client source: https://github.com/jeffglousher/spacexai-subscription-client/compare/main...harden-initial-release
- Client release: Version 0.1.0 is not yet published. Add the verified PyPI and GitHub release links before submitting.
- Brands pull request staging diff: https://github.com/home-assistant/brands/compare/master...jeffglousher:brands:spacexai-initial
- Prepared Core diff: https://github.com/jeffglousher/core/compare/be2e14f4273335fb5ef02b7f636cd01800e1491a...codex/spacexai/staged-01-initial
- Prepared Core commit: https://github.com/jeffglousher/core/commit/cbe618c9800419de39601496779da68e5dd8ed23
- Validation: [Native Linux run](https://github.com/jeffglousher/core/actions/runs/34175174869) tests Core `cbe618c9800419de39601496779da68e5dd8ed23` with client `b5513112b12a14baa43c295cf82cec8be3604ba7`: 44 tests, 99.1701% statement coverage, every integration module above 95%, and zero failures/errors/skips. Native lint, formatting, typing, and dependency regeneration pass; tracked generated files are unchanged. The same exact-source run also passes unchanged script/setup and standard native hooks; strict hassfest remains blocked only by dependency-transparency: todo. Human review, dependency publication, and refreshing/retesting against current upstream remain required.

- First-install validation: Fresh initial-only Home Assistant UI/OAuth login still needs an isolated native host and human authorization; the existing full-stack test system is not that evidence.

## Checklist
<!--
  Put an `x` in the boxes that apply. You can also fill these out after
  creating the PR. If you're unsure about any of them, don't hesitate to ask.
  We're here to help! This is simply a reminder of what we are going to look
  for before merging your code.

  AI tools are welcome, but contributors are responsible for *fully*
  understanding the code before submitting a PR. Please follow our AI policy:
  https://developers.home-assistant.io/docs/ai_policy
-->

- [ ] I understand the code I am submitting and can explain how it works.
- [ ] The code change is tested and works locally.
- [ ] Local tests pass. **Your PR cannot be merged unless tests pass**
- [x] There is no commented out code in this PR.
- [ ] I have followed the [development checklist][dev-checklist]
- [ ] I have followed the [perfect PR recommendations][perfect-pr]
- [x] The code has been formatted using Ruff (`ruff format homeassistant tests`)
- [x] Tests have been added to verify that the new code works.
- [ ] Any generated code has been carefully reviewed for correctness and compliance with project standards.

If user exposed functionality or configuration variables are added/changed:

- [x] Documentation added/updated for [www.home-assistant.io][docs-repository]

If the code communicates with devices, web services, or third-party tools:

- [ ] The [manifest file][manifest-docs] has all fields filled out correctly.  
      Updated and included derived files by running: `python3 -m script.hassfest`.
- [x] New or updated dependencies have been added to `requirements_all.txt`.  
      Updated by running `python3 -m script.gen_requirements_all`.
- [ ] For the updated dependencies a diff between library versions and ideally a link to the changelog/release notes is added to the PR description.

<!--
  This project is very active and we have a high turnover of pull requests.

  Unfortunately, the number of incoming pull requests is higher than what our
  reviewers can review and merge so there is a long backlog of pull requests
  waiting for review. You can help here!
  
  By reviewing another pull request, you will help raise the code quality of
  that pull request and the final review will be faster. This way the general
  pace of pull request reviews will go up and your wait time will go down.
  
  When picking a pull request to review, try to choose one that hasn't yet
  been reviewed.

  Thanks for helping out!
-->

To help with the load of incoming pull requests:

- [ ] I have reviewed two other [open pull requests][prs] in this repository.

[prs]: https://github.com/home-assistant/core/pulls?q=is%3Aopen+is%3Apr+-author%3A%40me+-draft%3Atrue+-label%3Awaiting-for-upstream+sort%3Acreated-desc+review%3Anone+-status%3Afailure

<!--
  Thank you for contributing <3

  Below, some useful links you could explore:
-->
[dev-checklist]: https://developers.home-assistant.io/docs/development_checklist/
[manifest-docs]: https://developers.home-assistant.io/docs/creating_integration_manifest/
[quality-scale]: https://developers.home-assistant.io/docs/integration_quality_scale_index/
[docs-repository]: https://github.com/home-assistant/home-assistant.io
[perfect-pr]: https://developers.home-assistant.io/docs/review-process/#creating-the-perfect-pr
