"""Validate ACP manifests and build the stable extension index."""

import argparse
import json
import shutil
import tarfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from jsonschema import Draft7Validator
from referencing import Registry, Resource

from check_archives import check_archive

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_URL = "https://raw.githubusercontent.com/yorkart/orbit-registry/registry-v1"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def build(output, offline=False):
    agent_schema = read_json(ROOT / "agent.schema.json")
    registry_schema = read_json(ROOT / "registry.schema.json")
    schemas = Registry().with_resource(
        agent_schema["$id"], Resource.from_contents(agent_schema)
    )
    format_checker = Draft7Validator.FORMAT_CHECKER
    validate_agent = Draft7Validator(
        agent_schema, format_checker=format_checker
    ).validate
    validate_registry = Draft7Validator(
        registry_schema, registry=schemas, format_checker=format_checker
    ).validate

    agents = []
    icons = {}
    for manifest in sorted(ROOT.glob("*/agent.json")):
        agent = read_json(manifest)
        validate_agent(agent)
        agent_id = agent["id"]
        if agent_id != manifest.parent.name:
            raise ValueError(f"{manifest}: agent ID must match the directory name")
        icon = manifest.with_name("icon.svg")
        if ET.parse(icon).getroot().tag != "{http://www.w3.org/2000/svg}svg":
            raise ValueError(f"{icon}: expected an SVG document")
        agent.pop("preview", None)
        if not offline:
            for platform, target in agent["distribution"].get("binary", {}).items():
                try:
                    size = check_archive(target)
                    print(
                        f"Verified {agent_id} {platform} archive ({size:,} bytes)",
                        flush=True,
                    )
                except (
                    OSError,
                    ValueError,
                    tarfile.TarError,
                    zipfile.BadZipFile,
                ) as error:
                    raise ValueError(f"{manifest} ({platform}): {error}") from error
        agent["icon"] = f"{PUBLIC_URL}/icons/{agent_id}.svg"
        agents.append(agent)
        icons[agent_id] = icon

    if not agents:
        raise ValueError("The registry must contain at least one agent")
    index = {"version": "1.0.0", "agents": agents}
    validate_registry(index)
    (output / "icons").mkdir(parents=True, exist_ok=True)
    for agent_id, icon in icons.items():
        shutil.copyfile(icon, output / "icons" / f"{agent_id}.svg")
    (output / "registry.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    parser.add_argument(
        "--offline", action="store_true", help="Build without checking remote archives"
    )
    args = parser.parse_args()
    build(args.output, args.offline)
