#!/bin/sh

echo "Starting frpc with token: $FRP_TOKEN"
echo "FRPC_CONFIG: $FRPC_CONFIG"

if [ -z "$FRPC_TOKEN" ]; then
  echo "FRPC_TOKEN environment variable is not set. Exiting."
  exit 1
fi
sed -i "s/token = ''/token = '$FRPC_TOKEN'/g" $FRPC_CONFIG
exec frpc -c $FRPC_CONFIG