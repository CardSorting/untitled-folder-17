#!/bin/bash

# Set the region
export AWS_DEFAULT_REGION=us-west-2

# Enable error handling
set -e
set -o pipefail

# Get Redis cluster info to find VPC and security group
REDIS_INFO=$(aws elasticache describe-cache-clusters \
    --cache-cluster-id matrix-redis \
    --show-cache-node-info)

# Get Redis security group
REDIS_SG_ID=$(echo "$REDIS_INFO" | grep -o '"SecurityGroupId": "[^"]*"' | cut -d'"' -f4)

# Get VPC ID
VPC_ID=$(aws ec2 describe-security-groups \
    --group-ids "$REDIS_SG_ID" \
    --query 'SecurityGroups[0].VpcId' \
    --output text)

echo "Found VPC ID: $VPC_ID"

# Create security group for the dev environment
TIMESTAMP=$(date +%s)
DEV_SG_NAME="matrix-dev-sg-$TIMESTAMP"

echo "Creating security group: $DEV_SG_NAME"
DEV_SG_ID=$(aws ec2 create-security-group \
    --group-name "$DEV_SG_NAME" \
    --description "Security group for Matrix development environment" \
    --vpc-id "$VPC_ID" \
    --query 'GroupId' \
    --output text)

# Allow inbound HTTP
aws ec2 authorize-security-group-ingress \
    --group-id "$DEV_SG_ID" \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0

# Allow inbound HTTPS
aws ec2 authorize-security-group-ingress \
    --group-id "$DEV_SG_ID" \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0

# Allow inbound Flask development port
aws ec2 authorize-security-group-ingress \
    --group-id "$DEV_SG_ID" \
    --protocol tcp \
    --port 5000 \
    --cidr 0.0.0.0/0

# Get public subnet in us-west-2a
PUBLIC_SUBNET_ID=$(aws ec2 describe-subnets \
    --filters "Name=vpc-id,Values=$VPC_ID" "Name=availability-zone,Values=us-west-2a" \
    --query 'Subnets[0].SubnetId' \
    --output text)

# Use Amazon Linux 2 AMI
AMI_ID="ami-06c7fbd87fa7b507c"

# Create user data script
cat << 'EOF' > user_data.sh
#!/bin/bash
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

echo "Starting user data script execution..."

# Install required packages
echo "Installing packages..."
yum update -y
yum install -y python3-pip python3-devel git nginx
pip3 install virtualenv

# Install development tools
yum groupinstall -y "Development Tools"

# Clone the repository
echo "Cloning repository..."
cd /home/ec2-user
git clone https://github.com/CardSorting/untitled-folder-17.git -b chatversion matrix-app
chown -R ec2-user:ec2-user matrix-app

# Set up virtual environment
echo "Setting up virtual environment..."
cd matrix-app
python3 -m virtualenv .venv
source .venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create systemd service for the Flask app
echo "Creating systemd service..."
cat << 'SERVICE' > /etc/systemd/system/matrix.service
[Unit]
Description=Matrix Flask Application
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/matrix-app
Environment="PATH=/home/ec2-user/matrix-app/.venv/bin"
Environment="FLASK_APP=app.py"
Environment="REDIS_URL=redis://matrix-redis.oo6rj9.0001.usw2.cache.amazonaws.com:6379"
Environment="CHAT_REDIS_URL=redis://matrix-redis.oo6rj9.0001.usw2.cache.amazonaws.com:6379"
ExecStart=/home/ec2-user/matrix-app/.venv/bin/flask run --host=0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
SERVICE

# Configure nginx
echo "Configuring nginx..."
cat << 'NGINX' > /etc/nginx/conf.d/matrix.conf
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
NGINX

# Remove default nginx config
rm -f /etc/nginx/conf.d/default.conf

# Start and enable services
echo "Starting services..."
systemctl daemon-reload
systemctl start matrix
systemctl enable matrix
systemctl start nginx
systemctl enable nginx

echo "User data script completed!"
EOF

echo "Launching development instance..."
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $AMI_ID \
    --instance-type t2.micro \
    --subnet-id $PUBLIC_SUBNET_ID \
    --security-group-ids $DEV_SG_ID \
    --associate-public-ip-address \
    --iam-instance-profile Name=matrix-dev-profile \
    --user-data file://user_data.sh \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=matrix-dev}]' \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "Waiting for instance to be running..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# Get the instance public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo "Development environment is being set up!"
echo "Instance ID: $INSTANCE_ID"
echo "Public IP: $PUBLIC_IP"
echo "Access your application at: http://$PUBLIC_IP"
echo ""
echo "The instance is still being configured. Wait a few minutes for the setup to complete."
echo "You can check the setup progress by connecting to the instance and running:"
echo "sudo tail -f /var/log/user-data.log"
