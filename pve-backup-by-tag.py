#!/usr/bin/env python3
"""
Proxmox VE Backup by Tag Script

This script provides tag-based backup functionality for Proxmox VE environments.
It integrates with the Proxmox API to query VMs and containers, filter them by tags,
and execute backups with various ordering and filtering options.
"""

import argparse
import sys
import logging
import requests
import urllib3
from typing import List, Dict, Set, Optional
from datetime import datetime
import yaml
import json

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ProxmoxAPI:
    """Handles communication with Proxmox API"""
    
    def __init__(self, host: str, user: str, password: str, verify_ssl: bool = False):
        self.host = host.rstrip('/')
        self.user = user
        self.password = password
        self.verify_ssl = verify_ssl
        self.ticket = None
        self.csrf_token = None
        self.session = requests.Session()
        self.session.verify = verify_ssl
        
    def authenticate(self) -> bool:
        """Authenticate with Proxmox API and obtain ticket"""
        try:
            url = f"{self.host}/api2/json/access/ticket"
            data = {
                'username': self.user,
                'password': self.password
            }
            response = self.session.post(url, data=data)
            response.raise_for_status()
            
            result = response.json()['data']
            self.ticket = result['ticket']
            self.csrf_token = result['CSRFPreventionToken']
            
            # Set up session with authentication
            self.session.headers.update({
                'CSRFPreventionToken': self.csrf_token
            })
            self.session.cookies.set('PVEAuthCookie', self.ticket)
            
            logging.info("Successfully authenticated with Proxmox API")
            return True
            
        except Exception as e:
            logging.error(f"Authentication failed: {e}")
            return False
    
    def get_cluster_resources(self) -> List[Dict]:
        """Get all cluster resources (VMs and containers)"""
        try:
            url = f"{self.host}/api2/json/cluster/resources"
            params = {'type': 'vm'}
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            resources = response.json()['data']
            logging.info(f"Retrieved {len(resources)} resources from cluster")
            return resources
            
        except Exception as e:
            logging.error(f"Failed to get cluster resources: {e}")
            return []
    
    def get_vm_config(self, node: str, vm_type: str, vmid: int) -> Dict:
        """Get configuration for a specific VM or container"""
        try:
            url = f"{self.host}/api2/json/nodes/{node}/{vm_type}/{vmid}/config"
            response = self.session.get(url)
            response.raise_for_status()
            
            config = response.json()['data']
            return config
            
        except Exception as e:
            logging.error(f"Failed to get config for {vm_type} {vmid} on {node}: {e}")
            return {}
    
    def get_storage_list(self) -> List[Dict]:
        """Get list of available storage"""
        try:
            url = f"{self.host}/api2/json/storage"
            response = self.session.get(url)
            response.raise_for_status()
            
            storage_list = response.json()['data']
            logging.info(f"Retrieved {len(storage_list)} storage entries")
            return storage_list
            
        except Exception as e:
            logging.error(f"Failed to get storage list: {e}")
            return []
    
    def create_backup(self, node: str, vmid: int, storage: str, mode: str = 'snapshot',
                     compress: str = 'zstd', remove: int = 0) -> Optional[str]:
        """Create a backup for a VM or container"""
        try:
            url = f"{self.host}/api2/json/nodes/{node}/vzdump"
            data = {
                'vmid': vmid,
                'storage': storage,
                'mode': mode,
                'compress': compress,
                'remove': remove
            }
            
            response = self.session.post(url, data=data)
            response.raise_for_status()
            
            result = response.json()['data']
            logging.info(f"Backup task created for VMID {vmid}: {result}")
            return result
            
        except Exception as e:
            logging.error(f"Failed to create backup for VMID {vmid}: {e}")
            return None


