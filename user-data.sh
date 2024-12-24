#!/bin/bash
yum update -y
yum install -y python3 python3-pip
pip3 install redis
cd /tmp
sudo yum install -y https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/linux_amd64/amazon-ssm-agent.rpm
sudo systemctl enable amazon-ssm-agent
sudo systemctl start amazon-ssm-agent
python3 -c "import redis; r = redis.from_url('redis://matrix-redis.oo6rj9.0001.usw2.cache.amazonaws.com:6379'); print(r.ping())" > /tmp/redis-test.log 2>&1
