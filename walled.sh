#!/bin/bash
NS=ai
ip netns del $NS 2>/dev/null
ip netns add $NS
ip netns exec $NS ip link set lo up
rm -f /tmp/ai.sock

# Start the brain
ip netns exec $NS llama-server -m /home/zero/ollama-models/Qwen3-4B-OBLITERATED.Q4_K_M.gguf --host 127.0.0.1 --port 8080 --threads 3 --ctx-size 4096 >/var/log/walled-llama.log 2>&1 &

# Wait for the brain to wake up
for i in $(seq 1 30); do
  ip netns exec $NS bash -c 'echo > /dev/tcp/127.0.0.1/8080' 2>/dev/null && break
  sleep 1
done

# Build the mail slot in the background
rm -f /tmp/ai.sock
ip netns exec $NS socat UNIX-LISTEN:/tmp/ai.sock,fork TCP:127.0.0.1:8080 &
SOCAT_PID=$!

# Unlock the door for the cashier
sleep 1
chmod 777 /tmp/ai.sock

# Keep the script alive
wait $SOCAT_PID
