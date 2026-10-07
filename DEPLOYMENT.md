# Deployment sequence

1. Verify SSH/hostnames/source-of-truth: `00-cluster-preflight.yml`.
2. Verify offline binaries: `05-artifact-preflight.yml`.
3. Apply kernel baseline: `10-kernel-baseline.yml`.
4. Render Netplan without applying: `20-network-baseline.yml`.
5. Review `/etc/netplan/60-g8825z5.yaml` and run `netplan generate` (the role already does syntax validation).
6. On one test node, rerun network with `-e network_apply=true`.
7. Install ROCm, Broadcom and Pensando roles independently.
8. Validate GPU/RDMA/network, then expand beyond `--limit r5n1`.

Do not enable `auto_reboot` and `network_apply` across all 32 nodes on the first run.
