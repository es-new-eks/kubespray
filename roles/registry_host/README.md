# registry_host

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
