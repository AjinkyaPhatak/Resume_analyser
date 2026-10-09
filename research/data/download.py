"""Download public datasets into research/data/raw/ (gitignored).

    python -m research.data.download skillspan
    python -m research.data.download biasbios

Each dataset is pinned to a specific HF revision (commit sha) in configs/data.yaml so
the files are byte-identical across machines.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from research.common.config import load_config, repo_path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def download_hf_files(repo_id: str, revision: str, files: list[str], out_dir: Path) -> dict:
    from huggingface_hub import hf_hub_download

    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {"repo_id": repo_id, "revision": revision, "files": {}}
    for name in files:
        local = hf_hub_download(
            repo_id=repo_id,
            filename=name,
            repo_type="dataset",
            revision=revision,
            local_dir=out_dir,
        )
        manifest["files"][name] = sha256_file(Path(local))
    with open(out_dir / "MANIFEST.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return manifest


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("dataset", choices=["skillspan", "biasbios"])
    p.add_argument("--config", default="configs/data.yaml")
    args = p.parse_args(argv)
    cfg = load_config(args.config)
    spec = cfg["datasets"][args.dataset]
    out_dir = repo_path(spec["local_dir"])
    manifest = download_hf_files(spec["hf_id"], spec["revision"], spec["files"], out_dir)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
