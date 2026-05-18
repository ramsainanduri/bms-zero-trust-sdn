# Experiment Documentation: Proposed Zero Trust-Inspired Software-Defined Networking (SDN) Architecture for Building Management System (BMS) Security

## Code Repository

The implementation artifact for this thesis is maintained as a GitHub repository:

```text
https://github.com/ramsainanduri/bms-zero-trust-sdn
```

The repository contains the POX controller, Mininet scripts, flowcharts, installation instructions, and repeatable test documentation. Large BACnet analysis scripts and generated result files are kept outside the public code repository because they are thesis-side evidence rather than runtime code.

## Abbreviations

| Abbreviation | Full form | Meaning in this experiment |
|---|---|---|
| AAA | Authentication, Authorisation, and Accounting | Verifies device identity, maintains sessions, and records authentication events |
| ABAC | Attribute-Based Access Control | Makes access decisions using attributes such as role, trust, system, and context |
| ARP | Address Resolution Protocol | Resolves IP addresses to MAC addresses inside the simulated network |
| BACnet | Building Automation and Control Network | BMS communication protocol represented in the controller by UDP port 47808 |
| BMS | Building Management System | The building-control environment being simulated |
| CLI | Command-Line Interface | Terminal interface used to run Mininet commands |
| HVAC | Heating, Ventilation, and Air Conditioning | One of the simulated BMS subsystems |
| ICMP | Internet Control Message Protocol | Protocol used by `ping` for connectivity tests |
| IP | Internet Protocol | Network-layer addressing used by the Mininet hosts |
| MAC | Media Access Control | Link-layer address used for device identity checks |
| OVS | Open vSwitch | Software switch used by Mininet |
| POX | Python-based OpenFlow controller | SDN controller framework used for the custom controller |
| RADIUS | Remote Authentication Dial-In User Service | Example external AAA server technology |
| SDN | Software-Defined Networking | Networking approach that separates the control plane from the data plane |
| TACACS+ | Terminal Access Controller Access-Control System Plus | Example external AAA server technology |
| UDP | User Datagram Protocol | Transport protocol used to represent BACnet-style traffic |
| VM | Virtual Machine | Full virtualised Linux environment, mentioned as an alternative to WSL |
| WSL | Windows Subsystem for Linux | Ubuntu environment used to run the experiment |
| ZT | Zero Trust | Security model based on continuous verification and least privilege |

## 1. Aim of the Experiment

The purpose of this experiment is to design and evaluate a proposed Zero Trust-inspired Software-Defined Networking (SDN) architecture for securing communication in a simulated Building Management System (BMS) network.

Building systems commonly include controllers, sensors, actuators, and external maintenance devices. These devices often communicate over flat or weakly segmented networks. If a device is compromised, misconfigured, or unauthorised, it may be able to communicate with systems that it should not access. The experiment addresses this problem by placing access-control logic in the SDN controller instead of relying only on static network configuration.

The experiment implements Zero Trust as an overall access-control model. Authentication, Authorisation, and Accounting (AAA) is not treated as a separate replacement for Zero Trust; it is the first verification step inside the Zero Trust flow when a packet reaches the controller.

| Zero Trust layer | Purpose in this experiment |
|---|---|
| 1. Authentication, Authorisation, and Accounting (AAA) | First verification layer: identify the source device using registered Internet Protocol (IP) and Media Access Control (MAC) address, maintain sessions, and log authentication events |
| 2. Zero Trust (ZT) risk assessment | Continuously score each authenticated flow using trust, context, previous denials, requested destination, and traffic behaviour |
| 3. Rate and quarantine checks | Block sources that exceed traffic limits or have already been isolated |
| 4. Attribute-Based Access Control (ABAC) | Apply least-privilege access policy using role, device type, BMS system, trust level, and context |
| 5. Behavioural response | Detect repeated denied attempts, revoke sessions, and quarantine suspicious devices |

The contribution of this thesis is the integration of these mechanisms into one BMS-focused architecture. SDN provides centralised enforcement, AAA provides verified device identity, Zero Trust provides continuous verification, ABAC provides fine-grained least-privilege policy decisions, and behavioural tracking provides quarantine and response.

The expected outcome is not that every ping succeeds. In this experiment, failed pings are meaningful because they show that the controller is enforcing policy.

> [!IMPORTANT]
> Failed pings are not automatically failed experiments. In this work, blocked traffic is often the expected result because the controller is enforcing segmentation, trust, and least-privilege policy.

## 2. Research Question

The practical research question for this implementation is:

> How can a Zero Trust-inspired SDN architecture detect and contain abnormal communication behaviour in Building Management Systems (BMS) using AAA-based identity verification, runtime risk assessment, ABAC policy enforcement, and dynamic quarantine?

This question is tested using a small but controlled Mininet topology. Each host represents a different BMS device type. The Python-based OpenFlow controller (POX) acts as the policy decision point and installs OpenFlow rules using a Zero Trust sequence: Authentication, Authorisation, and Accounting (AAA) first, then Zero Trust (ZT) risk assessment, rate/quarantine checks, Attribute-Based Access Control (ABAC), and final enforcement.

## 3. Proposed Architecture Contribution

This thesis does not claim to invent SDN, Zero Trust, AAA, or ABAC. Instead, it proposes an integrated architecture for applying Zero Trust principles to BMS communication using SDN-based enforcement.

