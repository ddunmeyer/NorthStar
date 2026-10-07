#!/bin/bash
# First-boot setup for the North Star demo server (Amazon Linux 2023).
# deploy.py passes this to EC2 as user data after filling in the __PLACEHOLDERS__.
#
# The app runs as a systemd service, so it comes back by itself every time the
# EC2 scheduler starts the instance. No AWS keys are stored here: the app uses
# the instance's IAM role.
set -euxo pipefail

dnf install -y python3.12 python3.12-pip git
useradd --system --create-home --home-dir /home/northstar northstar || true

git clone __REPO_URL__ /opt/northstar
python3.12 -m venv /opt/northstar/.venv
/opt/northstar/.venv/bin/pip install --upgrade pip
/opt/northstar/.venv/bin/pip install -r /opt/northstar/requirements.txt

cat > /opt/northstar/.env <<'EOF'
AWS_REGION=__REGION__
NORTHSTAR_MODEL_ID=__MODEL_ID__
NORTHSTAR_TABLE=__TABLE__
NORTHSTAR_KB_ID=__KB_ID__
EOF
chown -R northstar:northstar /opt/northstar

cat > /etc/systemd/system/northstar.service <<'EOF'
[Unit]
Description=North Star Streamlit app
After=network-online.target
Wants=network-online.target

[Service]
User=northstar
WorkingDirectory=/opt/northstar
# Pick up the latest main on every start. A leading "-" means a failure here doesn't block the app.
ExecStartPre=-/usr/bin/git -C /opt/northstar pull --ff-only
ExecStartPre=-/opt/northstar/.venv/bin/pip install -q -r /opt/northstar/requirements.txt
ExecStart=/opt/northstar/.venv/bin/python -m streamlit run app.py --server.port 80 --server.address 0.0.0.0 --server.headless true
# Lets the unprivileged user listen on port 80 without running the app as root.
AmbientCapabilities=CAP_NET_BIND_SERVICE
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now northstar
