"""Phase 0 sanity check: loads a config, seeds, resolves the device, and writes run
metadata, exercising the same path every real experiment uses.

    python -m research.experiments.check_env --config configs/base.yaml [--subset N]
"""

from __future__ import annotations

import json

from research.common.cli import base_parser, setup_run
from research.common.config import repo_path
from research.common.provenance import write_run_metadata
from research.common.seed import get_device


def main(argv: list[str] | None = None) -> None:
    args = base_parser(__doc__, default_config="configs/base.yaml").parse_args(argv)
    cfg = setup_run(args)
    device = get_device(cfg.get("device", "auto"))
    out_dir = repo_path(cfg["paths"]["results"]) / "check_env"
    meta_path = write_run_metadata(out_dir, cfg, extra={"resolved_device": device})
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    print(f"device:   {device}")
    print(f"seed:     {cfg['seed']}  subset: {cfg.get('subset')}")
    print(f"git:      {meta['git']}")
    print(f"packages: {meta['packages']}")
    print(f"wrote:    {meta_path}")


if __name__ == "__main__":
    main()
