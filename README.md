# Proxmox VE Backup by Tag

A Python script that enables tag-based backup functionality for Proxmox VE virtual machines and containers. This script addresses Proxmox's current limitation of not being able to backup VMs/containers by tags.

## Features

- ✅ **Tag-Based Filtering**: Include or exclude VMs/containers based on tags
- ✅ **Multiple Tag Support**: Specify multiple `--tag` and `--exclude-tag` options
- ✅ **Cluster-Wide Support**: Works in multi-node Proxmox clusters with shared storage
- ✅ **Flexible Backup Ordering**: Order backups by VMID or disk size
- ✅ **Dynamic Storage Resolution**: Automatically resolves storage names through Proxmox API
- ✅ **Tag Query**: List all available tags in your cluster
- ✅ **Dry Run Mode**: Test your backup configuration without creating actual backups
- ✅ **Comprehensive Logging**: Detailed logs with configurable verbosity
- ✅ **YAML Configuration**: Support for configuration files for easier management
- ✅ **Error Handling**: Robust error handling with detailed feedback

## Requirements

- Python 3.6 or higher
- Access to Proxmox VE API
- Network connectivity to Proxmox host

## Installation

1. Clone this repository:
```bash
git clone https://github.com/jannoke/pve-backup-by-tag.git
cd pve-backup-by-tag
```

2. Install required Python packages:
```bash
pip install -r requirements.txt
```

3. Make the script executable:
```bash
chmod +x pve-backup-by-tag.py
```

## Usage

### Basic Usage

#### Backup VMs with specific tags:
```bash
python pve-backup-by-tag.py \
  --host https://proxmox.local:8006 \
  --user root@pam \
  --tag production \
  --storage backup_storage
```

#### Backup with multiple tags (OR logic):
```bash
python pve-backup-by-tag.py \
  --host https://proxmox.local:8006 \
  --user root@pam \
  --tag web \
  --tag database \
  --storage backup_storage
```

#### Exclude specific tags:
```bash
python pve-backup-by-tag.py \
  --host https://proxmox.local:8006 \
  --user root@pam \
  --tag production \
  --exclude-tag maintenance \
  --storage backup_storage
```

#### Order backups by size (smallest first):
```bash
python pve-backup-by-tag.py \
  --host https://proxmox.local:8006 \
  --user root@pam \
  --tag production \
  --storage backup_storage \
  --order size
```

#### Dry run (test without creating backups):
```bash
python pve-backup-by-tag.py \
  --host https://proxmox.local:8006 \
  --user root@pam \
  --tag production \
  --storage backup_storage \
  --dry-run
```

#### Query all tags in the cluster:
```bash
python pve-backup-by-tag.py \
  --host https://proxmox.local:8006 \
  --user root@pam \
  --get-tags
```

### Using Configuration File

1. Copy the example configuration:
```bash
cp config.example.yaml config.yaml
```

2. Edit `config.yaml` with your settings

3. Run the script with config file:
```bash
python pve-backup-by-tag.py --config config.yaml
```

Command-line arguments override configuration file settings.

## Command-Line Options

### Connection Options
- `--host`: Proxmox host URL (e.g., `https://proxmox.local:8006`)
- `--user`: Proxmox username (e.g., `root@pam`)
- `--password`: Proxmox password (prompted if not provided)
- `--verify-ssl`: Verify SSL certificates (default: false)
- `--config`: Path to YAML configuration file

### Tag Filtering Options
- `--tag`: Include VMs/containers with this tag (can be specified multiple times)
- `--exclude-tag`: Exclude VMs/containers with this tag (can be specified multiple times)
- `--get-tags`: Query and list all tags in the cluster

### Backup Options
- `--storage`: Storage name for backups (required for backup operations)
- `--order`: Order backups by `vmid` (default) or `size`
- `--mode`: Backup mode - `snapshot` (default), `suspend`, or `stop`
- `--compress`: Compression algorithm - `zstd` (default), `gzip`, `lzo`, or `0` (none)

### Operation Modes
- `--dry-run`: Perform a dry run without creating actual backups
- `--cluster-mode`: Cluster operation mode - `centralized` (default) or `distributed`

### Logging Options
- `--log-level`: Logging level - `DEBUG`, `INFO` (default), `WARNING`, or `ERROR`
- `--log-file`: Path to log file

## Tag Filtering Logic

