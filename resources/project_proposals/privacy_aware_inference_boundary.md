# Privacy Aware Inference Boundary

## Status

Proposal

This document describes a possible lab project. It is not an active experiment and does not yet have an implementation commitment.

## Project idea

Build a local privacy gateway that sits between a user and any remote model or tool.

The gateway detects sensitive information, replaces it with typed session scoped placeholders, sends only the sanitized content outside the device, and restores approved values locally when the result is shown to the user.

The central principle is:

> Compute may cross the boundary. Sensitive identity and private state should not.

## Why this is a project

This idea is broader than a single experiment because it requires a reusable system boundary with several cooperating capabilities:

1. Sensitive information detection
2. Policy based transformation
3. Local placeholder storage
4. Remote model mediation
5. Response validation
6. Controlled restoration
7. Memory and tool boundary enforcement
8. Auditing and privacy evaluation

Individual experiments can later test each capability, but the privacy boundary itself is a product and systems project.

## Intended experience

A user can continue a normal chat session while the gateway keeps private values on the local machine.

```text
Original message
      |
      v
Local detection and policy
      |
      v
Sanitized message with typed placeholders
      |
      v
Remote model or tool
      |
      v
Sanitized response
      |
      v
Local validation and approved restoration
      |
      v
Rendered response
```

Example:

```text
Original

Send the report to raghavan@example.com and reference employee ID 483921.

Sanitized

Send the report to {{EMAIL_A7F2_01}} and reference {{EMPLOYEE_ID_A7F2_01}}.

Restored locally

Send the report to raghavan@example.com and reference employee ID 483921.
```

The mapping between placeholders and original values never leaves the local device.

## Trust boundary

The local gateway is trusted with original content.

The following components are outside the trusted boundary:

1. Frontier model APIs
2. Remote inference servers
3. Web search providers
4. Remote tools
5. Shared traces and logs
6. Cloud memory systems

Anything crossing from the trusted side to the untrusted side must pass through the same privacy policy.

## Detection strategy

The local LLM should not be the only detector.

Use a layered pipeline:

### Pass 1: Deterministic detection

Detect values with strong formats:

1. Email addresses
2. Phone numbers
3. IP addresses
4. API keys and access tokens
5. Credit card numbers
6. Social Security numbers
7. Account identifiers
8. Local file paths
9. Hostnames
10. Repository secrets

### Pass 2: Local entity recognition

Detect common semantic entities:

1. People
2. Organizations
3. Locations
4. Dates
5. Medical information
6. Financial values
7. Customer names

### Pass 3: Local LLM review

Detect context specific private information that rules and entity models cannot understand reliably:

1. Internal project codenames
2. Confidential customer situations
3. Personal relationships
4. Proprietary procedures
5. Unreleased product details
6. Indirectly expressed medical or employment information

The local LLM should return structured spans and classifications rather than rewriting the full message.

```json
{
  "sensitive_spans": [
    {
      "text": "Project Orion",
      "type": "PROJECT_CODENAME",
      "start": 31,
      "end": 44,
      "action": "placeholder",
      "confidence": 0.96
    }
  ]
}
```

## Transformation modes

Different information requires different treatment.

### Typed placeholders

Use when the remote model does not need the original value.

```text
John Smith      -> {{PERSON_A7F2_01}}
10.20.30.40     -> {{IP_ADDRESS_A7F2_01}}
secret project  -> {{PROJECT_A7F2_01}}
```

### Type preserving surrogates

Use when realistic structure helps the remote model complete the task.

```text
John Smith          -> David Miller
Tampa               -> Orlando
user@company.com    -> user@example.test
```

The local vault stores the reversible mapping.

### Semantic generalization

Use when the exact value is private but its meaning affects the answer.

```text
$187,450            -> high six figure salary
42 years old        -> early forties
8026 Clementine Ln  -> residential address in Tampa
```

### Permanent removal

Use when the information is unnecessary and should not be restored.

## Placeholder design

Placeholders should be:

1. Typed
2. Unique within the session
3. Difficult to guess
4. Stable across related turns when policy permits
5. Stored only inside the local vault
6. Deleted when the session expires

Example:

```text
{{PERSON_A7F2_01}}
{{EMAIL_A7F2_01}}
{{PROJECT_A7F2_01}}
```

The random session component reduces accidental collisions between conversations.

## Local vault

The vault stores placeholder mappings and policy metadata.

Possible record:

```json
{
  "placeholder": "{{EMAIL_A7F2_01}}",
  "original_value": "raghavan@example.com",
  "type": "EMAIL",
  "created_at": "2026_07_10T20:00:00",
  "allowed_destinations": ["local_display"],
  "expires_with_session": true
}
```

The first version can use an encrypted local file or an in memory session store. It should never write original content into repository fixtures, telemetry, or shared logs.

## Restoration policy

Restoration must happen at the latest possible trusted boundary.

Keep content sanitized inside:

1. Remote model exchanges
2. Remote tool calls
3. Shared memory
4. Search requests
5. Logs and traces
6. Intermediate agent reasoning

Restore only for approved local destinations such as:

1. Local screen rendering
2. A private local file
3. A local clipboard action explicitly approved by the user

Before restoration, verify that:

1. The placeholder belongs to the current session
2. The placeholder was introduced by the local gateway
3. The response did not alter its structure
4. The destination is allowed by policy
5. The restored result will not immediately cross another external boundary

