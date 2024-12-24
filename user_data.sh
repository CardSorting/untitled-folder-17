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
