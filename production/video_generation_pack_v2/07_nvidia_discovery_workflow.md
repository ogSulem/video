# NVIDIA discovery workflow — how to add the secret and run it manually

Workflow: `.github/workflows/nvidia-video-discovery.yml`
Scope: **discovery only.** Authenticated `GET` requests against the model catalog and
the official documentation. No generation request, no video, no commit.

---

## 0. Rotate the key first

A key pasted into a chat must be treated as burned, including the second one sent
"just in case" — being pasted is what exposes it. Revoke both at
<https://build.nvidia.com> → your account → API keys, then create one fresh key and
put it **only** into the GitHub secret below. Never in the repo, never in chat, never
in a command line that ends up in shell history.

## 1. Add the secret

Interactive — the value is read from a prompt and stored, never echoed, never in history:

```bash
gh secret set NVIDIA_API_KEY --repo ogSulem/video
# paste the new key at the prompt, Enter
```

Verify it exists without revealing it:

```bash
gh secret list --repo ogSulem/video
```

You should see `NVIDIA_API_KEY` with an updated timestamp. If your token cannot list
secrets (the agent's GitHub App token gets HTTP 403 here), do it in the UI instead:
**Settings → Secrets and variables → Actions → New repository secret**, name
exactly `NVIDIA_API_KEY`.

> Environment secrets also work, but the workflow targets a repository secret —
> keep it there unless you deliberately gate it behind an environment.

## 2. Run the discovery step

```bash
# make sure the workflow file is on the branch you run from
gh workflow run nvidia-video-discovery.yml \
  --repo ogSulem/video \
  --ref arena/f2f34461-video

# watch it
gh run list --repo ogSulem/video --workflow nvidia-video-discovery.yml --limit 3
gh run watch --repo ogSulem/video
```

Optional inputs:

| Input | Effect |
|---|---|
| `fetch_docs` (default true) | also fetch the official NVIDIA docs pages and quote documented capabilities |
| `probe_model_id` | run one extra `GET /v1/models/{id}` for an exact id, e.g. `wan-ai/wan2.2` |

```bash
gh workflow run nvidia-video-discovery.yml --repo ogSulem/video \
  --ref arena/f2f34461-video -f probe_model_id=wan-ai/wan2.2
```

## 3. Read the result

- The **job summary** of the run contains: catalog size, candidate video model ids,
  the full id list, optional single-model record, and quoted documentation snippets.
- The artifact **`nvidia-discovery-report`** (7-day retention) contains the same data
  as files: `models.json`, `model.json`, `docs-quotes.md`.

```bash
gh run download --repo ogSulem/video --name nvidia-discovery-report
```

## 4. What the workflow proves, and what it does not

Proves, per run:

- whether `NVIDIA_API_KEY` is configured (length + first 5 + last 4 characters only);
- which model ids this key can actually see, from `GET https://integrate.api.nvidia.com/v1/models`;
- optionally the raw record for one specific model id;
- what the official docs say about the video models, quoted with source URLs.

Does **not** prove (by design, and it says so in the summary):

- pricing or billing — shown on the model page and in account entitlements, not in `/v1/models`;
- quota or rate limits — same;
- authoritative max duration / resolution for the hosted variant;
- that this account is entitled to call the video model — the catalog listing only
  shows what exists for the key.

Only after this run, and only with your explicit approval, would a generation request
be made. That is a separate workflow and it does not exist yet.

## 5. Security model of the workflow

| Risk | Mitigation |
|---|---|
| key in logs | secret passed only via `env:`; `::add-mask::` registered; every response body piped through a redactor that replaces the exact key, any `nvapi-…` token, and `Authorization: Bearer …` |
| key in artifacts | only redacted JSON is uploaded; artifacts expire in 7 days |
| key in git | the workflow never runs `git add`, `git commit` or `git push`, has `permissions: contents: read`, and checks out with `persist-credentials: false` |
| accidental generation | a guard step greps the workflow for request-submitting patterns and fails the job if any is present; all HTTP is explicit `-X GET` |
| accidental run | `workflow_dispatch` only — no push, PR or schedule trigger |
| prompt-injection style surprises | no untrusted content is executed; response bodies are parsed as data, and only fixed keys are printed |
| sudden repo change | a tripwire fails the job if `git status --porcelain` is non-empty |

The redactor's self-test uses a synthetic `nvapi-TEST…` token, never the real secret,
and the job aborts if redaction fails.

## 6. Official facts already confirmed by reading the docs (no key needed)

These come from NVIDIA's own documentation, not from a live call:

- Video generation is served by **NIM for Visual Generative AI**, OpenAI-compatible
  route: `POST /v1/videos/generations`; model catalogue at `GET /v1/models` and
  `GET /v1/models/{model_id}`. ([Wan2.2 API reference](https://docs.nvidia.com/nim/visual-genai/latest/api/wan2.2.html))
- Documented video model: **Wan2.2**, canonical id `wan-ai/wan2.2` (the API reference
  header reads `wan-ai/wan2.2-14b`), with **t2v** and **i2v** variants selected
  server-side by `NIM_MODEL_VARIANT`. ([Video Generation API](https://docs.nvidia.com/nim/visual-genai/latest/api/openai-video-generation.html))
- Inputs: text prompt required; i2v takes an input image. The getting-started example
  posts `{"model": "wan-ai/wan2.2", "prompt": …, "size": "832x480", "seconds": 4}` and
  reads back a base64 MP4 from `.data.b64_json`. ([Getting started](https://docs.nvidia.com/nim/visual-genai/latest/getting-started.html))
- Documented output: "short MP4 clips at 832×480". ([Overview](https://docs.nvidia.com/nim/visual-genai/latest/overview.html))
- A separate model, `wan2.2-animate-2-14b`, does character animation **from a driving
  video** — it is not a still-to-video tool for our use.

**Not documented on those pages and therefore still unknown:** the hosted account's
maximum clip length, maximum resolution, and price/quota.

## 7. What this means for the four clips (planning note, no action yet)

If the hosted variant matches the documented 832×480 / ~4 s shape:

- **Resolution**: 832×480 is below our 1920×1080 delivery, so clips would need
  upscaling (softens detail) or a higher-resolution model must be found;
- **Duration**: a 4 s ceiling cannot cover the 11 s and 10 s windows in
  `05_vo_mapping.md` — each window would need 2–3 generations, or the windows shrink.

Do not re-plan the edit until the discovery run reports the real numbers.

## 8. One known stale helper

`video/nvidia_i2v.py` (from the earlier pack) contains *guessed* request shapes,
including a `{BASE}/video/{model}` path that is not the documented route. It is
harmless as long as it is not run, but it should be corrected to the confirmed
endpoint and the v2 prompts before any generation. Say the word and I will rewrite it
against the discovery output — I have not touched it, to keep this change purely
additive.
