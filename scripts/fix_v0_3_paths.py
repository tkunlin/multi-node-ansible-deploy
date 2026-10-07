#!/usr/bin/env python3
"""Repair v0.3 role and variable loading; preserve versions and local edits."""

import argparse
import configparser
from datetime import datetime, timezone
from pathlib import Path
import re
import shutil


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    args = parser.parse_args()
    root = args.project_dir.resolve()
    required = (
        "ansible.cfg",
        "inventory/hosts.ini",
        "roles/kernel_baseline/tasks/main.yml",
        "group_vars/all/cluster.yml",
    )
    for relative in required:
        if not (root / relative).is_file():
            parser.error(f"Project file is missing: {root / relative}")

    changes = {}
    cfg_path = root / "ansible.cfg"
    cfg_text = cfg_path.read_text(encoding="utf-8")
    cfg_parser = configparser.ConfigParser(interpolation=None)
    cfg_parser.read_string(cfg_text)
    if not cfg_parser.has_section("defaults"):
        parser.error("ansible.cfg has no [defaults] section")

    section = re.search(r"(?ms)(^\[defaults\][ \t]*\n)(.*?)(?=^\[|\Z)", cfg_text)
    if not section:
        parser.error("Cannot locate the [defaults] section safely")
    options = section.group(2)
    role_option = r"(?m)^[ \t]*roles_path[ \t]*=[^\n]*$"
    if re.search(role_option, options):
        options = re.sub(role_option, "roles_path = ./roles", options)
    else:
        options = "roles_path = ./roles\n" + options
    fixed_cfg = cfg_text[:section.start(2)] + options + cfg_text[section.end(2):]
    cfg_parser.read_string(fixed_cfg)
    if fixed_cfg != cfg_text:
        changes[cfg_path] = fixed_cfg

    play_count = 0
    for path in sorted((root / "playbooks").glob("*.yml")):
        original = path.read_text(encoding="utf-8")
        if not re.search(r"(?m)^  hosts:", original):
            continue  # Import-only wrappers inherit the updated child plays.
        play_count += 1
        if "../group_vars/all/cluster.yml" in original:
            continue
        if re.search(r"(?m)^  vars_files:[ \t]*$", original):
            updated = re.sub(
                r"(?m)^  vars_files:[ \t]*$",
                "  vars_files:\n    - ../group_vars/all/cluster.yml",
                original,
                count=1,
            )
        else:
            if not re.search(r"(?m)^  roles:[ \t]*$", original):
                parser.error(f"Cannot safely insert vars_files in {path}")
            updated = re.sub(
                r"(?m)^  roles:[ \t]*$",
                "  vars_files:\n    - ../group_vars/all/cluster.yml\n  roles:",
                original,
                count=1,
            )
        changes[path] = updated

    if not play_count:
        parser.error("No supported playbooks were found")
    if not changes:
        print("No changes needed: role and variable paths are already repaired.")
        return

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup = root / "path-fix-backups" / stamp
    for path in changes:
        destination = backup / path.relative_to(root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
    for path, text in changes.items():
        path.write_text(text, encoding="utf-8")
        print(f"Updated: {path.relative_to(root)}")
    print(f"Backup: {backup}")
    print("Target versions are preserved. No remote operations were performed.")
    print("Set ANSIBLE_CONFIG to this project's ansible.cfg before validation.")


if __name__ == "__main__":
    main()
