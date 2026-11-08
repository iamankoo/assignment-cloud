# Release metadata

| | |
|---|---|
| Release page | https://github.com/iamankoo/Cloud-Assignment/releases/tag/reference-nanoparse-v1.0 |
| Title | Cloud-Assignment – model artifact provenance (no model archives) |
| Tag | `reference-nanoparse-v1.0` (pre-release; published 2026-11-08 19:44 UTC by `iamankoo`) |
| Model archives in the Release | **None.** Removed on 2026-11-09 (see below) |
| This project's own model archives | **Not produced yet. They remain outstanding.** |

## Why the archives were removed
Two Pythia-70M archives from another project had been uploaded as reference material. Permission to redistribute them could not be established:
the source project has no licence file, and no written permission is on record in this repository. They were therefore removed from the Release.
They were never trained or evaluated in this repository and are not the submitting student's training output.

## Original source and provenance (preserved for attribution)
- Source: https://github.com/rahul-singh92/NanoParse, release `v1.0` (published 2026-11-01)
- Original author: Rahul Singh Jadoun (`rahul-singh92`)
- Base model: EleutherAI/Pythia-70M, fine-tuned on CPU
- Archive `pythia-70m-v1.tar.gz`: 1,500 training records, seed 42, 3 epochs (per the original release notes)
- Archive `pythia-70m-v2.tar.gz`: 1,500 training records, seed 123, 3 epochs (per the original release notes)

## What is still attached to the Release
| File | Size (bytes) | SHA-256 |
|---|---:|---|
| `model-v1.sha256` | 87 | `f9ec53f4f45c9a9996336cc85d114c480adf5aef4ac58b3bb40d37d39ad61c9f` |
| `model-v2.sha256` | 87 | `bc8eb603770777ef2e3103f8fdc846daf4c0c40ec84726917d1fd5bf772b93e3` |

These are the original checksum manifests (copies in `release_checksums/`). They record the hashes of the removed archives:

| Removed archive | Size (bytes) | SHA-256 recorded in the manifest |
|---|---:|---|
| `pythia-70m-v1.tar.gz` | 231,464,749 | `3b098817b3ab49b30b44cd2b6086b71b1ef7645542451883d54dfcfebab47bfe` |
| `pythia-70m-v2.tar.gz` | 231,431,692 | `47ce600a2c68fd4f36737ce09a1fbf719ced97cc6c9e388aa92c07af14b01117` |

## Outstanding for the assignment
The assignment requires the student's own trained model, tokenizer, version information and checksums as Release assets. None exist yet.
No evaluation (`score.py`), serving test or load test has been run with any model in this repository.
