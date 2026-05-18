# BACnet Dataset Analysis and Architectural Justification

This document explains how the BACnet dataset analysis informed the design of the proposed Zero Trust-inspired SDN architecture for Building Management System (BMS) security.

It is the bridge between the dataset study and the implemented architecture. The purpose is to show that the architecture was not chosen randomly: it was derived from observed weaknesses in BACnet/BMS traffic and from the attack scenarios described in the dataset source paper.

The implementation artifact and reproducibility package are available at:

```text
https://github.com/ramsainanduri/bms-zero-trust-sdn
```

The repository includes the SDN controller, Mininet test scripts, installation instructions, and architecture flowcharts. The large analysis scripts and generated CSV/SVG outputs are thesis-side evidence and are intentionally kept outside the public code repository.

## 1. Dataset and Paper Used

The dataset used as background evidence is the Kaggle **BACnet network dataset**:

```text
https://www.kaggle.com/datasets/78eb45aeaac481853135d90738672111e46fe2a4ce653573e8856fc920f3da68
```

The associated paper is:

```text
Seyed Amirhossein Moosavi, Mojtaba Asgari, Seyed Reza Kamel,
"Developing a comprehensive BACnet attack dataset: A step towards improved cybersecurity in building automation systems",
Data in Brief, Volume 57, 2024, Article 111192.
DOI: https://doi.org/10.1016/j.dib.2024.111192
```

The paper describes a framework for converting real building-management data into BACnet/IP network traffic. The source building data came from the Building and Energy Management System of Tampines College Global Campus in Singapore. The authors used virtual controllers to generate BACnet traffic and captured the traffic in PCAP format using Wireshark.

The dataset contains normal BACnet traffic and attack traffic, including:

| Dataset file/scenario | Type | Security meaning |
|---|---|---|
| `Normal-traffic` | Normal BACnet traffic | Baseline BMS communication |
| `CCA-plaintext` | Covert channel attack | Timing-based hidden message in plain text |
| `CCA-hash` | Covert channel attack | Timing-based hidden message represented as a hash |
| `CCA-encryption` | Covert channel attack | Timing-based hidden message represented with encryption |
| `Falsifying-in-chiller` | Falsifying attack | Manipulated chiller temperature value |
| `Modifying-in-chiller` | Modifying attack | Manipulated pump on/off status |

The published paper reports that the dataset contains millions of BACnet entries across normal and attack PCAPs. This matters because it provides realistic protocol traffic instead of only abstract tabular values.

## 2. Why the Data Analysis Was Done

The data analysis was done before designing the architecture for three reasons.

First, the thesis needed evidence of what BMS traffic looks like under normal and malicious conditions. A security architecture should respond to realistic weaknesses, not only theoretical assumptions.

Second, the analysis helped identify which security controls were missing or weak in typical BACnet-style BMS communication. The dataset showed that attacks can occur while network-level properties still appear normal.

Third, the analysis helped translate observed weaknesses into architectural requirements. For example, if malicious traffic can originate from apparently legitimate devices, then identity verification alone is not enough. The architecture also needs runtime risk assessment, least-privilege policy, behavioural tracking, and containment.

The data analysis therefore acted as the design justification stage for the artifact.

## 3. Current BMS Communication Model

Current and legacy BMS environments commonly include controllers, sensors, actuators, supervisory systems, and external maintenance devices. BACnet is widely used for building automation communication, especially in HVAC-related systems.

In the dataset scenario, the BMS network includes virtual controllers representing:

| Component | Role in BMS operation |
|---|---|
| Chiller controller | Produces and transfers chilled water for cooling |
| Air Handling Unit (AHU) | Produces and regulates air for the HVAC system |
| VAV box controller | Regulates airflow and room/zone temperature |
| Weather station | Provides environmental values used by other subsystems |
| Server/supervisory system | Receives BACnet traffic and captures network behaviour |

This reflects a common BMS pattern: multiple specialised controllers exchange operational data with a supervisory system. The challenge is that these systems often prioritise availability and interoperability. Security controls such as strong device identity, encryption, integrity validation, segmentation, and behavioural response may be limited or inconsistently deployed.

## 4. Initial Problem Statement

The dataset and paper show that BMS/BACnet environments face attacks that are difficult to detect using only network headers or static filtering.

The key problem is:

