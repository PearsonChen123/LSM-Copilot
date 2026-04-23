# Evidence Pack (template)

Use this template as the **return payload** of `ai4s-web-search`. Fill `results` with up to `k` items. Keep prose minimal — callers parse the JSON block.

```json
{
  "purpose": "",
  "goal": "",
  "queries": [],
  "results": [
    {
      "title": "",
      "url": "",
      "source_type": "paper|docs|repo|blog|other",
      "year": null,
      "license": "unknown",
      "why_relevant": "",
      "caveats": ""
    }
  ],
  "assumed_fields": [],
  "confidence": "low|medium|high",
  "notes": ""
}
```

## Optional human-readable summary

- **Top pick**: <title> — <1-sentence justification>
- **Runner-up**: <title> — <1-sentence justification>
- **Skipped**: <reason, e.g. paywalled, outdated, off-topic>

Attach the summary **after** the JSON block so machine consumers can strip it if not needed.