class BackupManager:
    """Manages the backup process with filtering and ordering"""
    
    def __init__(self, api: ProxmoxAPI, config: Dict):
        self.api = api
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def get_all_tags(self) -> Set[str]:
        """Query and return all unique tags from VMs and containers"""
        resources = self.api.get_cluster_resources()
        all_tags = set()
        
        for resource in resources:
            node = resource.get('node')
            vmid = resource.get('vmid')
            vm_type = 'qemu' if resource.get('type') == 'qemu' else 'lxc'
            
            config = self.api.get_vm_config(node, vm_type, vmid)
            tags = config.get('tags', '')
            
            if tags:
                # Tags are semicolon-separated in Proxmox
                tag_list = [tag.strip() for tag in tags.split(';') if tag.strip()]
                all_tags.update(tag_list)
        
        return all_tags
    
    def filter_resources_by_tags(self, resources: List[Dict], 
                                 include_tags: List[str],
                                 exclude_tags: List[str]) -> List[Dict]:
        """Filter resources based on include and exclude tags"""
        filtered = []
        
        for resource in resources:
            node = resource.get('node')
            vmid = resource.get('vmid')
            vm_type = 'qemu' if resource.get('type') == 'qemu' else 'lxc'
            
            config = self.api.get_vm_config(node, vm_type, vmid)
            tags = config.get('tags', '')
            
            if not tags and not include_tags:
                # If no include tags specified, include all
                if not exclude_tags:
                    filtered.append(resource)
                continue
            
            # Parse tags
            tag_list = [tag.strip() for tag in tags.split(';') if tag.strip()]
            tag_set = set(tag_list)
            
            # Check exclude tags first
            if exclude_tags:
                if any(etag in tag_set for etag in exclude_tags):
                    self.logger.debug(f"VMID {vmid} excluded due to exclude tags")
                    continue
            
            # Check include tags
            if include_tags:
                if any(itag in tag_set for itag in include_tags):
                    filtered.append(resource)
                else:
                    self.logger.debug(f"VMID {vmid} does not match include tags")
            else:
                # No include tags specified, include if not excluded
                filtered.append(resource)
        
        return filtered
    
    def get_disk_size(self, resource: Dict) -> int:
        """Get total disk size for a resource"""
        try:
            disk_size = resource.get('disk', 0)
            maxdisk = resource.get('maxdisk', 0)
            # Use maxdisk if available, otherwise disk
            return maxdisk if maxdisk > 0 else disk_size
        except:
            return 0
    
    def order_resources(self, resources: List[Dict], order_by: str = 'vmid') -> List[Dict]:
        """Order resources by specified criteria"""
        if order_by == 'size':
            # Sort by disk size (smallest first)
            return sorted(resources, key=lambda r: self.get_disk_size(r))
        else:
            # Default: sort by VMID
            return sorted(resources, key=lambda r: r.get('vmid', 0))
    
    def execute_backups(self, resources: List[Dict], storage: str, 
                       dry_run: bool = False, mode: str = 'snapshot') -> Dict:
        """Execute backups for filtered and ordered resources"""
        results = {
            'total': len(resources),
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'tasks': []
        }
        
        if dry_run:
            self.logger.info("=== DRY RUN MODE - No actual backups will be created ===")
        
        for resource in resources:
            vmid = resource.get('vmid')
            node = resource.get('node')
            name = resource.get('name', 'N/A')
            vm_type = resource.get('type')
            status = resource.get('status')
            disk_size = self.get_disk_size(resource)
            
            self.logger.info(f"Processing VMID {vmid} ({name}) on node {node} - "
                           f"Type: {vm_type}, Status: {status}, Size: {disk_size} bytes")
            
            if status != 'running' and mode == 'snapshot':
                self.logger.warning(f"VMID {vmid} is not running, snapshot mode may fail. "
                                  f"Consider using 'suspend' or 'stop' mode.")
            
            if dry_run:
                self.logger.info(f"[DRY RUN] Would backup VMID {vmid} to storage '{storage}'")
                results['tasks'].append({
                    'vmid': vmid,
                    'node': node,
                    'status': 'dry-run',
                    'message': 'Dry run - no backup created'
                })
                results['successful'] += 1
            else:
                task = self.api.create_backup(node, vmid, storage, mode=mode)
                if task:
                    self.logger.info(f"Successfully initiated backup for VMID {vmid}")
                    results['tasks'].append({
                        'vmid': vmid,
                        'node': node,
                        'status': 'success',
                        'task': task
                    })
                    results['successful'] += 1
                else:
                    self.logger.error(f"Failed to initiate backup for VMID {vmid}")
                    results['tasks'].append({
                        'vmid': vmid,
                        'node': node,
                        'status': 'failed',
                        'message': 'Failed to create backup task'
                    })
                    results['failed'] += 1
        
        return results


def load_config(config_file: str) -> Dict:
    """Load configuration from YAML file"""
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        logging.info(f"Loaded configuration from {config_file}")
        return config
    except Exception as e:
        logging.error(f"Failed to load config file: {e}")
        return {}