> A device can appear legitimate at the network layer while still sending manipulated, abnormal, or covert data at the application or behavioural layer.

This creates a security gap. Traditional approaches that only check IP address, MAC address, port number, or basic firewall rules may not detect attacks where the packet structure looks normal but the content or timing is malicious.

## 5. Research Question and Hypothesis

### Research Question

The research question derived from the dataset analysis is:

> How can a Zero Trust-inspired SDN architecture detect and contain abnormal communication behaviour in BMS networks using AAA-based identity verification, runtime risk assessment, ABAC policy enforcement, and dynamic quarantine?

### Hypothesis

The working hypothesis is:

> If BMS traffic is controlled through a central SDN controller that combines device identity, runtime risk scoring, least-privilege ABAC policy, and behavioural quarantine, then abnormal or unauthorised communication can be detected and contained more effectively than with static network filtering alone.

This hypothesis follows directly from the dataset analysis. The attacks show that no single security check is sufficient. The architecture therefore uses multiple verification layers.

## 6. Analysis Method

The dataset was treated as evidence for architectural design. The analysis focused on what the traffic revealed about BMS security requirements rather than training a machine-learning model.

The analysis method was:

1. Review the dataset source paper to understand how the BACnet traffic and attacks were generated.
2. Identify the normal and attack PCAP categories.
3. Use Wireshark-style protocol reasoning, especially BACnet/IP traffic over UDP port `47808`.
4. Compare normal traffic with falsifying, modifying, and covert-channel attack behaviour.
5. Extract security requirements from the differences between normal and attack behaviour.
6. Map those requirements to the final Zero Trust-inspired SDN architecture.

The analysis used BACnet/IP as the real BMS protocol motivation. The implemented artifact uses ICMP for repeatable baseline policy testing and UDP `47808` as BACnet-representative traffic in the advanced validation.

### 6.1 Packet-Level Observations Used in the Analysis

The Wireshark analysis showed a small BACnet/IP network with one central polling device and four field devices:

| IP address | Observed role |
|---|---|
| `172.120.236.70` | Central controller/supervisory polling device |
| `172.120.236.60` | Field device |
| `172.120.236.61` | Field device |
| `172.120.236.62` | Field device |
| `172.120.236.63` | Field device |
| `172.120.236.255` | Broadcast address, mainly relevant for BACnet discovery |

The observed protocol stack was Ethernet, IPv4, UDP, and BACnet/IP. BACnet traffic used UDP port `47808`, with BACnet BVLC, NPDU, and APDU layers visible in Wireshark. The main BACnet services observed were `Who-Is`, `I-Am`, `ReadProperty`, `ReadPropertyMultiple`, and response messages such as `Complex-ACK`.

No `WriteProperty` commands were observed in the normal, falsifying, or modifying traces. This is important because the attacks are not visible as direct write/control commands. They instead preserve normal-looking BACnet read behaviour while changing the truthfulness, meaning, timing, or distribution of the data.

The object-name queries returned the name `BAC0`, which suggests the dataset was generated in a simulated BACnet environment. Therefore, individual physical device types cannot be proven from the object-name field alone. The role interpretation is based mainly on communication behaviour, packet direction, and the dataset scenario description.

## 7. Normal Traffic Findings

Normal BACnet traffic showed predictable operational communication between BMS components. The traffic represents the expected behaviour of HVAC-related controllers and a supervisory system.

In the normal trace, the central device `172.120.236.70` communicates with the four field devices and periodically queries their properties. Discovery traffic such as `Who-Is` and `I-Am` is also present, including broadcast communication through `172.120.236.255`. The communication is stable and repetitive, which is consistent with a monitoring-oriented BMS where a supervisory component polls controllers and sensors at regular intervals.

Direct PCAP counting showed that `172.120.236.60` and `172.120.236.62` are already the most frequently polled field devices in normal traffic. This means their high request counts should be treated as part of the baseline process pattern, not as attack evidence by itself.

Key normal-traffic observations:

| Observation | Architectural meaning |
|---|---|
| Controllers communicate periodically | Normal BMS behaviour has predictable patterns |
| Specific devices have specific operational roles | Access control should consider device role |
| Communication is tied to subsystem function | Segmentation by BMS subsystem is meaningful |
| BACnet uses known protocol behaviour | Protocol-aware monitoring can help identify expected traffic |
| Supervisory systems receive data from multiple controllers | Some controller/server roles may require broader access |
| No `WriteProperty` commands are present | The baseline is mainly monitoring rather than direct actuation |
| Normal polling is stable and repetitive | Deviations in request distribution, intensity, or persistence can be suspicious |
| `172.120.236.60` and `172.120.236.62` receive the most reads even in normal traffic | These devices likely represent high-priority process points |

