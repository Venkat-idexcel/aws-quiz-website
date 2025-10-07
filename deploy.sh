#!/bin/bash
# Deployment script for AWS Quiz Website on a Debian-based Linux (e.g., Ubuntu) EC2 instance.

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
# Replace with your actual values. Use environment variables in a real-world scenario.
# It's recommended to store these in a .env file and source it.
export SECRET_KEY='a-very-long-and-secure-random-string-for-production'
export DB_HOST='localhost' # This will be the local end of the SSH tunnel
export DB_PORT='5432'
export DB_NAME='cretificate_quiz_db'
export DB_USER='psql_master'
export DB_PASSWORD='LaS%J`ea&>7V2CR8C+P`'
export REDIS_URL='redis://localhost:6379/0'
export RATELIMIT_STORAGE_URL='redis://localhost:6379/1'
export FLASK_ENV='production'
export PORT='8000'

# OAuth Credentials (replace with your actual credentials)
export GOOGLE_CLIENT_ID='your-google-client-id'
export GOOGLE_CLIENT_SECRET='your-google-client-secret'
export GITHUB_CLIENT_ID='your-github-client-id'
export GITHUB_CLIENT_SECRET='your-github-client-secret'
export MICROSOFT_CLIENT_ID='your-microsoft-client-id'
export MICROSOFT_CLIENT_SECRET='your-microsoft-client-secret'

# SSH Tunnel Configuration
# The user of the EC2 instance (e.g., 'ubuntu', 'ec2-user')
TUNNEL_USER="ubuntu"
# The public IP or DNS of the PostgreSQL server
DB_SERVER_IP="your_postgres_server_ip"
# The path to your PEM file on the EC2 instance
PEM_FILE_PATH="/home/${TUNNEL_USER}/your_key.pem"

# Project directory
PROJECT_DIR=$(pwd)
VENV_DIR="$PROJECT_DIR/venv"

# --- Helper Functions ---
log() {
    echo "✅ [$(date +'%Y-%m-%d %H:%M:%S')] - $1"
}

# --- Deployment Steps ---

# 1. Update System Packages
log "Updating system packages..."
sudo apt-get update -y
sudo apt-get upgrade -y

# 2. Install System Dependencies
log "Installing system dependencies (Python, Nginx, Redis, Supervisor)..."
sudo apt-get install -y python3-venv python3-pip nginx redis-server supervisor

# 3. Create Python Virtual Environment
log "Creating Python virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv $VENV_DIR
fi
source $VENV_DIR/bin/activate

# 4. Install Python Dependencies
log "Installing Python dependencies from requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt

# 5. Set up SSH Tunnel for PostgreSQL
# This requires manual setup of the PEM file on the EC2 instance.
# We will create a systemd service for a persistent tunnel.
log "Setting up persistent SSH tunnel for PostgreSQL..."

# Ensure correct permissions for the PEM file
log "Please ensure '$PEM_FILE_PATH' exists and has 'chmod 400'."
# Example:
# sudo chmod 400 $PEM_FILE_PATH

# Create systemd service file for the SSH tunnel
sudo bash -c "cat > /etc/systemd/system/postgres-tunnel.service" << EOL
[Unit]
Description=SSH Tunnel for PostgreSQL
After=network.target

[Service]
User=${TUNNEL_USER}
# Restart the service if it fails
Restart=always
RestartSec=5
# The command to create the tunnel
# -N: Do not execute a remote command.
# -L: Forward local port to remote port.
ExecStart=/usr/bin/ssh -i ${PEM_FILE_PATH} -N -L ${DB_PORT}:${DB_HOST}:${DB_PORT} ${TUNNEL_USER}@${DB_SERVER_IP}
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOL

log "Enabling and starting the SSH tunnel service..."
sudo systemctl enable postgres-tunnel.service
sudo systemctl start postgres-tunnel.service
sudo systemctl status postgres-tunnel.service --no-pager

# 6. Initialize the Database
log "Initializing the database..."
# This command will run the init_database() function from your app
flask init-db

# 7. Set up Gunicorn with Supervisor
log "Configuring Supervisor to manage Gunicorn..."
sudo bash -c "cat > /etc/supervisor/conf.d/quiz_app.conf" << EOL
[program:quiz_app]
command=${VENV_DIR}/bin/gunicorn --config gunicorn_config.py 'app:create_app()'
directory=${PROJECT_DIR}
user=${USER}
autostart=true
autorestart=true
stderr_logfile=/var/log/quiz_app.err.log
stdout_logfile=/var/log/quiz_app.out.log
environment=SECRET_KEY='${SECRET_KEY}',DB_HOST='${DB_HOST}',DB_PORT='${DB_PORT}',DB_NAME='${DB_NAME}',DB_USER='${DB_USER}',DB_PASSWORD='${DB_PASSWORD}',REDIS_URL='${REDIS_URL}',RATELIMIT_STORAGE_URL='${RATELIMIT_STORAGE_URL}',FLASK_ENV='${FLASK_ENV}',PORT='${PORT}',GOOGLE_CLIENT_ID='${GOOGLE_CLIENT_ID}',GOOGLE_CLIENT_SECRET='${GOOGLE_CLIENT_SECRET}',GITHUB_CLIENT_ID='${GITHUB_CLIENT_ID}',GITHUB_CLIENT_SECRET='${GITHUB_CLIENT_SECRET}',MICROSOFT_CLIENT_ID='${MICROSOFT_CLIENT_ID}',MICROSOFT_CLIENT_SECRET='${MICROSOFT_CLIENT_SECRET}'
EOL

# 8. Set up Nginx as a Reverse Proxy
log "Configuring Nginx as a reverse proxy..."
sudo bash -c "cat > /etc/nginx/sites-available/quiz_app" << EOL
server {
    listen 80;
    server_name your_domain_or_ec2_ip; # Replace with your domain or IP

    location / {
        proxy_pass http://127.0.0.1:${PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias ${PROJECT_DIR}/static;
        expires 30d;
    }
}
EOL

# Enable the Nginx site
if [ -L /etc/nginx/sites-enabled/quiz_app ]; then
    sudo rm /etc/nginx/sites-enabled/quiz_app
fi
sudo ln -s /etc/nginx/sites-available/quiz_app /etc/nginx/sites-enabled
# Remove default Nginx site if it exists
if [ -L /etc/nginx/sites-enabled/default ]; then
    sudo rm /etc/nginx/sites-enabled/default
fi

# 9. Restart Services
log "Restarting Supervisor and Nginx..."
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart quiz_app
sudo systemctl restart nginx

# --- Deployment Complete ---
log "Deployment complete!"
log "Your application should be accessible at http://your_domain_or_ec2_ip"
log "Check Supervisor status with: sudo supervisorctl status"
log "Check Nginx status with: sudo systemctl status nginx"
