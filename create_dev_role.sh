#!/bin/bash

# Create the IAM role
aws iam create-role \
    --role-name matrix-dev-role \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "ec2.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }'

# Attach SSM policy for session management
aws iam attach-role-policy \
    --role-name matrix-dev-role \
    --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore

# Attach ElastiCache policy
aws iam attach-role-policy \
    --role-name matrix-dev-role \
    --policy-arn arn:aws:iam::590184106837:policy/matrix-elasticache-policy

# Create instance profile
aws iam create-instance-profile \
    --instance-profile-name matrix-dev-profile

# Add role to instance profile
aws iam add-role-to-instance-profile \
    --instance-profile-name matrix-dev-profile \
    --role-name matrix-dev-role