These findings informed the role model in the architecture: controller, sensor, BMS controller, lighting controller, external device, subsystem, trust level, and context.

## 8. Attack Traffic Findings

### 8.1 Falsifying Attack

The paper describes a falsifying attack on the chiller controller where a random value between 4 and 5 degrees Celsius was added to the chilled water supply temperature.

This is best classified as a stealthy false data injection (FDI) or data-integrity attack at the device/application level. It is not a classic network-layer attack such as scanning, flooding, or malformed-packet injection. The network can still contain legitimate BACnet `ReadProperty` and `ReadPropertyMultiple` exchanges, while the value being reported by the compromised data source is false.

In the observed falsifying trace, the overall communication structure remains similar to normal traffic: `172.120.236.70` still communicates with the field devices and no new device-to-device communication appears. The same two field devices, `172.120.236.60` and `172.120.236.62`, remain the most frequently queried devices. However, direct PCAP counting shows that this is also true in the normal trace. Therefore, their high request count is not sufficient evidence of compromise by itself. The stronger attack evidence is the increased request intensity and the shift to `ReadPropertyMultiple` as the dominant read operation.

Security interpretation:

| Observation | Meaning |
|---|---|
| The sender can still appear to be a legitimate controller | Identity alone is not sufficient |
| The manipulated value affects process semantics | Application-layer integrity matters |
| Network headers may still look normal | Header-only filtering is insufficient |
| Only read-based BACnet messages are visible | The attack can be hidden inside legitimate monitoring traffic |
| `172.120.236.60` and `172.120.236.62` remain the most polled field devices | They appear to be high-priority process points, but this is also seen in normal traffic |
| Attack traffic is dominated by `ReadPropertyMultiple` | The attack changes read behaviour while avoiding direct write commands |
| Traffic remains structurally normal but semantically false | The supervisory system may trust data that no longer represents the physical process |

This supports the need for continuous verification and behavioural monitoring. A device should not remain trusted forever only because it authenticated once.

The security impact is cyber-physical. If the chilled water supply temperature is falsified by approximately 4-5 degrees Celsius, the supervisory system may make wrong cooling decisions even though the BACnet traffic appears normal. The dangerous part is that the attack changes the truth of the process value, not necessarily the packet format.

### 8.2 Modifying Attack

The paper describes a modifying attack on the chiller controller where pump on/off statuses were inverted: on was reported as off, and off was reported as on.

This is also a stealthy integrity attack. The reported actuator state is changed before it is trusted by the supervisory layer. A pump that is physically on may be reported as off, or a pump that is physically off may be reported as on. This can create wrong control decisions, inefficient operation, and possible equipment stress.

The modifying trace follows the same centralised structure as the normal and falsifying traces, but the abnormal behaviour is stronger. The controller/supervisory device continues interacting with all field devices, while `172.120.236.60` and `172.120.236.62` remain the most frequently queried devices. Since these two devices are also heavily polled in normal traffic, the safer conclusion is that they are likely important process-point devices in the simulated BMS. The modifying attack evidence is the higher total traffic volume and the almost exclusive use of `ReadPropertyMultiple`/`Complex-ACK` pairs.

Security interpretation:

| Observation | Meaning |
|---|---|
| Operational state can be falsified | Data integrity is a major BMS security concern |
| The traffic can still follow normal BACnet transport patterns | Static port-based rules are not enough |
| A legitimate source can transmit harmful information | Runtime trust and context must be evaluated |
| No direct `WriteProperty` command is required | Malicious impact can occur through false reporting rather than explicit control |
| Pump status can contradict related process values | Behavioural monitoring should check logical consistency, for example pump off but flow greater than zero |
| Higher traffic intensity appears without `WriteProperty` commands | The attack is stealthy at protocol level but suspicious at behavioural level |
| `.60` and `.62` are heavily queried in normal and attack traces | Their importance is process-related; compromise cannot be concluded from request volume alone |

This attack motivated separating authentication from authorisation. Even if a device is known, each communication request still needs policy and risk evaluation.

