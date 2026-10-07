# G8825Z5 Ansible Deployment v0.3.1

## v0.3.1 path repair

- `ansible.cfg` sets `roles_path = ./roles` for roles beside the `playbooks` directory.
- Every concrete play loads `../group_vars/all/cluster.yml` explicitly with `vars_files`.
- Existing desired versions are preserved. The packaged `target_kernel` is still `6.8.0-134-generic`; use an explicit override if R5/R6 must remain on `6.8.0-142-generic`.
- See `PATH-FIX.md` for existing-directory repair and validation commands.

This version centralizes all desired versions and node/network metadata. Roles do not hard-code ROCm, Broadcom or Pensando versions.

## Design

- `group_vars/all/cluster.yml`: single source of truth for target versions, kernel, network rules and all 32 nodes.
- `vars/software_catalog.yml`: version -> exact artifact filename mapping.
- `roles/kernel_baseline`: Ubuntu kernel 6.8.0-134-generic baseline, APT meta-package holds, disable unattended upgrades, GRUB default.
- `roles/network_baseline`: runtime management + 8 Pensando rails, MTU 9000, cross-fabric static routes.
- `roles/rocm`, `roles/broadcom`, `roles/pensando`: software installation using catalog-resolved artifacts.

## Address domains

Two address domains are intentionally kept separate:

- `provisioning_fe_ip` / `oob_ip`: copied from the original `pod_cluster_config.ini` (192.168.254.x).
- `runtime_mgmt_ip`: post-install OS management network (10.99.232.60-91/23).

The Netplan role uses `runtime_mgmt_ip`, not the provisioning address.

## Backend fabric rule

- R1/R2 -> 192.168.11.0/24 ... 18.0/24
- R3/R4 -> 192.168.21.0/24 ... 28.0/24
- R5/R6 -> 192.168.31.0/24 ... 38.0/24
- R7/R8 -> 192.168.41.0/24 ... 48.0/24
- odd rack nodes N1-N4 use host octets 1-4
- even rack nodes N1-N4 use host octets 5-8
- gateway on every backend /24 is `.254`
- each rail installs routes to the corresponding rail subnet in the other three rack pairs

Rail/slot physical mapping:

| Slot | Match |
|---|---|
| S1 | enp102s0* |
| S2 | enp118s0* |
| S3 | enp22s0* |
| S4 | enp6s0* |
| S9 | enp246s0* |
| S10 | enp230s0* |
| S11 | enp134s0* |
| S12 | enp150s0* |

The wildcard accepts both `enp102s0` and `enp102s0np0`. Preflight requires exactly one interface to match each pattern.

## Netplan renderer

`netplan_renderer` is empty by default, so generated YAML does not force NetworkManager or systemd-networkd. Netplan/Ubuntu uses the system/default backend.

## Safe first-node workflow

```bash
ansible r5n1 -m ping

ansible-playbook playbooks/00-cluster-preflight.yml --limit r5n1

# Kernel baseline; does not reboot unless auto_reboot=true.
ansible-playbook playbooks/10-kernel-baseline.yml --limit r5n1

# Render + netplan generate only. Does NOT apply by default.
ansible-playbook playbooks/20-network-baseline.yml --limit r5n1

# Review generated file remotely.
ansible r5n1 -b -m command -a 'cat /etc/netplan/60-g8825z5.yaml'

# Explicitly apply after review.
ansible-playbook playbooks/20-network-baseline.yml --limit r5n1 -e network_apply=true
```

## Software deployment

Place the large files listed in `ARTIFACTS.md`, then:

```bash
ansible-playbook playbooks/05-artifact-preflight.yml --limit r5n1
ansible-playbook playbooks/10-install-rocm.yml --limit r5n1
ansible-playbook playbooks/20-install-broadcom.yml --limit r5n1
ansible-playbook playbooks/30-install-pensando.yml --limit r5n1
```

## Full baseline

`90-deploy-baseline.yml` is intentionally `serial: 1`. Network apply and reboot remain off unless explicitly enabled.

```bash
ansible-playbook playbooks/90-deploy-baseline.yml --limit r5n1
```

After R5N1 validation, widen `--limit` gradually.

## Safety defaults

- `network_apply: false`
- `auto_reboot: false`
- `serial: 1` for disruptive deployment playbooks
- artifacts are checked before software install
- Netplan is syntax-validated with `netplan generate`
