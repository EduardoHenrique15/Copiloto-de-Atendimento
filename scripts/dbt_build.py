"""Roda o `dbt build` a partir da raiz do repositório.

Garante que a pasta de saída existe e aponta o dbt para a pasta de dados certa.
Uso (PowerShell ou bash):

    python scripts/dbt_build.py
    python scripts/dbt_build.py --data-dir tests/data/olist \
        --vars "{expected_empty_comment_rate: 0.286}"
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DBT_DIR = ROOT / "dbt"


def build(data_dir: Path, extra_vars: str | None = None, target_path: Path | None = None) -> int:
    """Executa `dbt build` e devolve o código de saída."""
    raw_dir = data_dir / "raw"
    if not raw_dir.is_dir():
        print(f"Pasta de dados brutos não encontrada: {raw_dir}", file=sys.stderr)
        return 2
    (data_dir / "processed").mkdir(parents=True, exist_ok=True)

    dbt = shutil.which("dbt")
    if dbt is None:
        print("Comando dbt não encontrado. Ative o ambiente virtual.", file=sys.stderr)
        return 2

    cmd = [dbt, "build", "--project-dir", str(DBT_DIR), "--profiles-dir", str(DBT_DIR)]
    if extra_vars:
        cmd += ["--vars", extra_vars]
    if target_path:
        cmd += ["--target-path", str(target_path)]
    env = {**os.environ, "DATA_DIR": data_dir.as_posix()}
    return subprocess.run(cmd, env=env, check=False).returncode


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", type=Path, default=Path(os.getenv("DATA_DIR", "data")))
    parser.add_argument("--vars", default=None, help="vars do dbt em YAML")
    args = parser.parse_args()
    sys.exit(build(args.data_dir.resolve(), args.vars))


if __name__ == "__main__":
    main()