This also motivates process-aware Zero Trust checks. For example, a response reporting `Pump = OFF` while another value indicates non-zero flow should not be accepted as automatically trustworthy. The architecture therefore needs behavioural and contextual verification, not only identity.

### 8.2.1 Why Two Devices Receive Many Repeated Requests

The observation that `172.120.236.60` and `172.120.236.62` receive many repeated requests must be interpreted carefully. Direct PCAP counting showed that these two devices are also the most frequently queried devices in normal traffic. Therefore, high request volume toward these two IP addresses is not, by itself, proof that they are compromised or uniquely attacked.

The more logical explanation is that these two devices represent high-priority BACnet process points in the simulated BMS. BACnet devices can expose many objects, such as temperature values, pump states, flow values, power values, setpoints, and alarms. Since the attack scenarios concern chiller temperature and pump status, `.60` and `.62` are likely associated with process points that are read more frequently by the supervisory device.

The following PCAP counts support this interpretation:

| PCAP file | Dominant read service | Requests to `.60` | Requests to `.62` | Approximate request rate |
|---|---|---:|---:|---:|
| `Normal-traffic.pcap` | Mostly `ReadProperty` | 618,009 | 617,578 | 27.6 requests/s |
| `Falsifying-in-chiller.pcap` | `ReadPropertyMultiple` | 991,843 | 991,861 | 38.4 requests/s |
| `Modifying-in-chiller.pcap` | `ReadPropertyMultiple` | 1,303,516 | 1,303,540 | 38.4 requests/s |

This means the safest conclusion is not "these two devices are compromised." The safer conclusion is:

> `172.120.236.60` and `172.120.236.62` are high-priority field devices or process-point devices in the simulated BMS. The attack evidence lies in the increased read intensity, the dominance of `ReadPropertyMultiple`, and the absence of direct `WriteProperty` commands, not in the high request count alone.

This distinction matters for the thesis because it avoids overclaiming. The dataset supports the argument that attacks can preserve legitimate BACnet request/response structure while manipulating the reported process values. It does not prove from request counts alone which specific device is compromised.

### 8.3 Covert Channel Attacks

The covert-channel attacks used timing differences in packet transmission to encode a hidden message. The message was represented in three forms: plain text, SHA3-256 hash, and AES-256 encryption.

In the covert-channel traces, the communication structure remains similar to normal traffic: the same centralised BACnet/IP model is used, and no direct device-to-device pattern is introduced. However, deeper inspection shows that `ReadPropertyMultiple` requests follow structured sequential patterns instead of repeatedly querying a fixed set of expected properties.

In the plaintext case, readable values such as object-name-related content can be extracted, which indicates that information is being carried through legitimate BACnet requests. In the hash case, the sequential structure remains but the content is no longer readable. In the encrypted case, the structure remains while the content becomes opaque and difficult to interpret.

Security interpretation:

| Observation | Meaning |
|---|---|
| The attack changes timing rather than obvious packet fields | Behavioural analysis is needed |
| Packet content may not be enough to identify the attack | Traffic pattern monitoring is important |
| Covert channels can hide inside normal-looking BACnet traffic | Zero Trust should consider history and behaviour |
| Plaintext, hash, and encrypted forms progressively reduce readability | Content inspection alone becomes less reliable |
| Sequential request parameters differ from fixed normal polling | Parameter-level behaviour can reveal covert communication |

This finding directly supports using traffic volume, previous denials, and communication history as part of the risk model.

Overall, the main difference between normal and attack traffic is not always the BACnet command type. Normal, falsifying, modifying, and covert-channel traces can all use legitimate read-based BACnet operations. The stronger indicators are communication distribution, persistence, timing, request sequence, and physical/logical consistency.

## 9. Security Limitations Identified

The dataset analysis identified the following limitations in typical BACnet/BMS communication security.

