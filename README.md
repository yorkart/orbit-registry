# Orbit ACP extension registry

Orbit uses this independent registry alongside the official Agent Client Protocol registry.

The stable index is [registry.json](https://raw.githubusercontent.com/yorkart/orbit-registry/registry-v1/registry.json).
GitHub Actions validates manifests on pull requests and publishes the generated index
and icons together to the `registry-v1` branch after a successful build on `main`.

Each extension has its own `<id>/agent.json` and `<id>/icon.svg`. Use the ACP
registry format and keep the directory name equal to the agent's fixed ID.
Run the same validation and build locally with:

```sh
uv run --no-project --with 'jsonschema[format-nongpl]==4.26.0' scripts/build_registry.py
```

The initial TRAE CLI 0.216.0 manifest and icon come from
[ACP registry PR #793](https://github.com/agentclientprotocol/registry/pull/793/files)
at commit `65dc8fb918a6db003c26600226432bba1b7885e5`.
The two schemas come from the
[official ACP registry](https://github.com/agentclientprotocol/registry/tree/761c5a48b9862f6ff7e537a28154818c78033a36)
and retain its Apache 2.0 license. Vendor distributions remain subject to their
respective terms.
