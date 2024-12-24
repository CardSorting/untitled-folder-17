import os
import configparser
import sys

def setup_aws_credentials():
    """Set up AWS credentials file."""
    # Get AWS credentials from environment variables or user input
    aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    aws_region = os.environ.get('AWS_DEFAULT_REGION', 'us-west-2')
    
    if not aws_access_key:
        aws_access_key = input("Enter AWS Access Key ID: ")
    if not aws_secret_key:
        aws_secret_key = input("Enter AWS Secret Access Key: ")
    
    # Create ~/.aws directory if it doesn't exist
    aws_dir = os.path.expanduser('~/.aws')
    if not os.path.exists(aws_dir):
        os.makedirs(aws_dir)
    
    # Create or update credentials file
    credentials_path = os.path.join(aws_dir, 'credentials')
    config = configparser.ConfigParser()
    
    if os.path.exists(credentials_path):
        config.read(credentials_path)
    
    if 'default' not in config:
        config['default'] = {}
    
    config['default']['aws_access_key_id'] = aws_access_key
    config['default']['aws_secret_access_key'] = aws_secret_key
    
    with open(credentials_path, 'w') as f:
        config.write(f)
    
    # Create or update config file
    config_path = os.path.join(aws_dir, 'config')
    config = configparser.ConfigParser()
    
    if os.path.exists(config_path):
        config.read(config_path)
    
    if 'default' not in config:
        config['default'] = {}
    
    config['default']['region'] = aws_region
    
    with open(config_path, 'w') as f:
        config.write(f)
    
    print("AWS credentials have been configured successfully!")

if __name__ == '__main__':
    setup_aws_credentials()