| Architecture layer | Function in the proposed BMS architecture |
|---|---|
| BMS device layer | Represents controllers, sensors, and external devices that generate communication requests |
| SDN data plane | Uses Open vSwitch to enforce controller-installed allow/drop flow rules |
| Identity layer | Uses AAA-style verification as the first Zero Trust step for source identity and session accounting |
| Zero Trust risk layer | Scores authenticated flows based on trust, context, previous denials, destination risk, and packet volume |
| Policy layer | Uses ABAC to enforce least-privilege communication between BMS roles and systems |
| Response layer | Drops unauthorised flows, revokes sessions, and quarantines suspicious hosts |
| Evidence layer | Logs authentication, Zero Trust decisions, ABAC decisions, quarantine events, and final metrics |

### 3.1 Why I Designed It This Way

I considered whether this experiment should implement a full real-world Zero Trust stack, such as certificate-based device identity, an external Authentication, Authorisation, and Accounting (AAA) server, device posture collection, and a production policy engine. That would be closer to an enterprise deployment, but it would also move the thesis away from the main research problem: showing how Software-Defined Networking (SDN) can enforce security decisions for Building Management System (BMS) communication.

For this reason, I kept the implementation as a controlled proof of concept. The controller does not claim to be a complete commercial Zero Trust product. Instead, it implements the main Zero Trust ideas in a transparent way so that each decision can be observed, tested, and explained.

| Real-world Zero Trust idea | How I model it in this experiment | Why I chose this approach |
|---|---|---|
| Strong device identity | Registered Internet Protocol (IP), Media Access Control (MAC), and device ID in the AAA registry | Simple enough to test in Mininet, but still shows that identity is checked before access |
| Continuous verification | Every new flow is checked by the controller | Demonstrates that trust is not based only on being inside the network |
| Context-aware access | Device attributes include role, system, trust, and context | Allows the controller to make BMS-specific decisions |
| Least privilege | Attribute-Based Access Control (ABAC) allows only expected communication paths | Matches the requirement that sensors, controllers, and external devices should not all communicate freely |
| Risk-based access | A rule-based score is calculated before ABAC | Makes risk visible and explainable instead of hiding the decision inside a black box |
| Dynamic response | Repeated denied attempts trigger quarantine and session revocation | Shows containment, not only allow/deny filtering |
| Enforcement | OpenFlow rules are installed in Open vSwitch (OVS) | Demonstrates that the SDN switch enforces the controller decision |

The scoring model is therefore not presented as an official Zero Trust standard. It is my experimental risk model. I use it because it is deterministic, repeatable, and easy to justify during evaluation. If h4 is denied, I can explain exactly whether the reason was unknown trust, cross-system access, previous denied attempts, quarantine, or ABAC policy.

This design keeps the thesis focused: the contribution is the architecture and experiment design, not the deployment of every production component that would exist in a real building network.

> [!NOTE]
> The risk score is a transparent proof-of-concept mechanism. It represents Zero Trust principles, but it is not claimed to be an official industry scoring standard.

## 4. Why SDN Was Used

SDN is suitable for this experiment because it separates the control plane from the data plane. The Open vSwitch instance forwards packets, but the POX controller decides how new flows should be handled.

This is useful for a BMS security design for three reasons:

| Reason | Explanation |
|---|---|
| Centralised policy enforcement | Access-control rules are implemented in one controller instead of being manually configured on many switches |
| Visibility | The controller sees new communication attempts and can log decisions for analysis |
| Dynamic response | Device behaviour can influence future decisions, for example quarantine after repeated denied attempts |

In a traditional static network, a switch generally forwards traffic based on MAC learning or fixed rules. In this experiment, the switch asks the controller before forwarding new flows. This allows security decisions to be made using device identity and context.

## 5. Experimental Environment

The experiment is implemented using the following components:

| Component | Role |
|---|---|
| Ubuntu 24.04 on Windows Subsystem for Linux (WSL) | Operating environment used to run the experiment |
| Mininet | Creates the simulated BMS network |
| Open vSwitch (OVS) | Acts as the OpenFlow switch |
| Python-based OpenFlow controller (POX) | Runs the custom SDN controller |
| `controller.py` | Implements AAA, Zero Trust risk scoring, ABAC, logging, rate limiting, and quarantine logic |
| `mininet.sh` | Starts Mininet and connects the switch to the POX controller |
| `ping_test.mn` | Mininet CLI test script with documented test cases |

Because the experiment is being run on Windows Subsystem for Linux (WSL), `mininet.sh` uses the Open vSwitch (OVS) userspace datapath when WSL is detected. This is done because the OVS kernel datapath is often unavailable or unreliable in WSL environments.

> [!WARNING]
> WSL behaves differently from a full Linux virtual machine. If Open vSwitch services fail under WSL, the experiment should still use the Mininet script because it selects the userspace datapath path where possible.

## 6. Network Topology

The topology is intentionally small so that each communication attempt can be understood and mapped directly to a policy decision.

```text
                    POX Controller
                          |
                          |
                         s1
          /        /       |       \        \
        h1        h2       h3       h4       h5
```

All hosts are connected to a single OpenFlow switch. The switch connects to the POX controller using OpenFlow 1.0.

