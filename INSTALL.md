# Installation and Third-Party Setup

This guide explains how to install and run the thesis artifact on Ubuntu or WSL Ubuntu.

## 1. Clone the Repository

```bash
git clone https://github.com/ramsainanduri/bms-zero-trust-sdn.git
cd bms-zero-trust-sdn
```

If you are using the local development copy created for the thesis, the repo is located at:

```text
/home/ram/dev/bms-zero-trust-sdn
```

## 2. Install System Packages

```bash
sudo apt update
sudo apt install -y git python3 mininet openvswitch-switch netcat-openbsd
```

## 3. Install POX

The controller is written for POX and OpenFlow 1.0.

```bash
mkdir -p ~/thesis
cd ~/thesis
git clone https://github.com/noxrepo/pox.git
```

## 4. Prepare the Controller

From the repository root:

```bash
cp controller.py ~/thesis/pox/ext/bms_controller.py
cd ~/thesis/pox
python pox.py bms_controller
```

Leave this terminal running.

## 5. Start Mininet

Open a second terminal and run:

```bash
cd /path/to/bms-zero-trust-sdn
bash mininet.sh
```

The script checks whether POX is listening on `127.0.0.1:6633`, cleans old Mininet state, handles common Open vSwitch recovery steps, and uses the OVS userspace datapath when running under WSL.

## 6. Run Test Scripts

Inside the Mininet CLI:

```text
source ping_test.mn
source advanced_test.mn
```

## 7. Review Evidence

The controller writes plain-text evidence to:

```text
/tmp/bms_controller_events.txt
```

Useful commands:

```bash
tail -n 120 /tmp/bms_controller_events.txt
grep "EVENT=QUARANTINE_APPLIED" /tmp/bms_controller_events.txt
grep "EVENT=AAA_AUTH_FAIL" /tmp/bms_controller_events.txt
```

## Notes for WSL

WSL may not provide a reliable Open vSwitch kernel datapath. The included `mininet.sh` detects WSL and selects:

```text
ovs,datapath=user,protocols=OpenFlow10
```

This is expected and does not invalidate the thesis experiment.
