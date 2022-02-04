#!/usr/bin/env bash

set +e

echo "Start Server"
python ./server.py &
server_pid=$!
echo

sleep 1

echo "Start NPC"
python ./npc.py &
npc_pid=$!
echo


function shutdown() {
	echo "Shutdown NPC"
	kill $npc_pid
	echo
	sleep 5
	echo "Shutdown Server"
	kill $server_pid
	echo
}

trap shutdown SIGINT


wait $server_pid