| Host | Internet Protocol (IP) address | Media Access Control (MAC) address | Device represented | System | Initial security meaning |
|---|---|---|---|---|---|
| h1 | 10.0.0.1 | 00:00:00:00:00:01 | BMS / HVAC controller | HVAC | Trusted central controller |
| h2 | 10.0.0.2 | 00:00:00:00:00:02 | HVAC sensor | HVAC | Trusted sensor |
| h3 | 10.0.0.3 | 00:00:00:00:00:03 | Lighting controller | Lighting | Trusted controller |
| h4 | 10.0.0.4 | 00:00:00:00:00:04 | Lighting sensor | Lighting | Sensor with unknown trust |
| h5 | 10.0.0.5 | 00:00:00:00:00:05 | External / unknown device | Unknown | Restricted and abnormal device |

The topology represents a simplified BMS where HVAC and lighting are separate subsystems. This allows the experiment to test segmentation, sensor restrictions, controller exemptions, and suspicious external communication.

The updated architecture flowcharts are provided as editable vector images:

```text
My_Thesis/2025-2026/code/zero_trust_sdn_flowchart.svg
My_Thesis/2025-2026/code/zero_trust_scenario_flowchart.svg
```

## 7. Controller Design

The controller is implemented in `controller.py`. It listens for OpenFlow `PacketIn` events from the switch. A `PacketIn` event occurs when the switch receives a packet for which it does not already have a forwarding rule.

The controller processes each IPv4 packet using the following Zero Trust sequence:

```text
PacketIn received by POX controller
        |
        v
Learn source MAC and handle ARP if needed
        |
        v
Extract source IP, destination IP, and source MAC
        |
        v
1. AAA identity and session validation
        |
        v
2. Destination registry validation
        |
        v
3. Zero Trust runtime risk assessment
        |
        +---- high risk: install drop rule and update denial behaviour
        |
        v
4. Rate-limit check
        |
        v
5. Quarantine check
        |
        +---- quarantined: install drop rule
        |
        v
6. ABAC least-privilege policy evaluation
        |
        +---- allow: install forwarding rule
        |
        +---- deny: install drop rule and update denial behaviour
```

This ordering is deliberate. Under Zero Trust, the first question is always identity: the controller must know which device produced the packet before any trust score or policy decision is meaningful. After AAA verifies identity, the controller calculates runtime risk, applies rate/quarantine checks, evaluates ABAC policy, and finally installs an allow or drop rule.

> [!INFO]
> In this design, AAA is not separate from Zero Trust. AAA is the first Zero Trust verification step because every later decision depends on knowing the source identity.

## 8. AAA Implementation

Authentication, Authorisation, and Accounting (AAA) is the first Zero Trust verification step in this controller. It is simulated inside the controller rather than using a separate Remote Authentication Dial-In User Service (RADIUS) or Terminal Access Controller Access-Control System Plus (TACACS+) server.

### 8.1 Authentication

Authentication checks whether the source device is registered and whether its Media Access Control (MAC) address matches the expected MAC address for its Internet Protocol (IP) address.

| Check | Example |
|---|---|
| Source Internet Protocol (IP) address exists in registry | `10.0.0.2` must exist in the AAA registry |
| Source Media Access Control (MAC) address matches registry | `10.0.0.2` must use `00:00:00:00:00:02` |

If the IP or MAC does not match, the packet is dropped and an authentication failure is logged.

### 8.2 Authorisation Session

After successful authentication, the controller creates a session entry for the device. This avoids full re-authentication on every packet, but the packet is still continuously evaluated by the later Zero Trust risk and ABAC layers. The session contains the generated token, issue time, MAC address, device ID, and label.

The session timeout is currently set to 300 seconds. If a session expires, the next packet from that device triggers re-authentication.

### 8.3 Accounting

The controller logs authentication events. This supports evaluation because the experiment can show not only whether traffic passed or failed, but also why the decision was made.

| Accounting event | Meaning |
|---|---|
| `AUTH_OK` | The device identity matched the AAA registry |
| `AUTH_FAIL` | Authentication failed because the source was unknown or the MAC did not match |
| `SESSION_REVOKED` | A device session was removed after quarantine |

## 9. ABAC Implementation

Attribute-Based Access Control (ABAC) evaluates attributes assigned to each device instead of allowing traffic only by Internet Protocol (IP) address.

| Attribute | Meaning in this experiment |
|---|---|
| `role` | Functional role, such as `sensor`, `bms_controller`, or `lighting_controller` |
| `device_type` | General device category, such as `sensor`, `controller`, or `unknown` |
| `system` | BMS subsystem, such as `hvac` or `lighting` |
| `trust` | Initial or dynamic trust level |
| `context` | Runtime condition, such as `normal`, `off-hours`, or `abnormal` |

The attributes are separate from the AAA registry. This separation is intentional inside the Zero Trust design: AAA answers "Who is this device?", Zero Trust asks "Is this request risky right now?", and ABAC answers "What is this device allowed to do?"

## 10. Zero Trust Risk Assessment

Zero Trust is the overall security model used in this experiment. AAA is part of Zero Trust because it is the first verification step when a packet arrives. After AAA verifies the device identity, the controller evaluates runtime risk and then applies ABAC access policy.

