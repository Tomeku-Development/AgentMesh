#!/bin/bash
# FoxMQ cluster setup script for MESH demo
set -e

FOXMQ_BIN="${FOXMQ_BIN:-./foxmq}"
DATA_DIR="${DATA_DIR:-./foxmq.d}"
NUM_NODES="${NUM_NODES:-4}"
BASE_MQTT_PORT="${BASE_MQTT_PORT:-1883}"
BASE_CLUSTER_PORT="${BASE_CLUSTER_PORT:-19793}"

echo "=== MESH FoxMQ Cluster Setup ==="
echo "Nodes: $NUM_NODES"
echo "MQTT ports: $BASE_MQTT_PORT-$((BASE_MQTT_PORT + NUM_NODES - 1))"

# Generate address book
ADDR_LIST=""
for i in $(seq 0 $((NUM_NODES - 1))); do
    PORT=$((BASE_CLUSTER_PORT + i))
    if [ -z "$ADDR_LIST" ]; then
        ADDR_LIST="127.0.0.1:$PORT"
    else
        ADDR_LIST="$ADDR_LIST,127.0.0.1:$PORT"
    fi
done

echo "Generating address book: $ADDR_LIST"
$FOXMQ_BIN address-book from-range 127.0.0.1 $BASE_CLUSTER_PORT $((BASE_CLUSTER_PORT + NUM_NODES - 1))

# Create agent users
AGENTS=("buyer" "supplier_a" "supplier_b" "logistics" "inspector" "oracle" "bridge")
for agent in "${AGENTS[@]}"; do
    echo "Creating user: $agent"
    $FOXMQ_BIN user add "$agent" 2>/dev/null || true
done

echo ""
echo "=== Setup Complete ==="
echo "Start nodes with:"
for i in $(seq 0 $((NUM_NODES - 1))); do
    echo "  $FOXMQ_BIN run --secret-key-file=$DATA_DIR/key_$i.pem --mqtt-port=$((BASE_MQTT_PORT + i))"
done
