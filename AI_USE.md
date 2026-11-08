# AI use

- **Claude Code (Anthropic)** wrote the code, tests, manifests and documents in this repository under my direction on 2026-11-08, in about 30 minutes.
- **How it was checked:** I ran `pytest` (14 tests) and `pyflakes` locally; outputs are in `results/`. Claude found and fixed one wrong expectation
  in its own packet file (A8) when a test failed. Nothing else was independently reviewed line by line by me yet.
- **Not done by AI or me:** no teacher labelling, no training, no cluster, no load test. No results for those exist.
- No code or results were copied from another student's repository.
- The handwritten reflection will be written by me personally.
- The study guide, README and report methodology sections (2026-11-08, late) were also written by Claude Code. The structure of another student's public repository (ABHISHEK27Y/CS3081-CLOUD-PROJECT) was consulted earlier only to see what documentation depth is expected; none of its code, text, numbers or results were copied. Result cells without a measurement are marked PLACEHOLDER.
- On branch mock/nanoparse-style (2026-11-09) Claude Code wrote original worker, training, tooling, cluster and script files laid out like a public reference project (rahul-singh92/NanoParse). Only its README headings and directory layout were used as a guide; no code, text or results were copied. These files have not been run.
- 2026-11-09: Claude Code audited the repository, corrected README/report/docs to match what exists, copied the reflection scan to its required filename (byte-identical), wrote docs/SETUP.md and docs/RELEASE_METADATA.md, and built the submission ZIP from a staging copy with path rewrites (scripts/build_submission.py), verifying tests in the staged layout. The model archives in the GitHub Release are externally sourced reference artifacts (rahul-singh92/NanoParse v1.0, Rahul Singh Jadoun), not my training output. The handwritten reflection was supplied by me; Claude Code did not edit it (it only made a byte-identical copy under the required filename).