The controller calculates a risk score for every new flow. The score is based on device trust, context, destination risk, previous denials, cross-system attempts, sensor-to-sensor attempts, and elevated packet volume.

| Risk factor | Example | Effect |
|---|---|---|
| Unknown or limited trust | h4 has `trust="unknown"` | Increases risk score |
| Abnormal source context | h5 has `context="abnormal"` | Strongly increases risk score |
| Abnormal or restricted destination | h2 attempts to reach h5 | Increases risk score |
| Sensor-to-non-controller traffic | h2 attempts to reach h4 | Increases risk score |
| Cross-system traffic by non-BMS controller | h3 attempts to reach h1 | Increases risk score |
| Previous denied attempts | h4 repeatedly violates policy | Increases risk score |
| Elevated packet volume | rapid h2 requests | Slightly increases risk score |

| Zero Trust decision | Risk score range | Controller behaviour |
|---|---|---|
| `ALLOW` | Below 40 | Continue to ABAC evaluation |
| `MONITOR` | 40-69 | Continue to ABAC, but count as high-risk monitoring |
| `DENY` | 70 or above | Drop before ABAC and update denial behaviour |

This models the Zero Trust principle that a device is not trusted only because it is inside the network. A device must remain acceptable at runtime based on its identity, context, behaviour, and requested destination.

The startup log prints:

```text
Zero Trust risk engine ready — monitor threshold=40 deny threshold=70
```

These thresholds mean:

| Threshold | Meaning |
|---|---|
| Monitor threshold `40` | The request is not automatically blocked, but it is counted as high-risk monitoring evidence |
| Deny threshold `70` | The request is considered high-risk enough to be dropped before ABAC evaluation |

For example, an unknown-trust device, abnormal context, restricted destination, previous denials, or cross-system behaviour can increase the score. The thresholds are intentionally transparent and rule-based for the proof of concept, so the reason for a Zero Trust decision can be explained in the thesis.

The score is not random or machine-generated. It is a deterministic weighted sum. Each matching risk condition adds points:

| Risk condition in controller | Score added | Why it matters |
|---|---:|---|
| Source trust is `unknown` | `35` | Device identity is known by AAA, but its operational trust is not strong |
| Source trust is dynamically `limited` | `45` | The device has been downgraded after repeated denied behaviour |
| Source trust is `restricted` | `50` | The source is treated as high-risk from the start |
| Source context is `off-hours` | `35` | A device with a restricted schedule is active outside its expected operating window |
| Source context is `abnormal` | `60` | The source is already marked as unsafe or compromised |
| Destination context is `abnormal` | `30` | The request targets a risky destination |
| Destination trust is `restricted` | `35` | The request targets a restricted asset |
| Sensor attempts non-controller communication | `15` | Sensors should not perform lateral communication |
| Non-BMS controller crosses subsystem boundary | `20` | Enforces segmentation between HVAC, lighting, and other BMS subsystems |
| Previous denied attempts from source | `10` per denial, maximum `30` | Repeated violations increase behavioural risk |
| Previous denied destinations from source | `10` per destination, maximum `20` | Attempts against multiple destinations indicate scanning or misuse |
| Elevated packet volume | `10` | Rapid repeated traffic increases risk before the hard rate limit is reached |
| Repeated short inter-arrival time | `15` per observation, maximum `30` | A small delta-t between new flows can indicate scanning, polling abuse, or automation |

Example: h4 has `trust="unknown"`, so it starts with `35` points. If h4 also attempts cross-system communication, the score becomes `55` (`35 + 20`), which is monitored. After previous denied attempts, additional points can push the same host above `70`, causing a Zero Trust deny before ABAC.

> [!TIP]
> During evaluation, explain the score by adding the matching risk factors. For example, unknown trust plus cross-system communication equals `35 + 20 = 55`.

## 11. Access-Control Policy

The controller applies the following policy rules.

| Rule | Rationale | Example |
|---|---|---|
| Unknown sources are denied | The controller should not allow devices without registered attributes | An unregistered IP is blocked |
| Abnormal sources are denied | Abnormal context indicates suspicious or unsafe behaviour | h5 is blocked because it starts as abnormal |
| Off-hours scheduled devices are restricted | Activity outside the configured schedule may indicate unusual operation | Lighting field devices may be blocked outside 08:00-18:00 |
| Source trust must be trusted | Unknown or restricted sources should not initiate communication | h4 is denied because its trust is `unknown` |
| Restricted destinations are denied | Trusted devices should not communicate with restricted devices | h2 to h5 is denied |
| Sensors can only communicate with controllers | Sensors should not communicate laterally with other sensors | h2 to h4 is denied |
| Cross-system communication is restricted | HVAC and lighting should remain segmented | h3 to h1 is denied |
| BMS controller can communicate across systems | The central BMS controller may need supervisory access | h1 to h3 may be allowed |

The controller currently allows Internet Control Message Protocol (ICMP) traffic when AAA, Zero Trust, and ABAC checks pass. This makes `ping` a simple way to test policy decisions. The controller also recognises User Datagram Protocol (UDP) destination port 47808 as Building Automation and Control Network (BACnet)-representative traffic.

### 11.1 Business-Hours Context

The controller uses a business-hours context rule:

```text
Business hours: 08:00 to 18:00
```

The off-hours rule is based on a per-device `schedule` attribute instead of a broad role rule.

