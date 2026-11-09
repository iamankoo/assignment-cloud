# Release metadata

**Aniket Raj** · Roll No. 230103030 · GitHub `iamankoo`

| Item | Value |
|---|---|
| Release | "CS3081 Cloud Computing Mini Project – Aniket Raj (230103030)" (the only Release, marked Latest) |
| Assets | `230103030.zip` (source package, single root folder `230103030/`) and `230103030.zip.sha256` |

The ZIP's own SHA-256 cannot be stored inside the ZIP; it is in `230103030.zip.sha256` and on the Release page.

## Model artifacts
Model weights are maintained separately from the Git repository. Model archives and their corresponding checksums will be published in the project Release after training and evaluation.
No model has been trained yet, so no model archive or model checksum exists.

Planned steps: `make train` (v1, v2) -> `make package VERSION=v1` and `VERSION=v2` (writes `dist/<v>.tar.gz`, `.sha256`, `release_manifest.json`; refuses without trained weights) ->
`gh release upload <tag> dist/*` -> set `RELEASE_TAG` / `RELEASE_ASSET` in `.github/workflows/ci.yml` -> run the `evaluate` and `quality-gate` jobs.
