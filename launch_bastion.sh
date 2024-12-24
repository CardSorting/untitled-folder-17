#!/bin/bash

# Set the region
export AWS_DEFAULT_REGION=us-west-2

# Use Amazon Linux 2 AMI for us-west-2
AMI_ID="ami-06c7fbd87fa7b507c"  # Amazon Linux 2 AMI in us-west-2

# Get Redis cluster info
REDIS_INFO=$(aws elasticache describe-cache-clusters \
    --cache-cluster-id matrix-redis \
    --show-cache-node-info)

# Get VPC ID from the security group
REDIS_SG_ID=$(echo "$REDIS_INFO" | grep -o '"SecurityGroupId": "[^"]*"' | cut -d'"' -f4)
VPC_ID=$(aws ec2 describe-security-groups \
    --group-ids "$REDIS_SG_ID" \
    --query 'SecurityGroups[0].VpcId' \
    --output text)

echo "Found VPC ID: $VPC_ID"

# Create a new security group with a unique name
TIMESTAMP=$(date +%s)
SG_NAME="matrix-bastion-sg-$TIMESTAMP"

echo "Creating new security group: $SG_NAME"
BASTION_SG_ID=$(aws ec2 create-security-group \
    --group-name "$SG_NAME" \
    --description "Security group for bastion host" \
    --vpc-id "$VPC_ID" \
    --query 'GroupId' \
    --output text)

# Add SSH ingress rule
aws ec2 authorize-security-group-ingress \
    --group-id "$BASTION_SG_ID" \
    --protocol tcp \
    --port 22 \
    --cidr 0.0.0.0/0

# Get public subnet in us-west-2a
PUBLIC_SUBNET_ID=$(aws ec2 describe-subnets \
    --filters "Name=vpc-id,Values=$VPC_ID" "Name=availability-zone,Values=us-west-2a" \
    --query 'Subnets[0].SubnetId' \
    --output text)

echo "Using VPC: $VPC_ID"
echo "Using Security Group: $BASTION_SG_ID"
echo "Using Subnet: $PUBLIC_SUBNET_ID"

echo "Launching bastion host..."
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $AMI_ID \
    --instance-type t2.micro \
    --subnet-id $PUBLIC_SUBNET_ID \
    --security-group-ids $BASTION_SG_ID \
    --associate-public-ip-address \
    --iam-instance-profile Name=matrix-ssm-profile \
    --user-data '#!/bin/bash
yum update -y
yum install -y redis
' \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=matrix-bastion}]' \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "Waiting for instance to be running..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# Get the instance public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo "Bastion host is ready!"
echo "Instance ID: $INSTANCE_ID"
echo "Public IP: $PUBLIC_IP"
echo "Redis Endpoint: matrix-redis.oo6rj9.0001.usw2.cache.amazonaws.com"