This means:

| Device/schedule | Off-hours behaviour |
|---|---|
| h1 BMS/HVAC controller, `always` | Remains `normal` |
| h2 HVAC sensor, `always` | Remains `normal` because HVAC telemetry is treated as continuous operation |
| h3 lighting controller, `business_hours` | Marked `off-hours` outside 08:00-18:00 |
| h4 lighting sensor, `business_hours` | Marked `off-hours` outside 08:00-18:00 |
| h5 external device, `maintenance_window` | Restricted and already abnormal in this testbed |

For repeatable tests, the controller also checks `/tmp/bms_controller_hour`. If that file contains an hour such as `2` or `10`, the controller uses it instead of the system clock. This avoids changing the operating-system time during validation.

## 12. Behavioural Detection and Quarantine

The controller records denied communication attempts. If a device repeatedly violates policy, it is treated as suspicious.

| Detection condition | Threshold | Action |
|---|---:|---|
| Repeated denied attempts from the same source | 3 denials | Mark host suspicious and quarantine it |
| Denied attempts to multiple destinations | 2 distinct destinations | Mark host suspicious and quarantine it |

When a host is quarantined:

1. It is added to the `quarantined_hosts` set.
2. Its context is changed to `abnormal`.
3. Its AAA session is revoked.
4. Future packets from that host are dropped quickly.

This is included to show that the controller can do more than static allow/deny decisions. It can also change its behaviour based on observed traffic.

> [!IMPORTANT]
> Quarantine is the containment part of the architecture. It shows that the controller can respond to repeated suspicious behaviour, not only evaluate one packet at a time.

## 13. Test Plan

The experiment uses two Mininet CLI test scripts. The baseline script verifies the main communication policy. The advanced script validates attack-style behaviour and evidence collection.

| Script | Purpose |
|---|---|
| `ping_test.mn` | Baseline policy tests: normal communication, policy denial, segmentation, restricted devices, rate-limit attempt, and quarantine |
| `advanced_test.mn` | Advanced validation: MAC spoofing, unknown IP, BACnet-style UDP, OpenFlow table inspection, quarantine persistence, and log evidence |

### 13.1 Baseline Policy Tests

The baseline tests are designed to exercise normal communication, policy denial, segmentation, restricted devices, and quarantine behaviour.

| Test ID | Traffic | Reason for test | Expected result |
|---|---|---|---|
| T01 | h2 -> h1 | HVAC sensor reports to HVAC controller | Allowed during business hours |
| T02 | h1 -> h2 | BMS controller communicates with HVAC sensor | Allowed during business hours |
| T03 | h2 -> h3 | HVAC sensor tries to reach lighting controller | Denied due to cross-system policy |
| T04 | h2 -> h4 | Sensor attempts lateral sensor communication | Denied because sensors may only talk to controllers |
| T05 | h3 -> h1 | Lighting controller attempts HVAC communication | Denied due to cross-system policy |
| T06 | h1 -> h3 | BMS controller reaches lighting controller | Allowed because BMS controller is exempt |
| T07 | h4 -> h3 | Unknown-trust lighting sensor contacts controller | Denied due to source trust |
| T08 | h5 -> h1 | External abnormal device contacts BMS controller | Denied due to abnormal/restricted attributes |
| T09 | h2 -> h5 | Trusted sensor contacts restricted destination | Denied due to destination context/trust |
| T10 | repeated h4 denials | Trigger behavioural detection | h4 is quarantined |
| T11 | h4 -> h3 after quarantine | Confirm quarantine enforcement | Denied |
| T12 | rapid h2 requests | Exercise rate-limit logic | Rate-limit entries may appear if enough packets reach controller |

The test script clears OpenFlow rules between selected tests. This is necessary because once the controller installs a rule, later packets in the same flow may be handled directly by Open vSwitch and may not reach the controller.

> [!NOTE]
> Clearing flows between tests makes the evidence easier to read because each test forces the next packet back to the controller.

### 13.2 Advanced Security Validation Tests

The advanced tests are designed to show that the architecture does more than permit or deny normal pings. These tests produce evidence for identity failure, Zero Trust risk handling, SDN flow-rule enforcement, and quarantine persistence.

| Test ID | Traffic/action | Reason for test | Expected result |
|---|---|---|---|
| A01 | h2 -> h1, then `dump-flows` | Show successful communication and installed OpenFlow rules | ALLOW plus visible flow entries |
| A02 | h2 changes to wrong MAC, then h2 -> h1 | Test AAA identity enforcement | `EVENT=AAA_AUTH_FAIL` due to MAC mismatch |
| A03 | h2 changes to unregistered IP, then h2 -> h1 | Test unknown identity handling | `EVENT=AAA_AUTH_FAIL` because source IP is not registered |
| A04 | h2 sends UDP to h1 on port 47808 | Test BACnet-representative traffic | ALLOW if AAA, Zero Trust, and ABAC pass |
| A05 | h2 sends several rapid h2 -> h1 flows | Test delta-t behaviour | `EVENT=TIMING_DELTA` and possible added risk |
| A06 | forced hour `10`, h3 -> h4 UDP/47808 | Test scheduled device during business hours | ALLOW |
| A07 | forced hour `2`, h3 -> h4 UDP/47808 | Test scheduled device outside business hours | `EVENT=OFF_HOURS_CONTEXT` and ABAC deny |
| A08 | forced hour `2`, h2 -> h1 | Confirm continuous HVAC device behaviour | ALLOW |
| A09 | h4 repeatedly triggers denied traffic | Test behavioural detection | Suspicious host detection and quarantine |
| A10 | h4 communicates after quarantine | Test quarantine persistence | Blocked quarantined host |
| A11 | show recent controller evidence from Mininet shell | Collect readable event lines | Compact log section for screenshots/results |