| Limitation | Evidence from analysis | Architectural response |
|---|---|---|
| Weak device identity | Legitimate-looking devices can send malicious data | AAA identity verification |
| Lack of least privilege | BMS devices may communicate based on network reachability | ABAC role/system policy |
| Lack of segmentation | Cross-device and cross-subsystem communication can occur | Subsystem-aware policy |
| Application data manipulation | Temperature and pump values can be falsified or modified | Continuous verification and risk context |
| Covert timing behaviour | Timing can encode hidden information | Behavioural risk scoring |
| Normal command types during attacks | Falsifying and modifying traces still use read-based BACnet services | Do not rely only on command allowlists |
| High-priority repeated polling | `172.120.236.60` and `172.120.236.62` receive many requests in normal and attack traces | Track per-device baselines before judging anomalies |
| Increased read intensity | Falsifying and modifying traces have higher request rates than normal traffic | Use behavioural thresholds and historical comparison |
| Shift in BACnet read service | Attack traces are dominated by `ReadPropertyMultiple` | Monitor service mix, not only allowed ports |
| Physical-process inconsistency | Pump state, flow, power, and temperature can contradict each other | Add process-aware behavioural checks |
| No automatic containment | Compromised behaviour may persist | Quarantine and session revocation |
| Static network control | Basic filtering does not adapt to behaviour | SDN-based dynamic enforcement |

This table is the central link between the dataset and the final architecture.

## 10. How the Analysis Led to the Architecture

The architecture was designed as a response to the dataset findings.

### 10.1 AAA Layer

The dataset showed that BMS devices need explicit identity handling. The architecture therefore begins with AAA-style verification.

However, the falsifying and modifying attacks also show the limitation of AAA. AAA can confirm that a device is known, but it cannot prove that the values produced by that device are truthful after compromise. This is why AAA is necessary but not sufficient.

In the artifact, AAA verifies:

| Field | Purpose |
|---|---|
| Source IP | Confirms the device is known |
| Source MAC | Confirms the device matches the registered identity |
| Device ID | Represents a pre-registered device credential |
| Session | Provides authorisation state and accounting |

AAA answers the first Zero Trust question: **who is making the request?**

### 10.2 Zero Trust Risk Layer

The falsifying, modifying, and covert-channel attacks show that an authenticated device can still behave maliciously. Therefore, the architecture adds runtime risk scoring after AAA.

The risk layer considers:

| Risk input | Dataset-based justification |
|---|---|
| Trust level | Known devices can still be risky |
| Context | Operational state affects whether communication is expected |
| Previous denied attempts | Repeated abnormal behaviour should increase suspicion |
| Cross-system communication | BMS subsystems should not all communicate freely |
| Sensor-to-non-controller communication | Lateral movement should be restricted |
| Packet volume/timing pressure | Covert channels and repeated traffic can appear through behaviour |
| Per-device baseline deviation | Some devices are naturally polled more often, so risk should compare behaviour against baseline rather than raw counts alone |
| BACnet service mix | Attack traces are dominated by `ReadPropertyMultiple`, while normal traffic contains mostly `ReadProperty` |
| Logical inconsistency | False pump or temperature values can conflict with expected physical behaviour |

Zero Trust answers the second question: **is this request risky right now?**

### 10.3 ABAC Policy Layer

The dataset shows that BMS devices have different operational roles. A chiller controller, AHU, VAV controller, weather station, and server should not all have the same access privileges.

ABAC is important because attacks can originate from devices that are already inside the BMS trust boundary. The policy layer restricts which roles may provide critical data, which devices may communicate with controllers, and which subsystem interactions are expected.

The architecture therefore uses ABAC attributes:

| Attribute | Reason |
|---|---|
| Role | Sensors, controllers, and external devices have different permissions |
| Device type | Sensors should not behave like controllers |
| System | HVAC and lighting should be segmented |
| Trust | Unknown/restricted devices should be limited |
| Context | Off-hours or abnormal context changes access decisions |

ABAC answers the third question: **is this communication allowed by least privilege?**

### 10.4 SDN Enforcement Layer

The dataset motivates dynamic control because malicious behaviour may emerge over time. SDN provides a way to enforce decisions immediately.

In the artifact:

| Controller decision | SDN enforcement |
|---|---|
| Allow | Install OpenFlow forwarding rule |
| Deny | Install OpenFlow drop rule |
| Quarantine | Deny future traffic from suspicious source |

SDN answers the fourth question: **how is the decision enforced in the network?**

### 10.5 Quarantine Layer

The attack scenarios show that compromised behaviour may continue after the first malicious event. Therefore, the architecture includes behavioural response.

The quarantine mechanism:

1. Counts denied attempts.
2. Tracks multiple denied destinations.
3. Marks suspicious hosts.
4. Downgrades trust or changes context.
5. Revokes AAA sessions.
6. Applies future deny decisions.

