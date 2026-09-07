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


Add speech-to-text and text-to-speech entities for use in Home Assistant voice pipelines. Users can add speech subentries under their existing OAuth account, select a speech voice, and configure synthesis speed.

The speech entities use shared account and token handling. Tests cover speech configuration, transcription and synthesis requests, supported audio parameters, lifecycle behavior, and provider errors. This layer uses spacexai-subscription-client 0.4.0.

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

- This PR fixes or closes issue: Not applicable; this adds spacexai speech platforms.
- This PR is related to issue: No separate issue recorded.
- Link to documentation pull request: Not opened; [prepared incremental documentation](https://github.com/jeffglousher/home-assistant.io/compare/codex/spacexai/docs-03-ai-task-next...codex/spacexai/docs-04-speech-next).
- Link to developer documentation pull request: Not applicable.
- Link to frontend pull request: Not applicable.

- Prepared Core diff: https://github.com/jeffglousher/core/compare/codex/spacexai/core-03-ai-task-ready...codex/spacexai/core-04-speech-ready
- Prepared Core commit: https://github.com/jeffglousher/core/commit/9f96bf6adc9ccc6dbc23ae66b099c86f4ca1831e
- Prerequisite: Submit against Home Assistant `dev` after the preceding Core layer merges. This is a prepared description; no upstream PR has been opened.
- Dependency diff: https://github.com/jeffglousher/spacexai-subscription-client/compare/spacexai/client-03-image...spacexai/client-04-speech
- Dependency changelog: https://github.com/jeffglousher/spacexai-subscription-client/blob/spacexai/client-04-speech/CHANGELOG.md
- Dependency release: Version 0.4.0 is not published. Add verified release/PyPI links and installation evidence before submission.
- Validation: [Native Linux run](https://github.com/jeffglousher/core/actions/runs/34081052741) passed 101 tests against client commit `9133ea56b89e6b35081f2bb19826bb83088582c8`, including its complete bounded speech-stream repair, with 99.6820% aggregate coverage and every integration module above 95%. Ruff, formatting, MyPy, and Pylint passed. Human review and dependency publication remain required before submission.

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
