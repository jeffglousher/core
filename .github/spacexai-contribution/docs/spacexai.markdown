---
title: SpaceXAI
description: Instructions on how to integrate SpaceXAI (Grok) with Home Assistant.
ha_category:
  - AI Task
  - Conversation
  - Text-to-speech
  - Speech-to-text
ha_iot_class: Cloud Polling
ha_release: "TBD"
ha_config_flow: true
ha_codeowners:
  - "@jeffglousher"
ha_domain: spacexai
ha_integration_type: service
ha_platforms:
  - ai_task
  - conversation
  - stt
  - tts
ha_quality_scale: bronze
---

The **SpaceXAI** {% term integration %} lets Home Assistant use Grok for conversation,
AI tasks, image generation, speech-to-text, and text-to-speech.

You sign in with your SpaceXAI account. The integration does not accept API keys, and
Home Assistant never sees your password — only the OAuth tokens returned by SpaceXAI.

## Prerequisites

- A SpaceXAI account with a subscription that includes API access.
- [Application Credentials](/integrations/application_credentials/) for SpaceXAI. Add the
  SpaceXAI OAuth client ID under
  **{% my application_credentials title="Settings > Devices & services > Application credentials" %}**.

{% include integrations/config_flow.md %}

During setup you choose how to sign in:

- **Sign in with device code** (recommended). Home Assistant shows a short code and a
  verification link. Open the link on any device, sign in, and approve the request. Home
  Assistant finishes on its own, and nothing needs to reach your Home Assistant URL.
- **Sign in with browser redirect**. Uses Authorization Code with PKCE through
  [My Home Assistant](/integrations/my/). Choose this if you prefer a single-browser flow.

Setup creates a conversation agent and an AI Task entity. During install you can also
opt in to speech-to-text and text-to-speech entities, or add them later from the
integration's subentry flows. Each entity is configured independently.

## Configuration options

### Conversation agent

{% configuration_basic %}
Model:
description: The Grok model used for this agent. The list is discovered from your subscription.
Control Home Assistant:
description: Which Home Assistant LLM APIs the agent may use. Only entities you have exposed are available.
Instructions:
description: The system prompt that defines how the agent should respond. Supports templates.
Enable web search:
description: Allow Grok to search the web on SpaceXAI's servers before answering. Off by default. Optional domain allow/deny lists and image understanding/search flags are available.
Enable X search:
description: Allow Grok to search public posts on X before answering. Off by default. Optional handle filters and image/video understanding flags are available.
Enable code interpreter:
description: Allow Grok to run Python on SpaceXAI's servers to calculate and analyze data. Off by default.
Enable image generation:
description: Allow Grok to create or edit images in the conversation with the server-side image generation tool. Off by default.
Allow Assist control with provider tools:
description: Required opt-in before combining Home Assistant control APIs with outbound provider tools (web/X search, code interpreter, or image generation). Off by default.
Processing speed:
description: Standard or Priority (fast). Priority maps to SpaceXAI `service_tier=priority` and is the Assist default. Keep selectable either way.
Maximum response tokens:
description: Ceiling for one response (default 3000). Short Assist answers stay short.
Temperature / Top P:
description: Sampling controls (defaults 1.0 / 1.0, matching the SpaceXAI API).
{% endconfiguration_basic %}

### AI Task

{% configuration_basic %}
Model:
description: The Grok model used for generating data.
Image model:
description: The Grok Imagine model used for generating images.
Image aspect ratio:
description: Aspect ratio for Imagine image generation (for example `1:1` or `16:9`).
Image resolution:
description: Imagine output resolution (`1k` or `2k`).
Processing speed:
description: Defaults to Standard for longer structured tasks; Priority remains selectable.
Maximum response tokens:
description: Ceiling for one task response (default 8192).
{% endconfiguration_basic %}

### Text-to-speech

{% configuration_basic %}
Voice:
description: The default voice used for spoken responses.
Speed:
description: The speaking rate, between 0.7 and 1.5.
{% endconfiguration_basic %}

## Supported functionality

### Conversation

Use the conversation agent as an [Assist](/voice_control/) pipeline agent, or talk to it
from the Assist dialog. The agent can control Home Assistant when you enable a Home
Assistant LLM API and expose entities to it. Prompts can include image and PDF
attachments.

### AI Task

The AI Task entity supports
[generating data](/integrations/ai_task/#action-ai_taskgenerate_data), including
structured output, and
[generating images](/integrations/ai_task/#action-ai_taskgenerate_image).

### Speech-to-text and text-to-speech

Recommended setup creates STT and TTS entities and can wire them into a preferred Grok
Assist pipeline. Change engines any time under
**{% my voice_assistants title="Settings → Voice assistants" %}**. If a speech or Imagine
media call is denied for the current session, a repair issue explains the failure while
the entities remain selectable.

### Generate video

Administrators can call `spacexai.generate_video` to start an Imagine video job and
receive the completed provider URL. Optional fields include model, a source image URL,
and duration (seconds).

## Data updates

SpaceXAI is queried only when you ask it something. There is no polling and no background
update interval.

## Examples

Summarize the state of your home from an automation:

```yaml
actions:
  - action: ai_task.generate_data
    data:
      task_name: House summary
      entity_id: ai_task.grok_ai_task
      instructions: >-
        Summarize whether the house is secure in one short sentence.
    response_variable: summary
  - action: notify.persistent_notification
    data:
      message: "{{ summary.data }}"
```

Generate an image:

```yaml
actions:
  - action: ai_task.generate_image
    data:
      task_name: Weather art
      entity_id: ai_task.grok_ai_task
      instructions: A watercolor painting of today's weather
    response_variable: art
```

## Known limitations

- Access depends on your SpaceXAI subscription. If your plan does not include API access,
  setup completes but requests are rejected.
- Web search, X search, and code interpreter run on SpaceXAI's servers, so the content of
  those requests leaves your network.
- Conversation history is kept by Home Assistant. Requests are sent with storage disabled,
  so SpaceXAI does not retain the conversation for you.
- Language and Imagine models are discovered from your subscription when the provider
  catalog exposes them; curated Imagine IDs remain as a fallback. Animated GIF _output_
  is not offered yet. GIF _attachments_ as input are supported.
- Combining Assist control with outbound provider tools requires an explicit opt-in.
- The conversation agent is told the Home Assistant Core version and the configured Grok
  model id so it can answer version questions. Other Assist agents do not get that context
  unless their integration adds it.

## Troubleshooting

### The integration asks me to sign in again

Your refresh token was revoked or expired. Reauthenticate from
**{% my integrations title="Settings > Devices & services" %}**.

### Setup fails with a subscription or quota message

Your SpaceXAI account does not currently have API access, or you have reached a usage
limit. Check your plan and usage with SpaceXAI, then reload the integration.

### The configured model disappeared

If SpaceXAI withdraws a model, Home Assistant raises a repair issue. Reconfigure the
affected entity and pick a model that is still available.

## Removing the integration

This integration follows standard integration removal.

{% include integrations/remove_device_service.md %}

When you delete the configuration entry, Home Assistant revokes the refresh token with
SpaceXAI so the authorization no longer appears in your account.
