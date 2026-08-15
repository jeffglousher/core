# Pull request review process

Source: https://developers.home-assistant.io/docs/review-process
Retrieved: 2026-08-15

Everybody can help reviewing PRs. Most review work is volunteer time.

## Before creating your PR

Comply with architectural decisions in the ADR folder. Open an architecture
discussion before submitting a PR that needs a new decision.

## Creating the perfect PR

1. Make your PRs as small as possible. One refactor, one fix, one feature.
2. Only change one thing at a time. Nearby cleanups belong in a separate PR.
3. Test your changes before creating a PR.
4. Ensure your PR is based on the latest version of the upstream `dev` branch.
5. Create a feature branch. Do not open PRs from `dev`.
6. Follow the PR template. Add a clear title and an extensive description
   with motivation.
7. Update a dependency in a standalone PR. Include release notes, changelog,
   or a GitHub compare view.

## Receiving review comments

Review comments are not personal. Ask for clarification when needed.

## PRs are drafted when changes are needed

Requested changes mark the PR as draft. Mark ready for review only after
every requested change is addressed and CI is green.

## Speeding up the review process

1. Draft the PR when CI failure is caused by your changes.
2. Monitor the PR and keep it up to date.
3. Add tests.
4. Revisit and tune while waiting.
5. Help review the queue.

## What not to do

* Do not contact contributors, code owners, or core team members directly
  about a PR, or ping them to ask for a review.
* Do not ask for a review in the PR description.
* Do not submit new pull requests that depend on other pull requests that
  are still open/unmerged.
* Do not open more than 5 pull requests. If you have more than 5 open PRs,
  close some until others have been merged.
* Do not open a PR if you are not going to work on it.

## Home Assistant Core pointers

* Development checklist
* Development checklist for integrations
* Submitting your work
* Style guidelines
* Testing your code
* Catching up with reality
* Tips and Tricks
