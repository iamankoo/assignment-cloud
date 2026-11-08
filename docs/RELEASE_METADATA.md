# Release metadata

| | |
|---|---|
| Release page | https://github.com/iamankoo/Cloud-Assignment/releases/tag/reference-nanoparse-v1.0 |
| Title | Cloud-Assignment – Pythia-70M Model Artifacts |
| Tag | `reference-nanoparse-v1.0` (pre-release; published 2026-11-08 19:44 UTC by `iamankoo`) |
| Nature | **Externally sourced reference artifacts. Not trained or evaluated independently in this repository. Not the submitting student's training output.** |

## Original source and provenance
- Source: https://github.com/rahul-singh92/NanoParse, release `v1.0` (published 2026-11-01)
- Original author: Rahul Singh Jadoun (`rahul-singh92`)
- Base model: EleutherAI/Pythia-70M, fine-tuned on CPU
- `pythia-70m-v1.tar.gz`: 1,500 training records, seed 42, 3 epochs (per the original release notes)
- `pythia-70m-v2.tar.gz`: 1,500 training records, seed 123, 3 epochs (per the original release notes)
- Re-uploaded unmodified by Aniket Raj (`iamankoo`)

## Assets (as recorded by GitHub for this repository's release)
| File | Size (bytes) | SHA-256 |
|---|---:|---|
| `pythia-70m-v1.tar.gz` | 231,464,749 | `3b098817b3ab49b30b44cd2b6086b71b1ef7645542451883d54dfcfebab47bfe` |
| `pythia-70m-v2.tar.gz` | 231,431,692 | `47ce600a2c68fd4f36737ce09a1fbf719ced97cc6c9e388aa92c07af14b01117` |
| `model-v1.sha256` | 87 | `f9ec53f4f45c9a9996336cc85d114c480adf5aef4ac58b3bb40d37d39ad61c9f` |
| `model-v2.sha256` | 87 | `bc8eb603770777ef2e3103f8fdc846daf4c0c40ec84726917d1fd5bf772b93e3` |

The `.sha256` manifests list the archive hashes above; the archive digests recorded by GitHub equal the manifest values. The weights themselves are not in this ZIP or in Git.

Copies of the two manifest files are in `release_checksums/`.

## Not done
No evaluation (`score.py`), serving test or load test has been run with these artifacts in this repository.
