# Raw HTTP measurements

The benchmark summaries and socket samples are in Git beside each experiment. The losslessly compressed k6 point streams total more than a gigabyte and are ignored by Git. They remain in the local `results/` tree while release archives are prepared and reviewed. No raw-data release has been uploaded yet.

| Asset | Experiment |
| --- | --- |
| `one-shot-raw.tar` | First full-product run |
| `one-shot-semantic-density-raw.tar` | Shared semantic-density prompt |
| `one-shot-ihp-raw.tar` | Three IHP runs and guided diagnostic |
| `shine-raw.tar` | Separate build and tuning experiments |
| `one-shot-v2-servant-raw.tar` | Servant safe-evolution pilot; [checksum and file index](../one-shot-v2-servant/pilot-1/runtime/raw-archive.json) |

The Servant pilot archive is prepared at `.work/one-shot-v2-servant-raw.tar`; its 36 compressed streams have individual hashes in [raw-index.json](../one-shot-v2-servant/pilot-1/runtime/raw-index.json). The other experiments' raw streams remain locally available but are not in a clone. Their browsable summaries and repeated measurements are in Git.

After a reviewed raw-data release is uploaded, restore an archive from a clone with the [GitHub CLI](https://cli.github.com/). For example, with a future release tag:

```bash
mkdir -p .work/raw-download
gh release download TAG -R sheetgenius/agentmvc \
  -p one-shot-ihp-raw.tar -D .work/raw-download
tar -xf .work/raw-download/one-shot-ihp-raw.tar -C .
```

Check the future release's archive checksum and the per-stream index before using restored points. The repository is private until its owner changes visibility.
