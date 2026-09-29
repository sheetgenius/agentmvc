# Raw HTTP measurements

The benchmark summaries and WebSocket samples are committed beside each experiment. The 576 losslessly compressed k6 point streams occupy 1.56 GB in six archives on the [raw-data-v1 release](https://github.com/sheetgenius/agentmvc/releases/tag/raw-data-v1); Git ignores the individual streams. Each stream was decompressed and scanned for common credential and home-path patterns before packaging. [index.json](index.json) records each stream's size and SHA-256 checksum; [archives.json](archives.json) records the archive checksums.

| Asset | Experiment | Streams |
| --- | --- | ---: |
| `one-shot-raw.tar` | First full-product run | 108 |
| `one-shot-semantic-density-raw.tar` | Shared semantic-density prompt | 108 |
| `one-shot-ihp-raw.tar` | Three IHP runs and guided diagnostic | 144 |
| `shine-raw.tar` | Separate build and tuning experiments | 144 |
| `one-shot-v2-servant-raw.tar` | Servant safe-evolution pilot | 36 |
| `one-shot-v2-typescript-raw.tar` | TypeScript safe-evolution pilot | 36 |

From a clone with the [GitHub CLI](https://cli.github.com/), restore an archive into the same paths used by the measurement scripts:

```bash
mkdir -p .work/raw-download
gh release download raw-data-v1 -R sheetgenius/agentmvc \
  -p one-shot-v2-typescript-raw.tar -D .work/raw-download
shasum -a 256 .work/raw-download/one-shot-v2-typescript-raw.tar
tar -xf .work/raw-download/one-shot-v2-typescript-raw.tar -C .
```

Compare the printed checksum with `archives.json` before extracting. The release and repository are private until the owner changes visibility.
