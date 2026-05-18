#!/usr/bin/env bash
set -euo pipefail

# Start the POX controller in another terminal:
#   cd ~/thesis/pox
#   cp /path/to/bms-zero-trust-sdn/controller.py ext/bms_controller.py
#   python pox.py bms_controller

OVS_RUN_DIR=/var/run/openvswitch
OVS_DB_SOCK="$OVS_RUN_DIR/db.sock"
SWITCH_OPTS="ovsk,protocols=OpenFlow10"
IS_WSL=0

if grep -qi microsoft /proc/version 2>/dev/null; then
    IS_WSL=1
    # WSL often lacks a usable OVS kernel datapath. Userspace datapath is more
    # reliable for repeat Mininet runs after the first exit.
    SWITCH_OPTS="ovs,datapath=user,protocols=OpenFlow10"
fi

# Mininet cleanup can hang when OVS has a stale db socket/pid state. Keep it
# bounded so the explicit OVS recovery below can still run.
if ! timeout 20s sudo mn -c; then
    echo "Warning: 'mn -c' timed out or failed; continuing with explicit OVS cleanup." >&2
fi

# If db.sock was deleted while ovsdb-server was still running, OVS can have a
# stale pid/ctl file but no database socket. Restarting the service is the
# cleanest recovery path on normal Ubuntu installs. On WSL, systemd service
# dependencies often fail even when manually started OVS works.
if [ "$IS_WSL" -eq 0 ] && command -v service >/dev/null 2>&1 && [ -d /run/systemd/system ]; then
    sudo service openvswitch-switch restart || true
fi

if [ ! -S "$OVS_DB_SOCK" ]; then
    sudo pkill ovs-vswitchd 2>/dev/null || true
    sudo pkill ovsdb-server 2>/dev/null || true
    sudo rm -f "$OVS_RUN_DIR"/db.sock \
               "$OVS_RUN_DIR"/ovsdb-server.pid \
               "$OVS_RUN_DIR"/ovs-vswitchd.pid \
               "$OVS_RUN_DIR"/*.ctl
    sudo mkdir -p "$OVS_RUN_DIR"

    sudo ovsdb-server /etc/openvswitch/conf.db \
        --remote=punix:"$OVS_DB_SOCK" \
        --remote=db:Open_vSwitch,Open_vSwitch,manager_options \
        --pidfile --detach

    sudo ovs-vsctl --no-wait init
fi

if ! pgrep -x ovs-vswitchd >/dev/null 2>&1; then
    sudo rm -f "$OVS_RUN_DIR"/ovs-vswitchd.pid "$OVS_RUN_DIR"/ovs-vswitchd.*.ctl
    sudo ovs-vswitchd unix:"$OVS_DB_SOCK" --pidfile --detach
fi

if ! timeout 2 bash -c '</dev/tcp/127.0.0.1/6633' 2>/dev/null; then
    echo "POX is not listening on 127.0.0.1:6633. Start it before running Mininet." >&2
    exit 1
fi

# Creating the testbed setup
sudo mn --topo single,5 --mac --switch "$SWITCH_OPTS" --controller=remote,ip=127.0.0.1,port=6633


######################################################################################################
# OUTPUT SHOULD LOOK LIKE THIS
# 2026-04-29T13:48:42Z|00001|ovs_numa|INFO|Discovered 8 CPU cores on NUMA node 0
# 2026-04-29T13:48:42Z|00002|ovs_numa|INFO|Discovered 1 NUMA nodes and 8 CPU cores
# 2026-04-29T13:48:42Z|00003|reconnect|INFO|unix:/var/run/openvswitch/db.sock: connecting...
# 2026-04-29T13:48:42Z|00004|reconnect|INFO|unix:/var/run/openvswitch/db.sock: connected
# 2026-04-29T13:48:42Z|00005|dpif_netlink|INFO|Generic Netlink family 'ovs_datapath' does not exist. The Open vSwitch kernel module is probably not loaded.
# *** Creating network
# *** Adding controller
# *** Adding hosts:
# h1 h2 h3 h4 h5
# *** Adding switches:
# s1
# *** Adding links:
# (h1, s1) (h2, s1) (h3, s1) (h4, s1) (h5, s1)
# *** Configuring hosts
# h1 h2 h3 h4 h5
# *** Starting controller
# c0
# *** Starting 1 switches
# s1 ...
# *** Starting CLI:
