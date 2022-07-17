#!/bin/bash
echo "Starting unoserver..."
python3 -m unoserver.server --port 2002 --executable /usr/bin/soffice &

echo "Starting processing server..."
cd server
python3 -m uvicorn server:app --reload --host 0.0.0.0 --port 3000 &
# Wait for any process to exit
wait -n
# Exit with status of process that exited first
exit $?