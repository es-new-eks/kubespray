# registry_host

## Revision history

| Date | Author | Change |
|---|---|---|
| 2026-11-23 | Codex | Reviewed the role against the Roller bootstrap and migration contracts. |

Pre-install container registry on the first control-plane node.

This role is intentionally separate from `kubernetes-apps/registry`:

- it runs before the `download` role and before Kubernetes exists;
- it provides the first-node image source for offline installation;
- the post-install registry addon remains a different component.

## Offline use

Ship the registry image as a tar and point the role at it:

```yaml
registry_host_enabled: true
registry_host_image: registry:2.8.1
registry_host_image_tar: /var/lib/eks-roller/registry-images.tar
registry_host_configure_mirrors: true
```

The role defaults to no public image pull.  If the image is not already
present and `registry_host_image_tar` is empty, the play fails instead of
silently reaching the network.

## Runtime selection

`registry_host_runtime` is `docker` for `container_manager=docker`, `nerdctl`
for containerd, and `podman` otherwise.  The service is a systemd unit with
`Restart=always`; data is stored in `registry_host_data_dir`.

## Test evidence

Verified locally with Ansible 2.4, Docker 26:

- offline image tar load;
- `/v2/` returns 200;
- service restart keeps the registry available;
- missing image without tar or online pull fails fast;
- role gated off by `registry_host_enabled: false`.

## Integration review (2026-11-23)

The invoking [cluster play](../../playbooks/cluster.yml) gates this role,
after the container-engine step and before download. The engine and its
offline prerequisites must already work at that point. The first node is
`groups['kube_control_plane'][0]`; the archive path is on that node.
The publishing address must be reachable from every target node. Cross-layer
delivery uses SSH on each machine's configured port (default 22). Port 5000
is for pulls within the target cluster.

| What the role does today | What the installer must establish before proceeding |
|---|---|
| Inspects a local image by name, optionally loads a tar, starts a systemd container and probes loopback HTTP. | Check architecture and digest, verify the loaded reference, then populate the **registry itself** with all indexed installation images. Loading the registry server image into Docker or nerdctl does not publish that payload. Keep online pulls disabled and test with egress blocked. |
| Publishes the configured host port and mounts a local data directory. | Verify ownership, free space, port availability and an effective source-CIDR firewall policy **before** starting the listener. The role installs no such policy. Never adopt an unrelated directory or stop an unknown listener. |
| Writes containerd configuration under the **first-node registry authority** and restarts containerd on changed files. | Require a working containerd service on each affected node and the matching CRI registry config path. Use image references for that authority; this file does not redirect arbitrary upstream registry names. For Docker/Podman hosts, explicitly decide whether containerd configuration applies. |
| Enables a fixed-name unit and requests state started. | Verify the effective container settings after a unit change; daemon-reload alone does not replace a running container. Record cluster ownership and generation before retry or handoff. Select one owner for the unit; the Roller backend also has a registry installer. |

The Docker checks above are historical component evidence. Product readiness
requires a real digest pull from another cluster node (an uncached pull from
the first node in a single-node cluster), complete index verification and a
denied connection from outside the allowed CIDRs.

The control-plane handoff is owned by Roller: exactly one writer on the
original node, port and data path. Suppress recreation of the bootstrap unit
after handoff, including on playbook reruns. A business cluster retains its
host registry. Disabling this role skips tasks; it does not uninstall the unit
or delete data. See the [joint migration proposal](https://github.com/es-new-eks/eks-roller/blob/master/docs/proposals/20261123-be-registry-deployment-migration.md).
