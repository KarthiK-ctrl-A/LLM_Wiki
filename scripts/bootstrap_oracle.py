"""Provision a dedicated local development account without embedding credentials.

Run explicitly with Docker access. Never changes an existing account or password.
"""

import argparse
import re
import secrets
import subprocess
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--container", default="oracle26ai")
    parser.add_argument("--pdb", default="FREEPDB1")
    parser.add_argument("--user", default="WIKI_APP")
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    args = parser.parse_args()
    for identifier in (args.pdb, args.user):
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{0,29}", identifier):
            raise ValueError(
                "Oracle identifiers must be uppercase letters, digits, and underscores"
            )
    if args.env_file.exists():
        raise FileExistsError(
            "Environment file already exists; use existing credentials for smoke oracle"
        )
    password = "Wiki_" + secrets.token_hex(20)
    sql = f"""whenever sqlerror exit failure rollback
set echo off verify off feedback off
alter session set container={args.pdb};
create user {args.user} identified by "{password}";
grant create session, create table to {args.user};
alter user {args.user} quota 100M on users;
exit
"""
    result = subprocess.run(
        ["docker", "exec", "-i", args.container, "sqlplus", "-s", "/", "as", "sysdba"],
        input=sql,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )
    if result.returncode:
        # Never include SQL/password in diagnostics.
        raise RuntimeError(
            "Oracle bootstrap failed; no environment file written. Check the PDB/account."
        )
    template = Path(".env.example").read_text(encoding="utf-8")
    template = template.replace("ORACLE_USER=WIKI_APP", f"ORACLE_USER={args.user}")
    template = template.replace("ORACLE_PASSWORD=", f"ORACLE_PASSWORD={password}")
    template = template.replace("localhost:1521/FREEPDB1", f"localhost:1521/{args.pdb}")
    with args.env_file.open("x", encoding="utf-8") as stream:
        stream.write(template)
    print(
        "Dedicated Oracle user created; credentials saved only in the ignored .env file."
    )


if __name__ == "__main__":
    main()
