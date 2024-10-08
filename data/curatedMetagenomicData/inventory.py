#!/usr/bin/env python3

import pandas as pd
from pathlib import Path
import json
from os.path import getctime

repo = "https://github.com/CirroBioApps/mudata-examples/raw/main/data/curatedMetagenomicData"


def describe(config: dict, ix: int, basename: str) -> dict:

    df = pd.read_csv(
        basename + ".relative_abundance.tsv",
        sep="\t",
        index_col=0
    )

    return {
        "Dataset Name": config["dataset_name"],
        "Total Samples": n_samples(config, df),
        "Comparison By": metadata(config, df),
        "n": df.shape[0],
        **find_file(basename, ix)
    }


def _find_file(folder: str, prefix: str, ix: int, suffix: str) -> str:
    files = list(Path(folder).rglob(f"{prefix}-{ix}*{suffix}"))
    if len(files) == 0:
        return
    assert len(files) > 0, f"No files found for {prefix}-{ix}"
    # Use the newest file
    latest_file = max(files, key=getctime)
    rel_path = Path(latest_file)
    return f"{repo}/{rel_path}"

def find_file(basename: str, ix: int) -> str:
    folder, prefix = basename.rsplit("/", 1)
    path = _find_file(folder, prefix, ix, "h5mu")
    # Also get the thumbnail
    png = _find_file(folder, prefix, ix, "png")

    return dict(path=path, png=png)


def n_samples(config: dict, df: pd.DataFrame) -> str:
    ntot = df.shape[0]
    if 'query' in config:
        nfilt = df.query(config['query']).shape[0]
        return f"{nfilt:,} of {ntot:,} samples where {config['query']}"
    else:
        return f"{ntot:,} samples"


def metadata(config: dict, df: pd.DataFrame) -> str:
    assert config["compare_by"] in df.columns, \
        f"Column {config['compare_by']} not found in {df.columns}"
    vals = df[config["compare_by"]].dropna()

    if config.get('is_categorical'):
        vc = vals.value_counts()

        if vc.shape[0] > 5:
            n_other = vc.iloc[5:].sum()
            vc = vc.iloc[:5]
            vc["Other"] = n_other

        counts = ", ".join(
            [f"{k}: {v:,}" for k, v in vc.items()]
        )
        return f"{config['label']} - {counts}"
    else:
        return config['label']


def run():
    inventory = (
        pd.DataFrame([
            describe(config, ix, str(config_file).replace(".config.json", ""))
            for config_file in Path("data").rglob("*.config.json")
            for ix, config in enumerate(json.load(config_file.open()))
        ])
        .sort_values(by="n", ascending=False)
        .drop(columns=["n"])
    )

    # Write out as markdown
    inventory.to_json("../../hugo/data/galleries/microbiome_report.json", orient="records", indent=4)


if __name__ == "__main__":
    run()
