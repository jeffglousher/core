# SpaceXAI stack review status (fork drafts)

Contribution kit: [`.github/spacexai-contribution/`](../spacexai-contribution/) (`STACK.md`, brands assets, docs page).

Wave-specific live media is under this directory (`pr1_` … `pr6_`). Each PR embeds only its own still + GIF.
PR screenshot embeds are pinned to media commit `9127ae8c876ad701a9bed7cd8586734f06c982d6` on `cursor/spacexai-conversation-0109`.

Code notes:

- Tolerate xAI omitting `name` on `response.function_call_arguments.done` (use the announced tool name).
- Conversation system prompt includes Home Assistant Core version + configured Grok model so Assist can answer version questions.

Human / external blockers:

1. Dedicated xAI OAuth client for Home Assistant
2. Brands PR from `.github/spacexai-contribution/brands/`
3. Docs PR from `.github/spacexai-contribution/docs/spacexai.markdown` (`home-assistant.io` `next`, bronze)
4. AI-policy human understanding
5. Later stack waves 7–8 flip `quality_scale` docs/brands to `done` and optionally declare Platinum
