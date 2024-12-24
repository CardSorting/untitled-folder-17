import os
import sys
from dotenv import load_dotenv
from ..utils.aws_utils import AWSManager

def update_redis_url(auth_token=None):
    """Update Redis URL in config if needed."""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.py')
    
    with open(config_path, 'r') as f:
        lines = f.readlines()
    
    new_lines = []
    for line in lines:
        if 'REDIS_URL =' in line:
            base_url = line.split('=')[1].strip().strip("'")
            if auth_token and 'redis://:' not in base_url:
                # Add auth token to URL
                parts = base_url.split('://')
                new_url = f"{parts[0]}://:{auth_token}@{parts[1]}"
                new_lines.append(f"    REDIS_URL = '{new_url}'\n")
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    
    with open(config_path, 'w') as f:
        f.writelines(new_lines)

def main():
    # Load environment variables
    load_dotenv()
    
    try:
        aws_manager = AWSManager()
    except EnvironmentError as e:
        print(f"AWS Configuration Error: {e}")
        sys.exit(1)
    
    # First, check for ElastiCache resources in all regions
    print("Checking for ElastiCache resources across all AWS regions...")
    aws_manager.list_elasticache_all_regions()
    
    # First, list all available clusters to verify permissions
    print("Checking AWS ElastiCache access...")
    if not aws_manager.list_elasticache_clusters():
        sys.exit(1)
    
    # Extract cluster name from Redis URL in config
    redis_url = os.getenv('REDIS_URL')
    if not redis_url:
        print("Error: REDIS_URL not found in environment variables")
        sys.exit(1)
    
    try:
        cluster_name = redis_url.split('://')[1].split('.')[0]
    except (IndexError, AttributeError):
        print("Error: Invalid REDIS_URL format")
        print(f"Current REDIS_URL: {redis_url}")
        print("Expected format: redis://cluster-name.xxx.region.cache.amazonaws.com:6379")
        sys.exit(1)
    
    print(f"Checking ElastiCache cluster: {cluster_name}")
    
    try:
        # Verify access
        results = aws_manager.verify_elasticache_access(cluster_name)
        
        if not results['cluster_info']:
            print("Error: Could not retrieve cluster information")
            print("Please check if the cluster name is correct and you have the necessary permissions")
            sys.exit(1)
        
        print("\nElastiCache Access Check Results:")
        print("=================================")
        
        # Print cluster info
        cluster_info = results['cluster_info']
        print("\nCluster Information:")
        print(f"Type: {cluster_info['type'].capitalize()}")
        print(f"Status: {cluster_info['status']}")
        print(f"Engine: {cluster_info['engine']}")
        print(f"Engine Version: {cluster_info['engine_version']}")
        
        # Print security group info
        if results['security_groups']:
            print("\nSecurity Group Rules:")
            for sg in results['security_groups']:
                print(f"\nSecurity Group: {sg['GroupId']}")
                for rule in sg.get('IpPermissions', []):
                    if rule.get('FromPort') == 6379:
                        for ip_range in rule.get('IpRanges', []):
                            print(f"Allowed IP: {ip_range.get('CidrIp')}")
        
        # Print subnet info
        if results['subnets']:
            print("\nSubnet Information:")
            for subnet in results['subnets']:
                print(f"\nSubnet: {subnet['SubnetId']}")
                print(f"VPC: {subnet['VpcId']}")
                print(f"Availability Zone: {subnet['AvailabilityZone']}")
                print(f"Auto-assign Public IP: {subnet['MapPublicIpOnLaunch']}")
        
        # Print authentication status
        print(f"\nAuthentication Required: {results['auth_required']}")
        
        # Print actions needed
        if results['actions_needed']:
            print("\nActions Needed:")
            for action in results['actions_needed']:
                print(f"- {action}")
            
            # Attempt to fix issues
            print("\nAttempting to fix issues...")
            
            for action in results['actions_needed']:
                if "Add security group rule" in action:
                    # Extract security group ID from action
                    import re
                    sg_match = re.search(r"group (sg-\w+)", action)
                    if sg_match:
                        sg_id = sg_match.group(1)
                        current_ip = aws_manager.get_current_public_ip()
                        if aws_manager.ensure_security_group_access(sg_id, current_ip):
                            print(f"Added security group rule for IP {current_ip} to group {sg_id}")
                
                elif "auth token" in action.lower():
                    print("\nNOTE: This is a serverless ElastiCache instance.")
                    print("Please ensure you have the correct authentication token configured.")
                    print("You can find the token in the AWS ElastiCache console or retrieve it using AWS Secrets Manager.")
        else:
            print("\nNo actions needed - ElastiCache access is properly configured")
    
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("\nTroubleshooting steps:")
        print("1. Verify your AWS credentials are correct")
        print("2. Ensure you have the necessary IAM permissions for ElastiCache and EC2")
        print("3. Check if the cluster name in your REDIS_URL is correct")
        print("4. Verify the cluster exists in the specified AWS region")
        sys.exit(1)

if __name__ == '__main__':
    main()
