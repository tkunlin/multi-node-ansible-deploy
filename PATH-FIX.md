# v0.3.1：修正角色與共用變數的載入路徑

v0.3 的 `roles/kernel_baseline` 已包含在部署包中，但 `ansible.cfg` 未設定專案根目錄的角色搜尋路徑。共用設定放在根目錄 `group_vars/`，與 `inventory/hosts.ini` 和 `playbooks/` 都不相鄰，也需要明確載入。

## 修正內容

1. 在 `ansible.cfg` 的 `[defaults]` 中加入 `roles_path = ./roles`。
2. 所有含 `hosts:` 的 playbook 在 `vars_files` 加入 `../group_vars/all/cluster.yml`，保留原有軟體目錄檔引用。
3. 原有 kernel、ROCm、NIC 版本及 inventory 內容均保留。版本仍從 `group_vars/all/cluster.yml` 管理，命令列 `-e` 可覆寫。

## 現有 v0.3 目錄的立即處理方式

下列方式使用環境變數指定角色路徑，並以 `-e @...` 明確載入共用設定，不需先修改檔案。

假設：r5n1 的目標 kernel 仍為 `6.8.0-142-generic`。若你的目標不同，請調整命令中的值。

```bash
cd ~/Documents/G8825Z5_ansible_deploy_v0.3
export ANSIBLE_CONFIG="$PWD/ansible.cfg"
export ANSIBLE_ROLES_PATH="$PWD/roles"

ansible-playbook playbooks/10-kernel-baseline.yml \
  --limit r5n1 \
  -e @group_vars/all/cluster.yml \
  -e target_kernel=6.8.0-142-generic \
  --syntax-check
```

語法檢查成功後，再執行實際部署：

```bash
ansible-playbook playbooks/10-kernel-baseline.yml \
  --limit r5n1 \
  -e @group_vars/all/cluster.yml \
  -e target_kernel=6.8.0-142-generic
```

此 playbook 使用 `become: true`；若 sudo 需要密碼，實際部署命令可加上 `-K`。

潛在風險：v0.3 和本修正版的設定檔目前都是 `target_kernel: "6.8.0-134-generic"`。若直接使用這個預設值，kernel role 會安裝 134 的套件並設定 GRUB 預設版本；若目標是 142，應明確覆寫或修改設定。`auto_reboot` 預設為 `false`。

## 永久修正現有專案

解壓本修正版後，可從舊目錄執行修補程式，以保留你已修改的 inventory 與版本設定。依實際解壓路徑調整腳本位置：

```bash
cd ~/Documents/G8825Z5_ansible_deploy_v0.3
python3 ../G8825Z5_ansible_deploy_v0.3.1/scripts/fix_v0_3_paths.py
export ANSIBLE_CONFIG="$PWD/ansible.cfg"
```

腳本僅修正 `ansible.cfg` 和 playbook 的載入路徑，會先備份至 `path-fix-backups/`，可重複執行。若共用設定已寫入正確的目標 kernel，可省略立即處理方式中的兩個 `-e` 參數。

## 檢查修正是否生效

在專案根目錄執行：

```bash
ansible --version
ansible-config dump --only-changed
ansible-playbook playbooks/10-kernel-baseline.yml --limit r5n1 --list-hosts
ansible-playbook playbooks/10-kernel-baseline.yml --limit r5n1 --syntax-check
```

`config file` 應指向目前專案的 `ansible.cfg`，`DEFAULT_ROLES_PATH` 應包含目前專案的 `roles/`，`--list-hosts` 應只列出 `r5n1`。`--syntax-check` 不會連線或修改遠端節點，也不能證明套件可下載或部署會成功。

## 本修正版的驗證範圍

- 已解析修改後的 YAML，確認共用變數檔、軟體目錄檔及角色引用路徑存在。
- 已確認重複執行修補程式不產生第二次修改。
- 已比對共用設定、inventory 與角色實作的內容保留原樣。
- 本執行環境無可用的 Ansible 安裝，尚未執行 Ansible 原生 `--syntax-check`；請在你的 remotedesktop 執行上述檢查。

## 官方參考

- [Ansible roles_path 設定](https://docs.ansible.com/projects/ansible/latest/reference_appendices/config.html#default-roles-path)
- [Ansible 設定檔載入順序](https://docs.ansible.com/projects/ansible/latest/reference_appendices/config.html#the-configuration-file)
