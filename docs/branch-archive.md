# Archived development branches

On 2026-10-26, obsolete development branches were removed after consolidating
the current application in `main`. The following annotated tags preserve the
exact tips of branches that contained commits not incorporated into `main`.

| Former branch | Archive tag | Preserved commit | Context |
| --- | --- | --- | --- |
| `cyto_test` | `archive/cyto_test-2026-10-26` | `1178f7bef22d652b93711f229cdc277292a2d641` | 2022 experiments with cytoplasm detection and drawing; 12 commits outside main. |
| `juliano` | `archive/juliano-2026-10-26` | `a9c0ff1901df91fb3b0124ee034c841ae78d9f7c` | 2021 Qt interface experiments; 16 commits outside main. |
| `pyqt5-migration` | `archive/pyqt5-migration-2026-10-26` | `8de20d262f58570db6dffc770300312784c99994` | 2022 incomplete Qt migration; 3 commits outside main. |

These tags are historical references, not supported releases. No changes from
these experimental branches were merged as part of the cleanup. The current
application already has cytoplasm analysis and a web interface; revisiting an
old experiment requires checking its behavior against the current implementation.

To inspect an archive without changing `main`:

```sh
git fetch origin --tags
git show archive/cyto_test-2026-10-26
git diff main...archive/cyto_test-2026-10-26
```

The branches `build/desktop-cpu`, `feature-fastapi`, `feature-trace`,
`feature/gui-dash`, `fornma_final` and `interface` were already fully incorporated
into `main`. Their commits remain reachable through its history. Desktop builds
now target `main`. Existing releases and their assets are preserved.
