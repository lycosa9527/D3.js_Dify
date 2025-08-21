#!/bin/bash
# MindGraph Logs Directory Setup Script for Ubuntu/Linux
# Creates the logs directory and sets proper permissions for Gunicorn logging

echo "🔧 Setting up MindGraph logs directory..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS_DIR="$SCRIPT_DIR/logs"

echo "📁 Script directory: $SCRIPT_DIR"
echo "📁 Logs directory: $LOGS_DIR"

# Create logs directory if it doesn't exist
if [ ! -d "$LOGS_DIR" ]; then
    mkdir -p "$LOGS_DIR"
    echo "✅ Created logs directory: $LOGS_DIR"
else
    echo "📁 Logs directory already exists: $LOGS_DIR"
fi

# Create log files if they don't exist
LOG_FILES=("gunicorn_access.log" "gunicorn_error.log" "gunicorn.pid" "app.log" "agent.log")

for log_file in "${LOG_FILES[@]}"; do
    log_path="$LOGS_DIR/$log_file"
    if [ ! -f "$log_path" ]; then
        touch "$log_path"
        echo "📝 Created log file: $log_file"
    else
        echo "📝 Log file exists: $log_file"
    fi
done

# Set proper permissions (755 for directory, 644 for files)
chmod 755 "$LOGS_DIR"
echo "🔐 Set directory permissions: $(stat -c %a "$LOGS_DIR")"

# Set file permissions
for log_file in "${LOG_FILES[@]}"; do
    log_path="$LOGS_DIR/$log_file"
    if [ -f "$log_path" ]; then
        chmod 644 "$log_path"
        echo "🔐 Set file permissions for $log_file: $(stat -c %a "$log_path")"
    fi
done

echo ""
echo "✅ Logs directory setup completed successfully!"
echo "📁 You can now run: python run_server.py"
