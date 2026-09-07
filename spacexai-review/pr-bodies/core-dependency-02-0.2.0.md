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


## Proposed change
<!--
  Describe the big picture of your changes here to communicate to the
  maintainers why we should accept this pull request. If it fixes a bug
  or resolves a feature request, be sure to link to that issue in the
  additional information section.
-->


Bump spacexai-subscription-client from 0.1.0 to 0.2.0. This updates only the SpaceXAI manifest and generated requirements. The existing feature set stays unchanged; new client capabilities are exposed in a later, separate feature contribution.

The preceding Core layer is tested against this exact newer client before submission. No compatibility adapter is added. The package versions are currently unpublished: this is fork-only preparation, not a submission-ready dependency upgrade.

## Type of change
<!--
  What type of change does your PR introduce to Home Assistant?
  NOTE: Please, check only 1! box!
  If your PR requires multiple boxes to be checked, you'll most likely need to
  split it into multiple PRs. This makes things easier and faster to code review.
-->

- [x] Dependency upgrade
- [ ] Bugfix (non-breaking change which fixes an issue)
- [ ] New integration (thank you!)
- [ ] New feature (which adds functionality to an existing integration)
- [ ] Deprecation (breaking change to happen in the future)
- [ ] Breaking change (fix/feature causing existing functionality to break)
- [ ] Code quality improvements to existing code or addition of tests

## Additional information
<!--
  Details are important, and help maintainers processing your PR.
  Please be sure to fill out additional details, if applicable.
-->

- This PR fixes or closes issue: Not applicable; dependency upgrade.
- This PR is related to issue: No separate issue.
- Link to documentation pull request: Not applicable; no user-facing feature changes.
- Link to developer documentation pull request: Not applicable.
- Link to frontend pull request: Not applicable.

- Prepared Core diff: https://github.com/jeffglousher/core/compare/1be5415320b9f511d568df7990d5f32ffb0df0df...23d3cadc96f939b3a0bb63409c31e3844aabae1c
- Prepared Core commit: https://github.com/jeffglousher/core/commit/23d3cadc96f939b3a0bb63409c31e3844aabae1c
- Package source comparison: https://github.com/jeffglousher/spacexai-subscription-client/compare/f12b460dffecff7ce4f2827fffa8351e06cadcb6...573e22c48b9e182ab27fcc0d3d4027d0e9e4a142
- Package changelog: https://github.com/jeffglousher/spacexai-subscription-client/blob/573e22c48b9e182ab27fcc0d3d4027d0e9e4a142/CHANGELOG.md
- Publication gate: Version 0.2.0 is not published. The dependency resolver returns HTTP 404 for the package. Verify actual PyPI artifacts, release tags, and immutable release comparisons before replacing these staging links.
- Submission order: Wait for the preceding Core layer to merge and the new package version to be published. Then refresh onto official dev, regenerate requirements, and rerun the preceding feature's tests with the released package. Do not open a dependent upstream PR.
- Validation: [Native Linux run](https://github.com/jeffglousher/core/actions/runs/34169519326) tests Core `23d3cadc96f939b3a0bb63409c31e3844aabae1c` with client `573e22c48b9e182ab27fcc0d3d4027d0e9e4a142`: 41 tests, 99.1701% statement coverage, every integration module above 95%, and zero failures/errors/skips. Scoped native lint, formatting, typing, and dependency regeneration pass; tracked generated files are unchanged. Human review and dependency publication remain required.

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
- [ ] Tests have been added to verify that the new code works.
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
