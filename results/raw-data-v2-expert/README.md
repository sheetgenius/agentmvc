# Expert-guided raw runtime data

The [TypeScript](../one-shot-v2-typescript-expert/README.md) and [Phoenix](../one-shot-v2-phoenix-expert/pilot-1/README.md) expert diagnostics each produced two production HTTP benchmark rounds and 36 losslessly compressed k6 point streams. Their small metrics, WebSocket measurements, source, and scrubbed transcripts are in Git. The larger raw streams are in two assets on the [`raw-data-v2-expert` release](https://github.com/sheetgenius/agentmvc/releases/tag/raw-data-v2-expert). This release is separate from [`raw-data-v1`](../raw-data/README.md) and does not alter the earlier measurements.

| Asset | Experiment | Raw HTTP streams |
| --- | --- | ---: |
| `agentmvc-v2-typescript-expert-runtime.tar.zst` | AdonisJS / TypeScript | 36 |
| `agentmvc-v2-phoenix-expert-runtime.tar.zst` | Phoenix / Elixir | 36 |

[archives.json](archives.json) records each asset's size and SHA-256. The [TypeScript raw-data manifest](../one-shot-v2-typescript-expert/expert-1/raw-data.json) and [Phoenix raw-stream manifest](../one-shot-v2-phoenix-expert/pilot-1/runtime/raw-manifest.json) record the run provenance and per-stream checksums. Before packaging, every compressed stream was verified and its decompressed contents scanned for common credential and host-path patterns.

From a clone with the [GitHub CLI](https://cli.github.com/), restore either or both assets to the paths used by the measurement scripts:

```bash
mkdir -p .work/raw-download
gh release download raw-data-v2-expert -R sheetgenius/agentmvc -D .work/raw-download
shasum -a 256 .work/raw-download/agentmvc-v2-*-runtime.tar.zst
zstd -dc .work/raw-download/agentmvc-v2-typescript-expert-runtime.tar.zst | tar -xf - -C .
zstd -dc .work/raw-download/agentmvc-v2-phoenix-expert-runtime.tar.zst | tar -xf - -C results
```

Compare each printed checksum with `archives.json` before extracting. The TypeScript archive contains paths beginning with `results/`; the Phoenix archive contains paths beginning with `one-shot-v2-phoenix-expert/`, so its extraction target is `results/`. The release and repository remain private until the owner changes visibility.
