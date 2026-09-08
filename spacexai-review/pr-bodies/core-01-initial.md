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

I'm adding a community-maintained SpaceXAI integration so people can use Grok as an Assist agent with their xAI subscription. I've kept this first contribution limited to conversation; AI Task, media, and speech are left for later.

Setup uses browser-based OAuth device authorization, validates the account and available models, and creates one conversation agent per account. Assist control is selected by default, can be disabled during setup, and respects Home Assistant's exposed entities. There is no API-key fallback or runtime CLI dependency.

The published, unofficial `spacexai-subscription-client` library handles provider communication and OAuth. The integration handles Home Assistant configuration, shared sessions, conversations, tool calls, and token persistence. It targets Bronze, not the full quality scale in this first PR.

The integration suite passes all 50 tests locally in a separate Linux environment on my HA host and in native CI, with 100% statement coverage. This includes login cancellation, shutdown, token refresh, provider failures, Assist exposure controls, and saving the default, enabled, or disabled Assist choice during setup. Formatting, typing, lint, hassfest, and generated-file checks pass too. Fresh initial-only OAuth setup and saved-account restart now pass, but live chat with the published client 0.1.0 is blocked by the provider's minimum CLI-version check (HTTP 426). This draft is not ready for submission until the library compatibility fix is reviewed, published, pinned, and retested.

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
- This PR is related to issue: Replaces my closed [PR #178765](https://github.com/home-assistant/core/pull/178765) with a smaller contribution and a separate provider library.
- Link to documentation pull request: Not created yet; [prepared documentation](https://github.com/jeffglousher/home-assistant.io/compare/codex/spacexai/review-base-release-0-1...codex/spacexai/docs-initial-release-0-1).
- Link to developer documentation pull request: Not applicable.
- Link to frontend pull request: Not applicable.
- Brands pull request: Not created yet; [prepared branding](https://github.com/jeffglousher/brands/compare/codex/spacexai/review-base...spacexai-initial).
- New dependency: [PyPI 0.1.0](https://pypi.org/project/spacexai-subscription-client/0.1.0/), [source](https://github.com/jeffglousher/spacexai-subscription-client/tree/v0.1.0), and [release notes](https://github.com/jeffglousher/spacexai-subscription-client/blob/v0.1.0/CHANGELOG.md). This is a new dependency, so there is no previous version to compare.
- Validation: 50 local Linux tests pass for Core `cd495263` with the published client, with no failures, errors, or skips. [Native CI](https://github.com/jeffglousher/core/actions/runs/34260917145) passes the same suite, formatting, typing, lint, unchanged development setup, native hooks, hassfest, and generated-file validation for that exact revision. No Windows test result is claimed.
- Live testing: Fresh authorization through external Chrome creates one loaded initial-only account and conversation agent with Assist enabled by default. Published client 0.1.0 then fails chat because the provider interprets its package-version header as an outdated CLI version. With the verified 0.1.1 candidate wheel installed as an explicit test-only dependency override, chat/history, exposed-helper control with native tool calls, an unchanged unexposed helper, saved-account restart followed by chat, and account/entity removal all pass. The unchanged Core source also passes all 50 native tests with that wheel. Only the isolated test account was removed; my main HA was untouched. The Core manifest still pins 0.1.0, so these candidate results do not make this submitted dependency ready.
- Detailed evidence and remaining gates: [first-wave review packet](https://github.com/jeffglousher/core/blob/codex/spacexai-validation/spacexai-review/FIRST_WAVE_READINESS.md).

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

- [x] I understand the code I am submitting and can explain how it works.
- [ ] The code change is tested and works locally.
- [x] Local tests pass. **Your PR cannot be merged unless tests pass**
- [x] There is no commented out code in this PR.
- [x] I have followed the [development checklist][dev-checklist]
- [ ] I have followed the [perfect PR recommendations][perfect-pr]
- [x] The code has been formatted using Ruff (`ruff format homeassistant tests`)
- [x] Tests have been added to verify that the new code works.
- [x] Any generated code has been carefully reviewed for correctness and compliance with project standards.

If user exposed functionality or configuration variables are added/changed:

- [x] Documentation added/updated for [www.home-assistant.io][docs-repository]

If the code communicates with devices, web services, or third-party tools:

- [x] The [manifest file][manifest-docs] has all fields filled out correctly.  
      Updated and included derived files by running: `python3 -m script.hassfest`.
- [x] New or updated dependencies have been added to `requirements_all.txt`.  
      Updated by running `python3 -m script.gen_requirements_all`.
- [ ] For the updated dependencies a diff between library versions and ideally a link to the changelog/release notes is added to the PR description.

The dependency-update checkbox does not apply to this new integration; the first release and its notes are linked above. Local automated tests pass, but I have cleared the works-locally checkbox because initial-only live testing found the provider rejection above. Earlier full-stack success does not establish that this initial dependency works. Review of two other PRs has not been confirmed.

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