Quarantine answers the final question: **how does the system contain repeated abnormal behaviour?**

## 11. Why This Architecture Is Different From Static Filtering

Static filtering might allow or deny traffic based on IP, port, or subnet. The dataset showed that this is not enough because attacks can keep the same protocol and network structure while changing data values or timing.

The proposed architecture is different because it combines:

| Static filtering | Proposed architecture |
|---|---|
| IP/port-based decisions | Identity, role, trust, context, and behaviour |
| One-time allow/deny rules | Continuous verification for new flows |
| No behavioural memory | Denial history and quarantine |
| Limited explanation | Logged reason, score, and event type |
| Manual policy changes | Controller-installed dynamic OpenFlow rules |

This makes the architecture more suitable for the type of BMS weaknesses observed in the dataset.

## 12. Why ICMP Is Used in the Artifact

The dataset uses BACnet/IP traffic, but the baseline artifact uses ICMP ping for repeatable policy testing. This was a design choice.

The reason is that the thesis tests the access-control architecture, not a full BACnet application stack. ICMP makes it easy to verify whether the controller allows or denies a flow. The same source/destination policy logic applies to BACnet traffic, and the controller includes a BACnet-representative UDP `47808` validation in the advanced tests.

Therefore:

| Dataset role | Artifact role |
|---|---|
| BACnet PCAPs show realistic BMS protocol weaknesses | Architecture requirements are derived from these weaknesses |
| ICMP tests validate access-control decisions repeatably | SDN/Zero Trust/ABAC behaviour is demonstrated clearly |
| UDP `47808` test represents BACnet-style traffic | Shows the controller can recognise BACnet-representative traffic |

This keeps the implementation focused and explainable while still being grounded in BACnet/BMS evidence.

## 13. Final Architecture Derived From the Dataset

The final architecture includes the following layers:

```text
BMS device request
        |
        v
SDN switch sends new flow to POX controller
        |
        v
AAA identity verification
        |
        v
Zero Trust runtime risk assessment
        |
        v
Rate and quarantine checks
        |
        v
ABAC least-privilege policy
        |
        v
OpenFlow allow/drop enforcement
        |
        v
Logging, accounting, and evidence collection
```

Each layer is justified by a dataset finding:

| Dataset finding | Architecture layer |
|---|---|
| Devices may appear legitimate while sending malicious values | AAA plus continuous risk |
| Operational roles matter | ABAC |
| BACnet attacks can preserve network-level normality | Behavioural risk scoring |
| Covert channels exploit timing behaviour | Traffic-volume and history-based risk |
| Repeated suspicious behaviour should not continue | Quarantine |
| Network enforcement must be dynamic | SDN/OpenFlow |
| Evaluation needs explainable evidence | Structured controller logs |

## 14. Conclusion

The BACnet dataset analysis was the starting point for the architecture. It showed that BMS attacks can be subtle: network headers may remain normal, devices may appear legitimate, and malicious behaviour may occur through application values or timing.

From this, the thesis derived a layered Zero Trust-inspired SDN architecture. AAA establishes identity, Zero Trust risk scoring evaluates runtime behaviour, ABAC enforces least privilege, quarantine contains repeated suspicious activity, and SDN applies the decision dynamically through OpenFlow.

The falsifying and modifying chiller scenarios are therefore interpreted as stealthy FDI/data-integrity attacks against the physical process. They are dangerous precisely because everything can look normal at the BACnet command level: the requests are legitimate, the responses are valid BACnet messages, and no obvious write command is required. Only the truth of the reported process value has changed.

The result is an architecture designed specifically to address the weaknesses observed in BACnet/BMS traffic rather than a generic access-control experiment.

## References

1. Kaggle dataset: [BACnet network dataset](https://www.kaggle.com/datasets/78eb45aeaac481853135d90738672111e46fe2a4ce653573e8856fc920f3da68)
2. Moosavi, S. A., Asgari, M., & Kamel, S. R. (2024). [Developing a comprehensive BACnet attack dataset: A step towards improved cybersecurity in building automation systems](https://doi.org/10.1016/j.dib.2024.111192). *Data in Brief*, 57, 111192.
3. ScienceDirect article page: [Developing a comprehensive BACnet attack dataset](https://www.sciencedirect.com/science/article/pii/S2352340924011545)