### Include Tags (`--tag`)
- If one or more `--tag` options are specified, only VMs/containers with **at least one** of these tags will be included
- Multiple tags work with OR logic: VM must have tag1 OR tag2 OR tag3
- If no `--tag` is specified, all VMs/containers are considered (unless excluded)

### Exclude Tags (`--exclude-tag`)
- VMs/containers with **any** of the exclude tags will be filtered out
- Exclude tags are processed **before** include tags
- If a VM has both an include and exclude tag, it will be **excluded**

### Example Scenarios

1. **Backup all production VMs except those in maintenance:**
   ```bash
   --tag production --exclude-tag maintenance
   ```

2. **Backup web and database servers, but not test instances:**
   ```bash
   --tag web --tag database --exclude-tag test
   ```

3. **Backup everything except temporary VMs:**
   ```bash
   --exclude-tag temporary
   ```

## Backup Modes

- **snapshot** (default): Uses a snapshot for running VMs. Fast and efficient, but requires QEMU guest agent for filesystem consistency
- **suspend**: Suspends the VM during backup. Ensures consistency but causes brief downtime
- **stop**: Stops the VM during backup. Maximum consistency but causes full downtime

## Compression Options

- **zstd** (default): Best balance of compression ratio and speed
- **gzip**: Good compression, moderate speed
- **lzo**: Fast compression, lower compression ratio
- **0**: No compression, fastest

## Cluster Modes

- **centralized** (default): Process one backup at a time across the entire cluster. Suitable for shared storage with limited I/O capacity
- **distributed**: Allow concurrent backups on different nodes. Better for clusters with node-local storage or high-performance shared storage

## Security Considerations

1. **Password Security**: 
   - Avoid passing passwords via command line (visible in process list)
   - Use configuration file with restricted permissions: `chmod 600 config.yaml`
   - Script will prompt for password if not provided

2. **SSL Verification**:
   - By default, SSL certificate verification is disabled (common for self-signed certs)
   - Enable with `--verify-ssl` for production environments with valid certificates

3. **API Permissions**:
   - User needs appropriate permissions in Proxmox:
     - VM.Backup permission on VMs/containers
     - Datastore.AllocateSpace on target storage
     - VM.Audit to read VM configurations

## Logging

The script provides detailed logging at multiple levels:

- **DEBUG**: Detailed information for troubleshooting
- **INFO**: General information about operations (default)
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for failures

Logs include:
- Authentication status
- Resources discovered
- Tag filtering results
- Backup operations and results
- Summary statistics

## Examples

### Daily Production Backup
```bash
#!/bin/bash
# /usr/local/bin/backup-production.sh

python3 /opt/pve-backup-by-tag/pve-backup-by-tag.py \
  --config /etc/pve-backup/production.yaml \
  --log-file /var/log/pve-backup-production-$(date +%Y%m%d).log
```

### Weekly Full Cluster Backup (by size)
```bash
#!/bin/bash
# Backup all VMs, starting with smallest

python3 /opt/pve-backup-by-tag/pve-backup-by-tag.py \
  --host https://proxmox.local:8006 \
  --user backup@pve \
  --storage weekly_backup \
  --order size \
  --compress zstd \
  --log-file /var/log/pve-backup-weekly-$(date +%Y%m%d).log
```

### Cron Job Example
```bash
# Backup production VMs daily at 2 AM
0 2 * * * /usr/local/bin/backup-production.sh

# Backup database VMs daily at 3 AM
0 3 * * * /usr/local/bin/backup-databases.sh
```

## Troubleshooting

### Authentication Fails
- Verify host URL is correct (include protocol and port)
- Check username format (user@realm, e.g., root@pam)
- Verify user has API access permissions
- Check network connectivity to Proxmox host

### No VMs Match Filter
- Use `--get-tags` to list all available tags
- Verify tag names match exactly (case-sensitive)
- Check if VMs actually have tags assigned in Proxmox
- Use `--log-level DEBUG` for detailed filtering information

### Backup Creation Fails
- Verify storage name exists and is accessible
- Check user has VM.Backup permissions
- Ensure sufficient space on target storage
- Review Proxmox task log for detailed error messages

### SSL Certificate Errors
- Use `--verify-ssl false` for self-signed certificates
- Or add certificate to system trust store

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is open source and available under the MIT License.

## Acknowledgments

This script was created to address the lack of native tag-based backup functionality in Proxmox VE. It leverages the Proxmox API to provide flexible, automated backup solutions based on VM/container tags.

## Support

For issues, questions, or contributions, please visit:
https://github.com/jannoke/pve-backup-by-tag
