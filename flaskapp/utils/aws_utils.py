import boto3
import os
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError
import requests

class AWSManager:
    def __init__(self):
        self.validate_credentials()
        self.elasticache = boto3.client('elasticache')
        self.ec2 = boto3.client('ec2')
    
    def validate_credentials(self):
        """Validate AWS credentials are properly configured."""
        required_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_DEFAULT_REGION']
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        if missing_vars:
            raise EnvironmentError(
                f"Missing required AWS credentials: {', '.join(missing_vars)}\n"
                "Please ensure these environment variables are set in your .env file"
            )
        
        try:
            # Test credentials by making a simple API call
            sts = boto3.client('sts')
            sts.get_caller_identity()
        except (NoCredentialsError, PartialCredentialsError) as e:
            raise EnvironmentError(
                "AWS credentials are invalid or incomplete. "
                "Please check your AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY"
            ) from e
        except ClientError as e:
            if 'InvalidClientTokenId' in str(e):
                raise EnvironmentError(
                    "AWS credentials are invalid. "
                    "Please check your AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY"
                ) from e
            elif 'ExpiredToken' in str(e):
                raise EnvironmentError(
                    "AWS credentials have expired. "
                    "Please refresh your credentials"
                ) from e
            else:
                raise
    
    def get_elasticache_info(self, cluster_name):
        """Get ElastiCache information."""
        try:
            # Try to get replication group info first (for serverless)
            response = self.elasticache.describe_replication_groups()
            for group in response.get('ReplicationGroups', []):
                if cluster_name in group.get('ReplicationGroupId', ''):
                    return {
                        'type': 'serverless',
                        'info': group,
                        'status': group.get('Status'),
                        'engine': 'redis',
                        'engine_version': group.get('EngineVersion'),
                        'security_groups': group.get('SecurityGroups', []),
                        'subnet_group': group.get('CacheSubnetGroupName')
                    }
            
            # If not found in replication groups, try cache clusters
            response = self.elasticache.describe_cache_clusters(
                ShowCacheNodeInfo=True
            )
            for cluster in response.get('CacheClusters', []):
                if cluster_name in cluster.get('CacheClusterId', ''):
                    return {
                        'type': 'cluster',
                        'info': cluster,
                        'status': cluster.get('CacheClusterStatus'),
                        'engine': cluster.get('Engine'),
                        'engine_version': cluster.get('EngineVersion'),
                        'security_groups': [sg['SecurityGroupId'] for sg in cluster.get('SecurityGroups', [])],
                        'subnet_group': cluster.get('CacheSubnetGroupName')
                    }
            
            return None
        except ClientError as e:
            print(f"Error getting ElastiCache info: {e}")
            return None
    
    def get_security_group_rules(self, security_group_id):
        """Get security group rules."""
        try:
            response = self.ec2.describe_security_groups(
                GroupIds=[security_group_id]
            )
            return response['SecurityGroups'][0] if response['SecurityGroups'] else None
        except ClientError as e:
            print(f"Error getting security group info: {e}")
            return None
    
    def ensure_security_group_access(self, security_group_id, source_ip):
        """Ensure security group allows access from source IP."""
        try:
            self.ec2.authorize_security_group_ingress(
                GroupId=security_group_id,
                IpPermissions=[{
                    'IpProtocol': 'tcp',
                    'FromPort': 6379,
                    'ToPort': 6379,
                    'IpRanges': [{'CidrIp': f'{source_ip}/32'}]
                }]
            )
            return True
        except ClientError as e:
            if 'InvalidPermission.Duplicate' in str(e):
                return True
            print(f"Error updating security group: {e}")
            return False
    
    def check_subnet_access(self, subnet_group_name):
        """Check subnet configuration."""
        try:
            response = self.elasticache.describe_cache_subnet_groups(
                CacheSubnetGroupName=subnet_group_name
            )
            subnet_group = response['CacheSubnetGroups'][0]
            subnet_ids = [subnet['SubnetIdentifier'] for subnet in subnet_group['Subnets']]
            
            # Get subnet details
            subnet_details = []
            for subnet_id in subnet_ids:
                subnet_response = self.ec2.describe_subnets(SubnetIds=[subnet_id])
                if subnet_response['Subnets']:
                    subnet_details.append(subnet_response['Subnets'][0])
            
            return subnet_details
        except ClientError as e:
            print(f"Error checking subnet group: {e}")
            return None

    def verify_elasticache_access(self, cluster_name):
        """Verify and fix ElastiCache access configuration."""
        results = {
            'cluster_info': None,
            'security_groups': [],
            'subnets': [],
            'auth_required': None,
            'actions_needed': []
        }
        
        # Get cluster info
        cluster_info = self.get_elasticache_info(cluster_name)
        if not cluster_info:
            results['actions_needed'].append("Unable to retrieve cluster information")
            return results
        
        results['cluster_info'] = cluster_info
        
        # Check security groups
        for sg_id in cluster_info['security_groups']:
            sg_info = self.get_security_group_rules(sg_id)
            if sg_info:
                results['security_groups'].append(sg_info)
                
                # Check if current IP has access
                current_ip = self.get_current_public_ip()
                if current_ip:
                    has_access = False
                    for rule in sg_info.get('IpPermissions', []):
                        for ip_range in rule.get('IpRanges', []):
                            if ip_range['CidrIp'].startswith(current_ip):
                                has_access = True
                                break
                    
                    if not has_access:
                        results['actions_needed'].append(f"Add security group rule for IP {current_ip} to group {sg_id}")
        
        # Check subnets
        if cluster_info['subnet_group']:
            subnet_details = self.check_subnet_access(cluster_info['subnet_group'])
            if subnet_details:
                results['subnets'] = subnet_details
                for subnet in subnet_details:
                    if not subnet.get('MapPublicIpOnLaunch'):
                        results['actions_needed'].append(
                            f"Subnet {subnet['SubnetId']} in AZ {subnet['AvailabilityZone']} "
                            "does not auto-assign public IPs"
                        )
        
        # Check if it's serverless
        if cluster_info['type'] == 'serverless':
            results['auth_required'] = True
            results['actions_needed'].append(
                "This is a serverless instance - ensure you have the correct auth token "
                "and update the Redis URL if needed"
            )
        
        return results

    def get_current_public_ip(self):
        """Get current public IP address."""
        try:
            import requests
            response = requests.get('https://api.ipify.org')
            return response.text
        except Exception as e:
            print(f"Error getting public IP: {e}")
            return None

    def list_elasticache_clusters(self):
        """List all ElastiCache clusters and replication groups."""
        try:
            print("Checking ElastiCache permissions...")
            print("\nListing Cache Clusters:")
            clusters = self.elasticache.describe_cache_clusters()
            for cluster in clusters.get('CacheClusters', []):
                print(f"- {cluster.get('CacheClusterId')} ({cluster.get('CacheClusterStatus')})")
            
            print("\nListing Replication Groups:")
            groups = self.elasticache.describe_replication_groups()
            for group in groups.get('ReplicationGroups', []):
                print(f"- {group.get('ReplicationGroupId')} ({group.get('Status')})")
            
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            print(f"\nAWS Error: {error_code}")
            print(f"Message: {error_message}")
            
            if error_code == 'AccessDeniedException':
                print("\nYour IAM user/role does not have sufficient permissions.")
                print("Required permissions:")
                print("- elasticache:DescribeCacheClusters")
                print("- elasticache:DescribeReplicationGroups")
                print("- elasticache:DescribeCacheSubnetGroups")
                print("- ec2:DescribeSecurityGroups")
                print("- ec2:DescribeSubnets")
                print("- ec2:AuthorizeSecurityGroupIngress")
            return False

    def list_elasticache_all_regions(self):
        """List ElastiCache clusters and replication groups across all regions."""
        try:
            # Get list of all AWS regions
            ec2 = boto3.client('ec2')
            regions = [region['RegionName'] for region in ec2.describe_regions()['Regions']]
            
            print("Checking ElastiCache in all AWS regions...")
            found_resources = False
            
            for region in regions:
                try:
                    print(f"\nRegion: {region}")
                    elasticache = boto3.client('elasticache', region_name=region)
                    
                    # Check cache clusters
                    clusters = elasticache.describe_cache_clusters()
                    if clusters.get('CacheClusters'):
                        found_resources = True
                        print("Cache Clusters:")
                        for cluster in clusters['CacheClusters']:
                            print(f"- {cluster.get('CacheClusterId')} ({cluster.get('CacheClusterStatus')})")
                    
                    # Check replication groups
                    groups = elasticache.describe_replication_groups()
                    if groups.get('ReplicationGroups'):
                        found_resources = True
                        print("Replication Groups:")
                        for group in groups['ReplicationGroups']:
                            print(f"- {group.get('ReplicationGroupId')} ({group.get('Status')})")
                
                except ClientError as e:
                    if e.response['Error']['Code'] == 'AccessDeniedException':
                        print(f"Access denied in region {region}")
                    else:
                        print(f"Error in region {region}: {e}")
            
            if not found_resources:
                print("\nNo ElastiCache resources found in any region")
            
            return found_resources
        
        except Exception as e:
            print(f"Error listing regions: {e}")
            return False
