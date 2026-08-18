# Submit your work

Source: https://developers.home-assistant.io/docs/development_submitting
Retrieved: 2026-08-15

Always base your Pull Requests off of the current **dev** branch, not master.

1. From your fork's dev branch, create a new branch to hold your changes.
2. Make your changes.
3. Test your changes and check for style violations. Consider adding tests.
4. If everything looks good according to the development checklist, commit:
   * Write a meaningful commit message.
   * Use a capital letter to start and do not finish with a full-stop
     (period).
   * Don't prefix your commit message with `[bla.bla]` or `platform:`.
   * Write your commit message using the imperative voice
     (`Add some feature`, not `Adds some feature`).
5. Push your committed changes back to your fork on GitHub.
6. Create the pull request against `home-assistant/core` `dev`. Complete the
   provided template.
7. Check for comments and suggestions and keep an eye on CI.

If this is your first time submitting a pull request, the CI won't run until
a maintainer approves running it.