The advanced test script intentionally changes h2's MAC and IP address, then restores them. It is best run from a fresh Mininet and controller session so previous quarantine or rate-limit state does not affect the result.

### 13.3 Interpreting OpenFlow Dump Output

Some advanced tests run `ovs-ofctl dump-flows s1`. This is not another ping result. It is the Open vSwitch (OVS) flow table, which shows what rule the SDN controller installed in the switch.

Example denied-flow output:

```text
cookie=0x0, duration=11.005s, table=0, n_packets=1, n_bytes=98,
idle_timeout=30, hard_timeout=60, priority=65535,icmp,in_port="s1-eth4",
dl_src=00:00:00:00:00:04,dl_dst=00:00:00:00:00:03,
nw_src=10.0.0.4,nw_dst=10.0.0.3,icmp_type=8,icmp_code=0 actions=drop
```

| Field | Meaning |
|---|---|
| `duration=11.005s` | How long the switch rule has existed |
| `n_packets=1` | Number of packets that matched this rule |
| `n_bytes=98` | Number of bytes that matched this rule |
| `idle_timeout=30` | Delete the rule after 30 seconds without matching traffic |
| `hard_timeout=60` | Delete the rule after 60 seconds even if traffic continues |
| `priority=65535` | Rule priority chosen by POX/OpenFlow for this match |
| `icmp` | The matched protocol was ICMP, which is what `ping` uses |
| `in_port="s1-eth4"` | The packet entered the switch from h4 |
| `dl_src` / `dl_dst` | Source and destination MAC addresses |
| `nw_src` / `nw_dst` | Source and destination IP addresses |
| `icmp_type=8` | ICMP echo request, meaning a ping request |
| `actions=drop` | The switch was instructed to drop matching packets |

This output is useful because it proves enforcement happened inside the SDN switch. The controller made the decision, then installed an OpenFlow rule so later matching packets could be dropped directly by the switch.

## 14. How the Experiment Is Run

### 14.1 POX Setup in a Python venv

Use a Python virtual environment so POX and its local imports are reproducible.

```bash
# 1. Clone POX
cd ~/thesis
git clone https://github.com/noxrepo/pox.git
cd pox
git checkout gar-experimental

# 2. Add minimal pyproject.toml so pip can install POX in editable mode
cat > pyproject.toml <<'EOF'
[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"

[project]
name = "pox"
version = "0.7.0"
description = "POX SDN controller"
requires-python = ">=3.8"

[tool.setuptools]
packages = ["pox"]

[tool.setuptools.package-dir]
pox = "pox"
EOF

# 3. Create and activate venv
python3 -m venv .venv
source .venv/bin/activate

# 4. Install POX as editable package
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .

# 5. Add custom controller module
cp /path/to/bms-zero-trust-sdn/controller.py pox/ext/bms_controller.py

# 6. Run POX with custom controller
python pox.py log.level --DEBUG bms_controller
```

For later runs, the repository and virtual environment already exist. Reactivate the environment, refresh the controller copy, and start POX:

```bash
cd ~/thesis
cd ~/thesis/pox
source .venv/bin/activate
cp /path/to/bms-zero-trust-sdn/controller.py ext/bms_controller.py
python pox.py log.level --DEBUG bms_controller
```

### 14.2 Start the POX Controller

The controller must be copied into the POX `ext` directory and then started by module name.

```bash
cd ~/thesis/pox
source .venv/bin/activate
cp /path/to/bms-zero-trust-sdn/controller.py ext/bms_controller.py
python pox.py log.level --DEBUG bms_controller
```

Expected startup messages include:

```text
EVENT=LOG_READY
EVENT=STARTUP
EVENT=BUSINESS_HOURS
EVENT=AAA_READY
EVENT=ZT_READY
```

### 14.3 Start Mininet

In a second terminal:

```bash
cd /path/to/bms-zero-trust-sdn
bash mininet.sh
```

The script performs cleanup, prepares Open vSwitch, checks that the POX controller is listening on port 6633, and starts the five-host topology.

### 14.4 Run Baseline Test Cases

The test cases are written directly as a Mininet Command-Line Interface (CLI) script so that the commands and comments remain together. Inside the Mininet CLI, run:

```text
source ping_test.mn
```

Do not use `~` in the Mininet `source` command. Mininet may not expand it, which can cause `error reading file`.

You can also run one test manually from the Mininet prompt. For example:

```text
h2 ping -c 2 10.0.0.1
```

The Mininet script prints simple test labels. The controller log remains the authoritative evidence for allow, deny, risk, and quarantine decisions.

### 14.5 Run Advanced Validation Tests

For attack-style and evidence-oriented validation, run this from the Mininet CLI:

```text
source advanced_test.mn
```

### 14.6 Observe Controller Logs

In another terminal:

```bash
tail -f /tmp/bms_controller_events.txt
```

The watcher waits until the controller creates the evidence file and then follows it. The controller writes to `/tmp/bms_controller_events.txt`. This intentionally avoids the `.log` suffix because `mn -c` removes `/tmp/*.log` during Mininet cleanup.

The log is the main evidence for the experiment. Ping output shows packet success or failure, but the log explains the reason for each controller decision.

The evidence file is plain text and can be viewed with standard shell tools such as `tail`, `less`, or `grep`.

Color legend for live terminals:

| Color | Meaning | Example events/output |
|---|---|---|
| Cyan | Test boundary or test label | `TEST=T04`, `RUN_TEST_NOW`, separator lines |
| Green | Allowed traffic | `EVENT=ALLOW`, `OBSERVED_OUTCOME=ALLOW` |
| Red | Denied traffic | `EVENT=ABAC_DENY`, `EVENT=ZT_DENY`, `EVENT=RATE_LIMIT_DENY` |
| Magenta | Detection or containment response | `EVENT=SUSPICIOUS_HOST`, `EVENT=QUARANTINE_APPLIED`, `EVENT=QUARANTINE_DENY` |
| Yellow | Risk/context/accounting signal | `EVENT=ZT_ASSESS`, `EVENT=DENY_COUNT`, `EVENT=TRUST_DOWNGRADE`, `EXPECTED=...` |

The colors are only for live readability in the terminal. They are not written into `/tmp/bms_controller_events.txt`.

> [!WARNING]
> Do not use `/tmp/bms_controller.log` for this version. Mininet cleanup removes `/tmp/*.log`, so the stable evidence file is `/tmp/bms_controller_events.txt`.

The Mininet test scripts print a readable marker before each test in the Mininet terminal. The controller evidence file remains controller-owned evidence only. This avoids permission conflicts between POX running as the normal user and Mininet running through `sudo`.

```text
================================================================================
TEST=T07
TRAFFIC=h4 10.0.0.4 -> h3 10.0.0.3
PURPOSE=Unknown-trust lighting sensor attempts controller communication
EXPECTED=ABAC_DENY, possible ZT monitor
TIME=2026-04-29 18:10:22
RUN_TEST_NOW
================================================================================
```

After the ping command, the test script prints the actual observed controller outcome:

```text
--------------------------------------------------------------------------------
TEST=T07
EXPECTED=ABAC_DENY, possible ZT monitor
OBSERVED_OUTCOME=ABAC_DENY
CONTROLLER_EVENT=2026-04-29 18:10:25 | EVENT=ABAC_DENY | src=10.0.0.4 | dst=10.0.0.3 | ...
--------------------------------------------------------------------------------
```

`OBSERVED_OUTCOME` is copied from the controller decision event, such as `ALLOW`, `ABAC_DENY`, `ZT_DENY`, `RATE_LIMIT_DENY`, or `QUARANTINE_APPLIED`.

> [!TIP]
> For screenshots or seminar explanation, show one complete test block: marker, expected result, controller events, and the matching ping output.

## 15. Expected Observations

The following log messages are expected during a successful experiment.

| Log event | Interpretation |
|---|---|
| `EVENT=AAA_AUTH_OK` | A device successfully authenticated |
| `EVENT=AAA_AUTH_FAIL` | Authentication or registry validation failed |
| `EVENT=ZT_ASSESS` | Runtime risk score calculated before ABAC |
| `EVENT=TIMING_DELTA` | New flow from a source arrived sooner than the configured delta-t threshold |
| `EVENT=OFF_HOURS_CONTEXT` | A scheduled device was active outside business hours |
| `EVENT=ZT_DENY` | High-risk flow blocked before ABAC |
| `EVENT=ALLOW` | Traffic passed AAA, Zero Trust, and ABAC checks |
| `EVENT=ABAC_DENY` | Traffic passed AAA and Zero Trust but failed ABAC policy |
| `EVENT=DENY_COUNT` | A denied attempt was recorded for behavioural tracking |
| `EVENT=TRUST_DOWNGRADE` | A trusted device was demoted after repeated denials |
| `EVENT=SUSPICIOUS_HOST` | The detection threshold was reached |
| `EVENT=QUARANTINE_APPLIED` | The host was isolated by the controller |
| `EVENT=AAA_SESSION_REVOKED` | A quarantined host lost its AAA session |
| `EVENT=RATE_LIMIT_DENY` | A source exceeded the configured packet threshold |
| `EVENT=FINAL_SUMMARY` | Summary printed when the controller exits cleanly |

The final metrics include total requests, allowed requests, denied requests, authentication failures, Zero Trust denies, high-risk Zero Trust observations, rate-limit drops, detections, quarantines, and latency measurements.

```text
================================================================================
TEST=T01
TRAFFIC=h2 10.0.0.2 -> h1 10.0.0.1
PURPOSE=Trusted HVAC sensor reports to HVAC controller
EXPECTED=ALLOW
TIME=2026-04-29 17:50:12
RUN_TEST_NOW
================================================================================
2026-04-29 17:50:12 | EVENT=ALLOW | src=10.0.0.2 | dst=10.0.0.1 | direction="h2 -> h1" | score=0 | latency_ms=1.214 | reason="ICMP allowed by ABAC policy"
```

