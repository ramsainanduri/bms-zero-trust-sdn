# BACnet Architecture Short Summary

## GitHub Repository Reference

The implementation and supporting documentation for this thesis artifact are packaged in the following repository:

```text
https://github.com/ramsainanduri/bms-zero-trust-sdn
```

This repository should be referenced in the thesis text as the reproducible source for the controller, Mininet topology, test scripts, documentation, and architecture flowcharts. Large BACnet dataset analysis files are kept outside the code repository.

## Thesis Idea

This thesis proposes a Zero Trust-inspired SDN architecture for securing Building Management System (BMS) communication. The design is based on observations from a BACnet attack dataset and is implemented as a proof-of-concept testbed using Mininet, Open vSwitch, and a POX controller.

## Why BACnet Dataset Analysis Was Used

The BACnet dataset shows that BMS attacks can be stealthy. In the normal traffic, one central device, `172.120.236.70`, communicates with four field devices using BACnet/IP over UDP port `47808`. The traffic mainly contains discovery and read operations such as `Who-Is`, `I-Am`, `ReadProperty`, and `ReadPropertyMultiple`.

The important observation is that no `WriteProperty` commands were seen in the falsifying and modifying attack traces. This means the attack does not look like direct control or obvious network abuse. Instead, legitimate BACnet read requests and responses are used while the reported physical values are changed. Direct PCAP counting also showed that the attack traces are dominated by `ReadPropertyMultiple`, while normal traffic contains mostly `ReadProperty`.

## Attack Meaning

The falsifying and modifying chiller scenarios are best understood as stealthy False Data Injection (FDI) or data-integrity attacks.

In the falsifying attack, the chilled water supply temperature is changed by about 4-5 degrees Celsius. In the modifying attack, pump on/off states are inverted. The traffic can still look normal at the protocol level, but the physical meaning of the data is false.

This is dangerous because the supervisory BMS may make wrong cooling or equipment decisions while the network packets still appear legitimate.

## Why Two Devices Receive Many Requests

Two field devices, `172.120.236.60` and `172.120.236.62`, receive many repeated requests. However, after checking the PCAP files directly, this should not be treated as attack evidence by itself because these two devices are also the most heavily queried devices in normal traffic.

The better explanation is that these two devices are high-priority process-point devices in the simulated BMS. Since the attack scenarios are about chiller temperature and pump status, these devices likely contain important BACnet objects related to the chiller process.

The attack evidence is therefore not simply "many requests to two devices." The stronger evidence is:

| Evidence | Meaning |
|---|---|
| `.60` and `.62` are highly queried in normal and attack traffic | They are likely important process-point devices |
| Falsifying and modifying traces have higher read intensity than normal | Behaviour changes compared with the baseline |
| Attack traces are dominated by `ReadPropertyMultiple` | The read pattern changes while still using legitimate BACnet services |
| No `WriteProperty` commands are observed | The attack is not direct command-based control |

This makes the attack stealthy: the communication structure remains mostly legitimate, but the truth of the reported process data is changed.

## Why the Architecture Is Needed

The dataset shows that static security is not enough. Checking only IP address, MAC address, protocol, or port cannot detect attacks where the packet format is normal but the content or behaviour is malicious.

Therefore, the proposed architecture uses multiple layers:

| Layer | Purpose |
|---|---|
| AAA | Verifies device identity using registered IP, MAC, and session state |
| Zero Trust risk scoring | Checks runtime behaviour, trust, context, previous denials, and traffic patterns |
| ABAC | Enforces least-privilege rules based on role, device type, subsystem, trust, and context |
| SDN/OpenFlow | Dynamically allows or blocks traffic in the switch |
| Quarantine | Isolates devices after repeated suspicious behaviour |

## Testbed Implementation

The implementation uses a small Mininet topology:

```text
                    POX Controller
                          |
                         s1
          /        /       |       \        \
        h1        h2       h3       h4       h5
```

Each host represents a BMS device:

| Host | Role |
|---|---|
| h1 | BMS/HVAC controller |
| h2 | HVAC sensor |
| h3 | Lighting controller |
| h4 | Lighting sensor with unknown trust |
| h5 | External or abnormal device |

Open vSwitch acts as the SDN switch. The POX controller receives new flows, verifies the source device, calculates risk, checks ABAC policy, and installs allow or drop rules.

## What the Tests Show

The testbed does not aim for every ping to succeed. Some failed pings are expected because they prove that the controller is enforcing policy.

The tests show that:

| Test behaviour | Security meaning |
|---|---|
| Allowed traffic | Expected BMS communication is permitted |
| Denied cross-system traffic | Segmentation is enforced |
| Denied sensor-to-sensor traffic | Lateral movement is restricted |
| Repeated denied attempts | Suspicious behaviour is detected |
| Quarantine event | The architecture can contain abnormal devices |
| UDP `47808` validation | BACnet-representative traffic can be recognised |

## Main Justification

The BACnet dataset proves that BMS attacks can remain hidden inside legitimate-looking communication. The testbed demonstrates how a Zero Trust-inspired SDN controller can respond by combining identity verification, runtime risk, least-privilege ABAC policy, dynamic OpenFlow enforcement, and quarantine.

In short, the contribution is not only analysing BACnet attacks, but using that analysis to justify and build a working security architecture for BMS communication.