Unknown or malformed placeholders must remain unresolved.

## Conversation behavior

The gateway should maintain stable placeholder identity across a chat session when the same entity reappears.

```text
Turn 1
My manager Sarah approved Project Orion.

Sanitized
My manager {{PERSON_A7F2_01}} approved {{PROJECT_A7F2_01}}.

Turn 6
Ask Sarah whether Orion can launch next week.

Sanitized
Ask {{PERSON_A7F2_01}} whether {{PROJECT_A7F2_01}} can launch next week.
```

This preserves conversational coherence without revealing the original names.

## Memory integration

The project has a direct relationship with Memory Wiki.

A future privacy aware memory design could separate:

1. Private local knowledge
2. Sanitized portable knowledge
3. Public knowledge
4. Derived summaries
5. Provenance and restoration rules

The system must prevent deleted private values from surviving inside summaries, indexes, embeddings, or cached model outputs.

## Session capsule integration

The project also relates to Session Capsule Analysis.

A future session capsule could contain separate layers:

```text
Private layer
  Original values
  Local instructions
  Placeholder mappings

Portable layer
  Sanitized transcript
  Public references
  Model independent metadata

Derived layer
  Summaries
  Retrieval indexes
  Optional runtime state
```

The private layer must remain local unless the user explicitly exports it.

## Threat model

The project should assume that a remote model or tool may:

1. Receive every sanitized prompt
2. Retain submitted content according to its own service policy
3. Attempt to infer the hidden value from context
4. Produce malformed placeholders
5. Ask the user or agent to reveal mappings
6. Echo sensitive context into later tool calls
7. Generate content that causes unintended restoration

The gateway should not assume that placeholders provide anonymity when the surrounding context uniquely identifies the hidden entity.

## Important limitations

This system cannot promise perfect privacy.

Possible failure modes include:

1. A sensitive span is missed
2. Too much information is removed and response quality collapses
3. Context reveals the hidden entity even after replacement
4. A placeholder is restored into an unsafe destination
5. Derived memory retains deleted information
6. The local LLM itself produces incorrect classifications
7. Multimodal content contains private information that text scanning misses
8. Code, logs, or structured data hide secrets in unfamiliar formats

The project must report both privacy failures and utility loss.

## Minimum viable project

### Phase 1: Local text gateway

Build a command line proxy that:

1. Accepts a chat message
2. Applies deterministic detectors
3. Replaces detected values with typed placeholders
4. Stores mappings in an in memory vault
5. Sends the sanitized prompt to a configurable model endpoint
6. Validates returned placeholders
7. Restores values for local display

### Phase 2: Contextual detection

Add local entity recognition and a compact local instruct model for context specific classifications.

### Phase 3: Session continuity

Maintain stable entity mappings across multiple turns and prevent cross session collisions.

### Phase 4: Tool mediation

Apply the same boundary to web search, remote tools, logs, and memory writes.

### Phase 5: Memory and capsule separation

Test private and portable layers with Memory Wiki and session capsule artifacts.

## Suggested project structure

```text
privacy_boundary/
  README.md
  privacy_policy.yaml
  src/
    gateway.py
    detectors.py
    classifier.py
    transformer.py
    vault.py
    validator.py
    restorer.py
  fixtures/
    synthetic_conversations.jsonl
  evaluations/
    leakage_cases.jsonl
    utility_cases.jsonl
  results/
    README.md
```

All committed fixtures must be synthetic.

## Evaluation plan

The project should support experiments comparing:

1. No gateway
2. Deterministic rules only
3. Rules plus entity recognition
4. Rules plus entity recognition plus a local LLM
5. Placeholders versus surrogates versus generalization

Measure:

1. Sensitive span recall
2. Sensitive span precision
3. Complete prompt protection rate
4. Response quality
5. Placeholder preservation rate
6. Correct restoration rate
7. Unauthorized restoration rate
8. Added latency
9. Local memory usage
10. Tokens sent to the remote model

The most important privacy metric is complete prompt protection rate. A prompt containing five sensitive spans is not fully protected when only four are detected.

## Project success criteria

The project becomes useful when it can:

1. Mediate a multi turn chat session
2. Keep the local mapping outside all remote requests and logs
3. Preserve stable references across turns
4. Reject malformed or unauthorized restoration
5. Report measurable privacy leakage and utility loss
6. Apply one policy consistently across models, tools, memory, and traces

## Relationship to the lab thesis

Memory Wiki studies whether reusable knowledge can reduce repeated frontier inference.

Session Capsule Analysis studies what conversational and execution state exists and what it costs to reconstruct.

Privacy Aware Inference Boundary asks what information is permitted to move between local and frontier systems.

Together they define three reusable assets for long tail inference:

```text
Knowledge
State
Trust boundaries
```

The long term direction is an inference system where computation can move to the most appropriate model or device while private identity and sensitive state remain under local control.

## Open design questions

1. Should placeholder identity remain stable across separate sessions?
2. How should the gateway handle streaming responses?
3. Can embeddings be safely computed from sanitized text without leaking the hidden value?
4. When should a surrogate replace a placeholder?
5. How should users inspect and override detection decisions?
6. How should multimodal inputs be handled?
7. Can a local model estimate reidentification risk from surrounding context?
8. What information belongs in a portable session capsule?
9. How should the system prove that deleted mappings are no longer recoverable?
10. Which local models provide the best privacy and latency tradeoff?