The Mininet test label separates test cases. The `EVENT=...` line remains the authoritative controller evidence.

## 16. Why the Controller Evidence File May Not Exist

The evidence file is created only when POX successfully imports the controller module and calls the `launch()` function. If the file does not exist, it usually means the controller has not actually started.

The old path, `/tmp/bms_controller.log`, should not be used for this experiment. Mininet cleanup removes `/tmp/*.log`, so the controller now writes to:

```text
/tmp/bms_controller_events.txt
```

| Check | Command | Explanation |
|---|---|---|
| Confirm controller file was copied | `ls ~/thesis/pox/ext/bms_controller.py` | POX loads the module from `ext/` |
| Confirm correct POX command | `python pox.py log.level --DEBUG bms_controller` | The module name must match `bms_controller.py` |
| Look for startup logs | POX terminal output | Confirms that `launch()` ran |
| Check stale processes | `ps -ef | grep pox` | Old POX processes may be running old code |
| View controller evidence | `tail -f /tmp/bms_controller_events.txt` | Follows the controller's standard POX/file log output |

If POX is started correctly, `/tmp/bms_controller_events.txt` should appear immediately after the startup event:

```text
EVENT=LOG_READY
```

## 17. Data Collection

The main data source is `/tmp/bms_controller_events.txt`. For each test case, the relevant evidence is:

| Evidence | Source |
|---|---|
| Whether traffic was allowed or denied | `EVENT=ALLOW`, `EVENT=ABAC_DENY`, `EVENT=ZT_DENY`, and `EVENT=RATE_LIMIT_DENY` |
| Why traffic was denied | Reason text in the controller log |
| Authentication behaviour | `EVENT=AAA_AUTH_OK`, `EVENT=AAA_AUTH_FAIL`, and `EVENT=AAA_SESSION_REVOKED` |
| Zero Trust behaviour | `EVENT=ZT_ASSESS`, risk score, and `EVENT=ZT_DENY` |
| SDN enforcement | `ovs-ofctl dump-flows s1` output from advanced tests |
| Detection behaviour | `EVENT=DENY_COUNT`, `EVENT=SUSPICIOUS_HOST`, and `EVENT=QUARANTINE_APPLIED` |
| Performance overhead | Per-request latency values |
| Summary statistics | `EVENT=FINAL_SUMMARY` |

Screenshots of the Mininet CLI and POX terminal can be used as supporting evidence, but the controller log should be treated as the primary result.

## 18. Limitations

This implementation is a proof of concept, so several limitations should be acknowledged:

| Limitation | Explanation |
|---|---|
| Simulated devices | Mininet hosts represent BMS devices, but they are not real HVAC or lighting hardware |
| Simplified AAA | AAA is implemented inside the controller rather than using an external AAA server |
| Simplified identity | Device identity uses IP and MAC addresses for simulation; production systems should use stronger credentials |
| Simplified Zero Trust | The risk score is rule-based and transparent for experimentation, not a production-grade risk engine |
| Static attribute registry | Device attributes are manually defined in code |
| ICMP-based testing | Ping is used for repeatable policy testing, although real BMS traffic would include protocols such as BACnet |
| Windows Subsystem for Linux (WSL) environment | WSL may require Open vSwitch (OVS) userspace datapath and may behave differently from a full Linux Virtual Machine (VM) |
| Small topology | The topology is intentionally limited to five hosts for clarity |

These limitations do not invalidate the experiment. They define the scope: the aim is to demonstrate policy logic and controller behaviour, not to reproduce a full production BMS network.

## 19. Future Work

Future versions of this architecture should replace simulated IP/MAC identity with stronger device identity mechanisms such as certificate-based authentication, 802.1X-style network access control, signed device credentials, or hardware-backed identity such as a Trusted Platform Module (TPM). The risk engine could also be extended with richer telemetry, longer-term behaviour history, and integration with a Security Information and Event Management (SIEM) platform.

## 20. File Organisation

The experiment is kept in multiple files because each file has a distinct role.

| File | Purpose |
|---|---|
| `controller.py` | Implements the POX controller and all security logic |
| `mininet.sh` | Starts and cleans the Mininet/Open vSwitch environment |
| `ping_test.mn` | Documents and runs repeatable Mininet test commands |
| `advanced_test.mn` | Runs advanced identity, flow-table, BACnet-style UDP, and quarantine validation tests |
| `Documentation.md` | Describes the experiment design, method, and expected observations |

A Jupyter notebook can be useful later for analysing the log file and producing plots. It is not the best place to run the live SDN experiment because Mininet, Open vSwitch, and POX are process-based tools that are more reproducible from scripts.

```text
Live experiment:  shell scripts + POX controller
Documentation:    Markdown
Result analysis:  optional Jupyter notebook after logs are collected
```

## 21. Summary

This experiment uses Mininet and POX to simulate a BMS network and test a proposed Zero Trust-inspired SDN access-control architecture. The design separates device identity from access policy, treats AAA as the first Zero Trust verification step, adds continuous risk assessment, records accounting information, and includes a behavioural response mechanism for repeated policy violations.

The value of the experiment is that it produces observable evidence: successful authentications, denied communication attempts, policy reasons, quarantine events, and final metrics. These observations can be used to evaluate the suitability of SDN-based access control for BMS network security.
