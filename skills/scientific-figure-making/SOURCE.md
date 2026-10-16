# Source, license, and local changes

This separately triggerable skill is vendored from:

- Repository: `ChenLiu-1996/figures4papers`
- Upstream path: `scientific-figure-making/`
- Locked revision: `3c181f85e82c6f24948fcaaf3be6696102b41d8d`
- Locked tree: <https://github.com/ChenLiu-1996/figures4papers/tree/3c181f85e82c6f24948fcaaf3be6696102b41d8d/scientific-figure-making>
- Upstream license: Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)
- Local license copy: [LICENSE](LICENSE)

The upstream `SKILL.md` and all five upstream references are present in full. This integration adds a mandatory repository-priority gate, safety notices, and narrowly scoped corrections; it does not vendor the upstream repository's plotting scripts, PNG files, PDF files, paper data, or other demo assets.

## Change indication

Relative to the locked upstream files, this vendored copy:

- adds the local precedence gate to `SKILL.md`;
- labels exact palettes and unsafe historical practices as subordinate or reference-only;
- prevents truncated magnitude bars, hidden ambiguous labels, alpha-only or red–green-only categories, and fixed ultra-wide canvases from becoming defaults;
- changes the tutorial magnitude-bar example from a truncated y-axis to a zero baseline;
- pins every `tree/main` demo link to the locked revision;
- adds local Codex UI metadata under `agents/openai.yaml`.

## Upstream normalized SHA-256

These hashes identify the unmodified locked source files before the local changes above:

| Upstream file | SHA-256 |
|---|---|
| `scientific-figure-making/SKILL.md` | `952300b4d0bd8fbd0c55aaa732a47a0abb8e9707bc80965c8e70221ef13f0292` |
| `scientific-figure-making/references/api.md` | `12892f4940c153c8b2e75abe8eed8f96476989b0a75d65f0dc3d08118bf58269` |
| `scientific-figure-making/references/common-patterns.md` | `1456736819f17c5a8bef0daaa58107355dd3212e1594afae5fb49279af2d6d67` |
| `scientific-figure-making/references/demos.md` | `23ce4b9f626af9ace648b047cbc3100ebc511b83127b8cebe793cab3a2f93fa3` |
| `scientific-figure-making/references/design-theory.md` | `d34fa995a481588a33aab301591a9a2ae54dae8df34c74e0a13311582ef48d99` |
| `scientific-figure-making/references/tutorials.md` | `e5a9b9fa78a73a981f046aa29728dd844268282109159fd934f9c9716b3592c1` |
| repository-root `LICENSE` | `0afca3145596cd005f6f6ed977313ea31928094fc5b4aaabc21bb765ea369d09` |

## License boundary

This vendored skill subtree remains CC BY-NC 4.0 and is **not relicensed** by the repository-root MIT license. Attribution, the license link, and this change indication must travel with redistributed or adapted copies. Commercial reuse requires separate permission. Possible publisher, coauthor, dataset, font, icon, or other third-party rights are not cleared by the repository license.

For commercial or unclear contexts, do not copy upstream code, prose, figures, paper data, exact visual recipes, or demo assets. Use the repository's independently written `references/figures4papers-profile.md` and implement general plotting principles from first principles.
