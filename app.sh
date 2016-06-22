#!/usr/bin/env bash

trap 'kill -TERM $PID' TERM INT

gunicorn --bind $OPENSHIFT_PYTHON_IP:$OPENSHIFT_PYTHON_PORT wsgi:app

PID=$!
wait $PID
trap - TERM INT
wait $PID
STATUS=$?

exit $STATUS