def setup_logging(log_level: str = 'INFO', log_file: Optional[str] = None):
    """Setup logging configuration"""
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Setup root logger
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            logging.info(f"Logging to file: {log_file}")
        except Exception as e:
            logging.error(f"Failed to setup file logging: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Proxmox VE Backup by Tag Script',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Backup all VMs with 'production' tag
  %(prog)s --host https://proxmox.local:8006 --user root@pam --tag production --storage backup_storage
  
  # Backup VMs with 'web' or 'database' tags, excluding 'maintenance'
  %(prog)s --host https://proxmox.local:8006 --user root@pam --tag web --tag database --exclude-tag maintenance --storage backup_storage
  
  # List all tags in the cluster
  %(prog)s --host https://proxmox.local:8006 --user root@pam --get-tags
  
  # Dry run with size-based ordering
  %(prog)s --host https://proxmox.local:8006 --user root@pam --tag production --storage backup_storage --order size --dry-run
  
  # Use configuration file
  %(prog)s --config config.yaml
        """
    )
    
    # Proxmox connection arguments
    parser.add_argument('--host', help='Proxmox host URL (e.g., https://proxmox.local:8006)')
    parser.add_argument('--user', help='Proxmox username (e.g., root@pam)')
    parser.add_argument('--password', help='Proxmox password')
    parser.add_argument('--verify-ssl', action='store_true', help='Verify SSL certificates')
    
    # Configuration file
    parser.add_argument('--config', help='Path to YAML configuration file')
    
    # Tag filtering
    parser.add_argument('--tag', action='append', dest='tags', 
                       help='Include VMs/containers with this tag (can be specified multiple times)')
    parser.add_argument('--exclude-tag', action='append', dest='exclude_tags',
                       help='Exclude VMs/containers with this tag (can be specified multiple times)')
    
    # Query tags
    parser.add_argument('--get-tags', action='store_true',
                       help='Query and list all tags in the cluster')
    
    # Backup options
    parser.add_argument('--storage', help='Storage name for backups')
    parser.add_argument('--order', choices=['vmid', 'size'], default='vmid',
                       help='Order backups by VMID or disk size (default: vmid)')
    parser.add_argument('--mode', choices=['snapshot', 'suspend', 'stop'], default='snapshot',
                       help='Backup mode (default: snapshot)')
    parser.add_argument('--compress', choices=['0', 'gzip', 'lzo', 'zstd'], default='zstd',
                       help='Compression algorithm (default: zstd)')
    
    # Operation modes
    parser.add_argument('--dry-run', action='store_true',
                       help='Perform a dry run without creating backups')
    parser.add_argument('--cluster-mode', choices=['centralized', 'distributed'], 
                       default='centralized',
                       help='Cluster operation mode (default: centralized)')
    
    # Logging
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Logging level (default: INFO)')
    parser.add_argument('--log-file', help='Log file path')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level, args.log_file)
    
    # Load configuration from file if specified
    config = {}
    if args.config:
        config = load_config(args.config)
    
    # Override config with command-line arguments
    host = args.host or config.get('host')
    user = args.user or config.get('user')
    password = args.password or config.get('password')
    verify_ssl = args.verify_ssl or config.get('verify_ssl', False)
    
    # Validate required parameters
    if not host or not user:
        logging.error("Host and user are required. Provide them via --host and --user or --config")
        parser.print_help()
        sys.exit(1)
    
    # Get password if not provided
    if not password:
        import getpass
        password = getpass.getpass("Proxmox password: ")
    
    # Initialize Proxmox API
    logging.info(f"Connecting to Proxmox at {host}")
    api = ProxmoxAPI(host, user, password, verify_ssl)
    
    if not api.authenticate():
        logging.error("Failed to authenticate with Proxmox API")
        sys.exit(1)
    
    # Initialize backup manager
    backup_manager = BackupManager(api, config)
    
    # Handle --get-tags
    if args.get_tags:
        logging.info("Querying all tags from cluster...")
        tags = backup_manager.get_all_tags()
        if tags:
            logging.info(f"Found {len(tags)} unique tags:")
            for tag in sorted(tags):
                print(f"  - {tag}")
        else:
            logging.info("No tags found in the cluster")
        sys.exit(0)
    
    # Validate backup requirements
    storage = args.storage or config.get('storage')
    if not storage:
        logging.error("Storage is required for backup operations. Use --storage or config file")
        sys.exit(1)
    
    # Get include/exclude tags
    include_tags = args.tags or config.get('tags', [])
    exclude_tags = args.exclude_tags or config.get('exclude_tags', [])
    
    logging.info(f"Include tags: {include_tags if include_tags else 'None (all VMs)'}")
    logging.info(f"Exclude tags: {exclude_tags if exclude_tags else 'None'}")
    
    # Get all resources
    logging.info("Retrieving cluster resources...")
    resources = api.get_cluster_resources()
    
    if not resources:
        logging.warning("No resources found in cluster")
        sys.exit(0)
    
    # Filter resources
    logging.info("Filtering resources by tags...")
    filtered_resources = backup_manager.filter_resources_by_tags(
        resources, include_tags, exclude_tags
    )
    
    if not filtered_resources:
        logging.warning("No resources match the specified tag filters")
        sys.exit(0)
    
    logging.info(f"Found {len(filtered_resources)} resources matching filters")
    
    # Order resources
    logging.info(f"Ordering resources by {args.order}...")
    ordered_resources = backup_manager.order_resources(filtered_resources, args.order)
    
    # Display resources to be backed up
    logging.info("Resources to be backed up:")
    for resource in ordered_resources:
        vmid = resource.get('vmid')
        name = resource.get('name', 'N/A')
        node = resource.get('node')
        size = backup_manager.get_disk_size(resource)
        logging.info(f"  - VMID {vmid}: {name} (Node: {node}, Size: {size} bytes)")
    
    # Execute backups
    logging.info("Starting backup process...")
    results = backup_manager.execute_backups(
        ordered_resources, 
        storage, 
        dry_run=args.dry_run,
        mode=args.mode
    )
    
    # Print summary
    logging.info("=" * 70)
    logging.info("BACKUP SUMMARY")
    logging.info("=" * 70)
    logging.info(f"Total resources processed: {results['total']}")
    logging.info(f"Successful: {results['successful']}")
    logging.info(f"Failed: {results['failed']}")
    logging.info(f"Skipped: {results['skipped']}")
    logging.info("=" * 70)
    
    # Exit with appropriate code
    if results['failed'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
