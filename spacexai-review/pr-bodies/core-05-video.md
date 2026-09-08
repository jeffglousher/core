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


None.

## Proposed change
<!--
  Describe the big picture of your changes here to communicate to the
  maintainers why we should accept this pull request. If it fixes a bug
  or resolves a feature request, be sure to link to that issue in the
  additional information section.
-->


Add the SpaceXAI generate_video action for a prompt and optional reference image, plus publish_media for a time-limited link to local media. Both actions require an administrator.

Generated videos are downloaded from allowed provider hosts with redirects disabled and bounded reads, then stored in Home Assistant media. Tests cover input validation, moderation, translated provider failures, signed URLs, and media download restrictions. The video protocol is implemented by spacexai-subscription-client 0.5.0.

Token-refresh timeouts return a translated HA error before provider calls or local media creation.

## Type of change
<!--
  What type of change does your PR introduce to Home Assistant?
  NOTE: Please, check only 1! box!
  If your PR requires multiple boxes to be checked, you'll most likely need to
  split it into multiple PRs. This makes things easier and faster to code review.
-->

- [ ] Dependency upgrade
- [ ] Bugfix (non-breaking change which fixes an issue)
- [ ] New integration (thank you!)
- [x] New feature (which adds functionality to an existing integration)
- [ ] Deprecation (breaking change to happen in the future)
- [ ] Breaking change (fix/feature causing existing functionality to break)
- [ ] Code quality improvements to existing code or addition of tests

## Additional information
<!--
  Details are important, and help maintainers processing your PR.
  Please be sure to fill out additional details, if applicable.
-->

- This PR fixes or closes issue: Not applicable; this adds spacexai video and media actions.
- This PR is related to issue: No separate issue recorded.
- Link to documentation pull request: Not opened; [prepared incremental documentation](https://github.com/jeffglousher/home-assistant.io/compare/codex/spacexai/staged-docs-04-speech...codex/spacexai/staged-docs-05-video).
- Link to developer documentation pull request: Not applicable.
- Link to frontend pull request: Not applicable.

- Prepared Core diff: https://github.com/jeffglousher/core/compare/a7a0e4b5f6fbad3cc36bec34d4199bb766614735...22180c78bea231061810d1427a4a3acd36014dde
- Prepared Core commit: https://github.com/jeffglousher/core/commit/22180c78bea231061810d1427a4a3acd36014dde
- Prerequisite: Submit against Home Assistant `dev` only after Core layer 08 merges. The preceding dependency-only layer owns the package version bump; this feature diff does not bundle it. No new upstream PR has been opened.
- Client source comparison (the version bump is a separate Core layer): https://github.com/jeffglousher/spacexai-subscription-client/compare/b6b1d7d301b66bd29e24d2c0c309fa3e775f9881...f58ec77aebff01fe6bf4b72e97a2370b023647a2
- Dependency changelog: https://github.com/jeffglousher/spacexai-subscription-client/blob/f58ec77aebff01fe6bf4b72e97a2370b023647a2/CHANGELOG.md
- Dependency release: Version 0.5.0 is not published. Add verified release/PyPI links and installation evidence before submission.
- Validation: [Native Linux run](https://github.com/jeffglousher/core/actions/runs/34175314769) tests Core `22180c78bea231061810d1427a4a3acd36014dde` with client `f58ec77aebff01fe6bf4b72e97a2370b023647a2`: 144 tests, 99.3827% statement coverage, every integration module above 95%, and zero failures/errors/skips. Native lint, formatting, typing, and dependency regeneration pass; tracked generated files are unchanged. Human review, dependency publication, and refreshing/retesting against current upstream remain required.

- Quality gate: The current `has-entity-name: todo` remains unresolved, so clean quality-scale validation is not established. Address it at the speech wave using existing accepted TTS precedent and, only if necessary, a separate minimal HA naming fix. It does not enlarge or block the initial conversation contribution.

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
- [ ] There is no commented out code in this PR.
- [ ] I have followed the [development checklist][dev-checklist]
- [ ] I have followed the [perfect PR recommendations][perfect-pr]
- [ ] The code has been formatted using Ruff (`ruff format homeassistant tests`)
- [x] Tests have been added to verify that the new code works.
- [ ] Any generated code has been carefully reviewed for correctness and compliance with project standards.

If user exposed functionality or configuration variables are added/changed:

- [ ] Documentation added/updated for [www.home-assistant.io][docs-repository]

If the code communicates with devices, web services, or third-party tools:

- [ ] The [manifest file][manifest-docs] has all fields filled out correctly.  
      Updated and included derived files by running: `python3 -m script.hassfest`.
- [ ] New or updated dependencies have been added to `requirements_all.txt`.  
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
