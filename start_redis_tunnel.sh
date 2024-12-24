#!/bin/bash

# Get the instance ID
INSTANCE_ID=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=matrix-bastion" \
  --query "Reservations[].Instances[?State.Name=='running'].InstanceId[]" \
  --output text)

if [ -z "$INSTANCE_ID" ]; then
    echo "Error: Could not find running instance with name 'matrix-bastion'"
    exit 1
fi

# Start the port forwarding session
aws ssm start-session \
    --target "$INSTANCE_ID" \
    --document-name AWS-StartPortForwardingSessionToRemoteHost \
    --parameters "{\"host\":[\"matrix-redis.oo6rj9.0001.usw2.cache.amazonaws.com\"],\"portNumber\":[\"6379\"],\"localPortNumber\":[\"6379\"]}"
