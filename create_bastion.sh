#!/bin/bash

# Launch EC2 instance in the same VPC as your Redis cluster
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id ami-0c55b159cbfafe1f0 \
    --instance-type t2.micro \
    --security-group-ids sg-0a44a2b5e251c45ba \
    --iam-instance-profile Name=matrix-ssm-profile \
    --user-data '#!/bin/bash
yum update -y
yum install -y redis
' \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=matrix-bastion}]' \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "Created bastion host with ID: $INSTANCE_ID"
echo "Waiting for instance to be ready..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# Get the instance public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo "Bastion host is ready!"
echo "Instance ID: $INSTANCE_ID"
echo "Public IP: $PUBLIC_IP"
