# BMS Zero Trust SDN

This repository contains the implementation and supporting evidence for a thesis proof of concept:

> A Zero Trust-inspired Software-Defined Networking architecture for Building Management System security.

GitHub repository:

```text
https://github.com/ramsainanduri/bms-zero-trust-sdn
```

## What This Project Contains

This code artifact contains the SDN controller, Mininet topology scripts, test scripts, documentation, and flowcharts. The large BACnet dataset analysis files are intentionally not included in this repository.

The thesis uses the BACnet analysis as motivation: building-management attacks can remain hidden inside legitimate-looking BACnet/IP communication. This testbed demonstrates how identity verification, Zero Trust risk assessment, ABAC policy, rate limiting, and quarantine can be enforced centrally.

## Repository Contents

| Path | Purpose |
|---|---|
| `controller.py` | POX OpenFlow controller implementing AAA, Zero Trust risk scoring, ABAC, rate limiting, quarantine, logging, and OpenFlow enforcement |
| `mininet.sh` | Starts the five-host Mininet topology and connects it to POX |
| `ping_test.mn` | Baseline test sequence T01-T12 |
| `advanced_test.mn` | Advanced validation for spoofing, unknown identity, UDP/47808, timing delta, off-hours context, flow-table inspection, and quarantine |
| `Documentation.md` | Full experiment documentation and architecture explanation |
| `BACnet_data_analysis.md` | Thesis-side summary explaining how the BACnet dataset motivated the architecture |
| `BACnet_Architecture_Short_Summary.md` | Short thesis-facing summary |
| `QA.md` | Thesis defense question-and-answer preparation |
| `zero_trust_sdn_flowchart.svg` | Architecture decision-flow diagram |
| `zero_trust_scenario_flowchart.svg` | Scenario/test-flow diagram |

## Architecture Summary

When a new flow reaches the switch, Open vSwitch sends a `PacketIn` event to the POX controller. The controller applies the following sequence:

```text
PacketIn
  -> AAA identity/session validation
  -> destination registry validation
  -> Zero Trust runtime risk assessment
  -> rate-limit and quarantine checks
  -> ABAC least-privilege policy
  -> OpenFlow allow/drop rule installation
  -> evidence logging
```

The topology is intentionally small and explainable:

```text
                    POX Controller
                          |
                         s1
          /        /       |       \        \
        h1        h2       h3       h4       h5
```

| Host | Role |
|---|---|
| h1 | BMS/HVAC controller |
| h2 | HVAC sensor |
| h3 | Lighting controller |
| h4 | Lighting sensor with unknown trust |
| h5 | External or abnormal device |

## Quick Start

See [INSTALL.md](INSTALL.md) for setup instructions and [TESTING.md](TESTING.md) for the full validation workflow.

The short version is:

```bash
cp controller.py ~/thesis/pox/ext/bms_controller.py
cd ~/thesis/pox
python pox.py bms_controller
```

In a second terminal:

```bash
cd /path/to/bms-zero-trust-sdn
bash mininet.sh
```

Inside the Mininet CLI:

```text
source ping_test.mn
source advanced_test.mn
```

Controller evidence is written to:

```text
/tmp/bms_controller_events.txt
```

## Thesis Citation

Use this repository in the thesis text as the implementation artifact:

```text
Sainanduri, R. BMS Zero Trust SDN.
GitHub: https://github.com/ramsainanduri/bms-zero-trust-sdn
```
