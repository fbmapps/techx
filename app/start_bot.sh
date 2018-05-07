#!/bin/bash
echo "Starting Techx.Bot Listener..."
nohup gunicorn -w 4 -b 0.0.0.0:5105 app:app &

echo "Process ID..."
ps -ax | grep gunicorn

