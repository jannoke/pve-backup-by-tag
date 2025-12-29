# Quick Start Guide

Get started with pve-backup-by-tag in 5 minutes!

## Prerequisites

- Python 3.6 or higher
- Access to Proxmox VE API (URL, username, password)
- A backup storage configured in Proxmox

## Installation

```bash
# Clone the repository
git clone https://github.com/jannoke/pve-backup-by-tag.git
cd pve-backup-by-tag

# Install dependencies
pip install -r requirements.txt

# Make the script executable
chmod +x pve-backup-by-tag.py
```

## First Run - Query Tags

Let's see what tags exist in your Proxmox cluster:

```bash
python3 pve-backup-by-tag.py \
  --host https://your-proxmox:8006 \
  --user root@pam \
  --get-tags
```

You'll be prompted for your password. The script will list all tags found.

## First Backup - Dry Run

Test backing up VMs with a specific tag (without actually creating backups):

```bash
python3 pve-backup-by-tag.py \
  --host https://your-proxmox:8006 \
  --user root@pam \
  --tag production \
  --storage local-zfs \
  --dry-run
```

This shows you what would be backed up without actually doing it.

## Create Your First Backup

Once you're confident with the dry run, create real backups:

```bash
python3 pve-backup-by-tag.py \
  --host https://your-proxmox:8006 \
  --user root@pam \
  --tag production \
  --storage local-zfs
```

## Using Configuration File

For regular use, create a configuration file:

```bash
# Copy the example
cp config.example.yaml config.yaml

# Edit it with your settings
nano config.yaml
```

Update these settings:
- `host`: Your Proxmox URL
- `user`: Your username
- `password`: Your password (optional, will be prompted)
- `storage`: Your backup storage name
- `tags`: Tags to include

Then run:

```bash
python3 pve-backup-by-tag.py --config config.yaml
```

## Common Use Cases

### Backup all production VMs
```bash
python3 pve-backup-by-tag.py --config config.yaml --tag production
```

### Backup multiple tag types
```bash
python3 pve-backup-by-tag.py --config config.yaml --tag web --tag database
```

### Exclude maintenance VMs
```bash
python3 pve-backup-by-tag.py --config config.yaml --tag production --exclude-tag maintenance
```

### Order by size (smallest first)
```bash
python3 pve-backup-by-tag.py --config config.yaml --tag production --order size
```

### Enable detailed logging
```bash
python3 pve-backup-by-tag.py --config config.yaml --tag production --log-level DEBUG
```

## Scheduling with Cron

Create a backup script:

```bash
# /usr/local/bin/backup-production.sh
#!/bin/bash
python3 /opt/pve-backup-by-tag/pve-backup-by-tag.py \
  --config /opt/pve-backup-by-tag/config.yaml \
  --log-file /var/log/pve-backup-$(date +\%Y\%m\%d).log
```

Add to crontab:

```bash
# Edit crontab
crontab -e

# Add this line for daily backups at 2 AM
0 2 * * * /usr/local/bin/backup-production.sh
```

## Troubleshooting

### SSL Certificate Errors
If you get SSL errors with self-signed certificates, use `--verify-ssl false` (or set in config).

### Authentication Failed
- Verify your host URL includes `https://` and port (usually `:8006`)
- Check username format: `user@realm` (e.g., `root@pam`)
- Ensure user has proper API permissions

### No VMs Match Filter
- Use `--get-tags` to see available tags
- Check tag names (case-sensitive)
- Verify VMs have tags assigned in Proxmox web UI

## Next Steps

- Read the full [README.md](README.md) for all features
- Check out [example-backup-script.sh](example-backup-script.sh) for automation ideas
- Review [CONTRIBUTING.md](CONTRIBUTING.md) if you want to contribute

## Getting Help

- Check the [README.md](README.md) for detailed documentation
- Search existing GitHub issues
- Create a new issue if you need help

Happy backing up! 🚀
