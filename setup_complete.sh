#!/bin/bash

# Create VPC
echo "Creating VPC..."
VPC_ID=$(aws ec2 create-vpc \
    --cidr-block 10.0.0.0/16 \
    --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=matrix-vpc}]' \
    --query 'Vpc.VpcId' \
    --output text)

# Enable DNS hostnames in the VPC
aws ec2 modify-vpc-attribute \
    --vpc-id $VPC_ID \
    --enable-dns-hostnames "{\"Value\":true}"

# Create Internet Gateway
echo "Creating Internet Gateway..."
IGW_ID=$(aws ec2 create-internet-gateway \
    --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=matrix-igw}]' \
    --query 'InternetGateway.InternetGatewayId' \
    --output text)

# Attach Internet Gateway to VPC
aws ec2 attach-internet-gateway \
    --vpc-id $VPC_ID \
    --internet-gateway-id $IGW_ID

# Create public subnet
echo "Creating public subnet..."
PUBLIC_SUBNET_ID=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block 10.0.1.0/24 \
    --availability-zone us-east-1a \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=matrix-public-subnet}]' \
    --query 'Subnet.SubnetId' \
    --output text)

# Create private subnet
echo "Creating private subnet..."
PRIVATE_SUBNET_ID=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block 10.0.2.0/24 \
    --availability-zone us-east-1a \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=matrix-private-subnet}]' \
    --query 'Subnet.SubnetId' \
    --output text)

# Create route table for public subnet
echo "Creating route table..."
ROUTE_TABLE_ID=$(aws ec2 create-route-table \
    --vpc-id $VPC_ID \
    --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=matrix-public-rt}]' \
    --query 'RouteTable.RouteTableId' \
    --output text)

# Create route to Internet Gateway
aws ec2 create-route \
    --route-table-id $ROUTE_TABLE_ID \
    --destination-cidr-block 0.0.0.0/0 \
    --gateway-id $IGW_ID

# Associate route table with public subnet
aws ec2 associate-route-table \
    --subnet-id $PUBLIC_SUBNET_ID \
    --route-table-id $ROUTE_TABLE_ID

# Create security group for Redis
echo "Creating security group for Redis..."
REDIS_SG_ID=$(aws ec2 create-security-group \
    --group-name matrix-redis-sg \
    --description "Security group for Redis cluster" \
    --vpc-id $VPC_ID \
    --query 'GroupId' \
    --output text)

# Create security group for bastion host
echo "Creating security group for bastion..."
BASTION_SG_ID=$(aws ec2 create-security-group \
    --group-name matrix-bastion-sg \
    --description "Security group for bastion host" \
    --vpc-id $VPC_ID \
    --query 'GroupId' \
    --output text)

# Allow inbound Redis from bastion security group
aws ec2 authorize-security-group-ingress \
    --group-id $REDIS_SG_ID \
    --protocol tcp \
    --port 6379 \
    --source-group $BASTION_SG_ID

# Allow inbound SSH to bastion from anywhere
aws ec2 authorize-security-group-ingress \
    --group-id $BASTION_SG_ID \
    --protocol tcp \
    --port 22 \
    --cidr 0.0.0.0/0

# Create subnet group for Redis
echo "Creating subnet group for Redis..."
aws elasticache create-cache-subnet-group \
    --cache-subnet-group-name matrix-redis-subnet \
    --cache-subnet-group-description "Subnet group for Matrix Redis cluster" \
    --subnet-ids $PRIVATE_SUBNET_ID

# Create Redis cluster
echo "Creating Redis cluster..."
aws elasticache create-cache-cluster \
    --cache-cluster-id matrix-redis \
    --cache-node-type cache.t3.micro \
    --engine redis \
    --num-cache-nodes 1 \
    --cache-subnet-group-name matrix-redis-subnet \
    --security-group-ids $REDIS_SG_ID \
    --port 6379

# Wait for Redis cluster to be available
echo "Waiting for Redis cluster to be available..."
aws elasticache wait cache-cluster-available --cache-cluster-id matrix-redis

# Launch EC2 instance
echo "Launching bastion host..."
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id ami-0ac664bd64e1dcc6b \
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

# Get Redis endpoint
REDIS_ENDPOINT=$(aws elasticache describe-cache-clusters \
    --cache-cluster-id matrix-redis \
    --show-cache-node-info \
    --query 'CacheClusters[0].CacheNodes[0].Endpoint.Address' \
    --output text)

# Get bastion public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo "Setup complete!"
echo "VPC ID: $VPC_ID"
echo "Redis Security Group: $REDIS_SG_ID"
echo "Bastion Security Group: $BASTION_SG_ID"
echo "Bastion Instance ID: $INSTANCE_ID"
echo "Redis Endpoint: $REDIS_ENDPOINT"
echo "Bastion Public IP: $PUBLIC_IP"
