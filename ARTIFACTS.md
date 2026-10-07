# Required offline artifacts

Large binaries are intentionally excluded from Git. Put them in the exact paths below.

```text
artifacts/
├── rocm/
│   └── rocm-installer_1.2.8.70203-61-90~24.04.run
├── broadcom/
│   └── bcm_238.1.138.6a.tar.gz
└── pensando/
    └── ainic_bundle_1.117.5-a-38.tar.gz
```

Selections are controlled by `group_vars/all/cluster.yml`. Exact filenames are mapped in `vars/software_catalog.yml`.

For production use, fill the `sha256` fields in `vars/software_catalog.yml`; artifact preflight validates them when non-empty.
