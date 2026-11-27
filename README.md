# Orbit ACP extension registry

Orbit uses this registry alongside the official [Agent Client Protocol registry](https://github.com/agentclientprotocol/registry).

## Usage

Orbit reads the [stable registry index](https://raw.githubusercontent.com/yorkart/orbit-registry/registry-v1/registry.json).
Each successful publication also attaches the built indexes, schemas and SVGs to a
[versioned GitHub Release](https://github.com/yorkart/orbit-registry/releases).

## Adding an agent

Each entry lives in `<id>/agent.json` with a matching `<id>/icon.svg`.
See the [registry format](FORMAT.md), [contribution guide](CONTRIBUTING.md)
and [authentication requirements](AUTHENTICATION.md).

Build and validate the registry locally:

```sh
uv run --with 'jsonschema[format-nongpl]==4.26.0' .github/workflows/build_registry.py
```

Set `SKIP_URL_VALIDATION=1` for an offline build. CI also checks authentication
and uses `--verify-archives` to validate the SHA-256 and executable of each
stable binary target. The 1 GiB archive limit matches Orbit Host.

The upstream workflows also check license URLs, detect agent updates, and
publish the nightly protocol matrix for this registry's catalog.

## Upstream and license

The schemas, registry tools, workflows and format documentation are based on the
[official ACP registry at `4273056`](https://github.com/agentclientprotocol/registry/tree/4273056f03b93f8ce41e9276256ea47b057b794c).
This registry uses the [Apache License 2.0](LICENSE).
Individual agent distributions are subject to their own terms.
