# Thesis Defense Questions and Answers

This file is a preparation aid for the final defense. It is separate from `Documentation.md` and is not part of the main experiment documentation.

## Short Opening Answers

### 1. What is your thesis about?

My thesis proposes and evaluates a Zero Trust-inspired Software-Defined Networking architecture for Building Management System security. The implementation uses Mininet, Open vSwitch, and a custom POX controller to verify device identity, assess runtime risk, enforce ABAC policy, and quarantine suspicious devices.

### 2. What is the main research question?

The research question is: how can a Zero Trust-inspired SDN architecture detect and contain abnormal communication behaviour in BMS networks using AAA identity verification, runtime risk assessment, ABAC policy enforcement, and dynamic quarantine?

### 3. What is your main contribution?

The contribution is not inventing Zero Trust, SDN, AAA, or ABAC individually. The contribution is integrating them into one transparent BMS-focused proof of concept where each packet decision can be logged, explained, and enforced through SDN.

### 4. What problem are you solving?

BMS networks can contain controllers, sensors, and external devices that should not all communicate freely. If a device is compromised or misconfigured, it may attempt lateral movement or cross-system access. My architecture enforces least privilege and can dynamically contain suspicious communication.

## Architecture and Design

### 5. Why did you use SDN?

SDN separates the control plane from the data plane. The Open vSwitch forwards packets, but the controller makes security decisions. This is useful because access policy, risk assessment, and quarantine can be applied centrally instead of manually configuring every switch.

### 6. Why did you use POX?

POX is lightweight, Python-based, and suitable for proof-of-concept OpenFlow experiments. It allows me to implement the controller logic clearly and inspect every decision. For production, a more modern controller could be used, but POX is sufficient for demonstrating the research idea.

### 7. Why did you use Mininet?

Mininet allows a repeatable simulated network with hosts, switches, and links on one machine. It is appropriate for testing SDN controller behaviour before deploying anything on real BMS equipment.

### 8. Why is this BMS-specific?

The host roles and policies are based on BMS communication patterns: HVAC controller, HVAC sensor, lighting controller, lighting sensor, and external device. The policy enforces subsystem segmentation, sensor-to-controller communication, controller exemptions, and suspicious external access handling.

### 9. What are the five hosts?

h1 is the BMS/HVAC controller, h2 is an HVAC sensor, h3 is a lighting controller, h4 is a lighting sensor with unknown trust, and h5 is an external or abnormal device. They represent a simplified BMS topology.

### 10. Why is the topology small?

The topology is intentionally small so every communication attempt can be mapped directly to a policy decision. The goal is explainability and controlled evaluation, not scale testing.

## Zero Trust, AAA, and ABAC

### 11. How do you define Zero Trust in your work?

Zero Trust means no device is automatically trusted just because it is inside the network. Every new flow is verified using identity, context, risk, policy, and behaviour before access is allowed.

### 12. Is AAA separate from Zero Trust?

No. In my design, AAA is the first Zero Trust verification step. The controller must identify the source device before it can calculate risk or apply policy.

### 13. What does AAA do in the controller?

AAA authenticates the device using registered IP and MAC address, authorises an active session, and records accounting events such as successful authentication, failed authentication, and session revocation.

### 14. Why did you not use a real RADIUS or TACACS+ server?

This is a proof of concept focused on SDN-based enforcement and explainable Zero Trust decision flow. Implementing a full external AAA server would increase deployment complexity without changing the main research contribution.

### 15. Is IP and MAC identity secure enough?

Not for production. IP and MAC identity are used because they are simple and testable in Mininet. In a real deployment, this should be replaced with certificates, 802.1X, signed credentials, or hardware-backed identity.

### 16. What is ABAC?

Attribute-Based Access Control makes decisions based on attributes such as role, device type, subsystem, trust level, and context. In this experiment, ABAC enforces least privilege between BMS devices.

### 17. Why use ABAC instead of simple IP rules?

IP rules are static and do not express device roles or context well. ABAC lets the controller say, for example, sensors may communicate with controllers, but not laterally with other sensors.

### 18. What is the difference between Zero Trust risk and ABAC?

Zero Trust risk asks whether the request is risky right now. ABAC asks whether this device is allowed to perform this communication according to policy. A flow can pass risk assessment but still fail ABAC.

### 19. Can a request be denied before ABAC?

Yes. If the Zero Trust risk score reaches the deny threshold, the controller drops the flow before ABAC. This represents high-risk behaviour that should not continue to policy evaluation.

## Risk Scoring

### 20. How does the risk score work?

The risk score is a deterministic weighted sum. Conditions such as unknown trust, abnormal context, restricted destination, sensor-to-sensor traffic, cross-system communication, previous denials, and elevated packet volume add points.

### 21. Why did you choose a rule-based score?

A rule-based score is transparent, repeatable, and easy to defend. The experiment needs explainable decisions, not a black-box model.

### 22. Is your risk score an official Zero Trust standard?

No. It is an experimental proof-of-concept model inspired by Zero Trust principles. I explicitly do not claim it is an industry standard.

### 23. What are the thresholds?

Below 40, the flow continues to ABAC. From 40 to 69, the flow is monitored but still continues to ABAC. At 70 or above, the flow is denied before ABAC.

### 24. Why can expected ABAC_DENY become observed ZT_DENY?

Because the controller is stateful. Earlier denied attempts increase behavioural risk. A flow that initially would fail ABAC may later be blocked earlier by Zero Trust if the source has accumulated risk.

### 25. Is that a problem?

No, it is part of the dynamic behaviour. The important point is to explain that the observed outcome depends on current state. For independent results, POX should be restarted before each test.

### 26. How is off-hours context calculated?

The controller uses a per-device schedule profile. HVAC devices in this testbed are treated as continuous operation, while lighting field devices use the business-hours schedule. For repeatable tests, `/tmp/bms_controller_hour` can force an hour such as `2` or `10`; otherwise the controller uses the POX process system time.

### 27. Is using system time a limitation?

Yes. It is acceptable for a proof of concept, but production systems should use reliable time synchronisation, configured schedules, and possibly building operation calendars.

### 27a. Why did you add delta-t timing checks?

The BACnet analysis showed that attack traffic can remain protocol-valid while changing behaviour. Delta-t checks let the controller notice unusually short inter-arrival times between new flows from the same device. This is not a full anomaly detector, but it gives transparent timing evidence that can increase Zero Trust risk.

## Policy and Test Cases

### 28. Why do some pings fail?

Failed pings are often the expected result. A blocked ping shows that the controller enforced policy, such as denying cross-system traffic, sensor-to-sensor traffic, or suspicious external access.

### 29. What does T01 test?

T01 tests h2 to h1, an HVAC sensor reporting to the HVAC/BMS controller. It should be allowed if AAA, risk assessment, and ABAC all pass.

### 30. What does T04 test?

T04 tests h2 to h4, sensor-to-sensor lateral communication. It should be denied because sensors should only communicate with controller devices.

### 31. What does T06 test?

T06 tests h1 to h3, where the BMS controller communicates across systems. This is allowed because the BMS controller has a supervisory exemption.

### 32. What does T10 test?

T10 tests repeated denied behaviour from h4. The expected result is behavioural detection, suspicious host logging, quarantine, and AAA session revocation.

### 33. Why is h4 initially unknown trust?

h4 represents a device whose identity is registered but whose operational trust is not strong. This allows the experiment to test unknown-trust behaviour and dynamic containment.

### 34. Why is h5 restricted and abnormal?

h5 represents an external or abnormal device. It is included to test whether the architecture blocks risky communication to protected BMS controllers.

## Controller and Logs

### 35. What happens when a packet arrives?

The switch sends a PacketIn event to POX. The controller handles ARP if needed, extracts IP and MAC details, validates AAA, checks destination registration, refreshes attributes, calculates risk, applies rate and quarantine checks, evaluates ABAC, and installs an allow or drop rule.

### 36. Why are controller logs important?

The logs are the primary evidence. Ping output only shows success or failure, but the controller log explains why a flow was allowed or denied.

### 37. What does EVENT=ZT_ASSESS mean?

It means the controller calculated a runtime risk score for the flow. The log includes the decision, score, and reason.

### 38. What does EVENT=ABAC_DENY mean?

It means the flow passed AAA and Zero Trust risk assessment, but failed the ABAC least-privilege policy.

### 39. What does EVENT=ZT_DENY mean?

It means the flow was considered high-risk and was denied before ABAC evaluation.

### 40. What does EVENT=QUARANTINE_APPLIED mean?

It means the controller detected repeated or multi-destination denied behaviour and marked the host as abnormal, revoked its AAA session, and isolated future traffic.

### 41. Why do logs sometimes show both request and reply directions?

Ping can generate traffic in both directions. Also, after flow rules are deleted between tests, new packets may trigger additional PacketIn events. The controller logs what it sees chronologically.

### 42. Are events grouped per test?

The Mininet scripts print simple test labels before each command. The controller itself is event-driven, so its log remains chronological. Running one test at a time makes the controller events easier to interpret.

### 43. Why did you add `direction="h2 -> h1"`?

The raw IP addresses are still logged for evidence, but the host direction makes logs easier to read during a live demo.

### 44. Why are logs colorized?

Color is only for live readability in the terminal. It helps distinguish allowed traffic, denied traffic, detection, quarantine, and test boundaries. The evidence file remains plain text.

## SDN Enforcement

### 45. How does the switch enforce decisions?

The controller installs OpenFlow rules in Open vSwitch. Allowed flows get forwarding actions, and denied flows get drop rules.

### 46. Why clear flows between tests?

Clearing flows ensures each test reaches the controller again. Otherwise, OVS might already have a rule and the controller would not log a fresh decision.

### 47. What does `ovs-ofctl dump-flows s1` prove?

It shows the actual OpenFlow rules installed in the switch. This proves that the controller decision is enforced in the data plane, not only logged.

### 48. Is the controller a policy decision point or enforcement point?

The controller is the policy decision point. Open vSwitch is the enforcement point because it forwards or drops packets according to controller-installed rules.

## Evaluation and Evidence

### 49. What are your evaluation metrics?

The main evidence is whether flows are allowed or denied as expected, why they were denied, whether authentication works, whether Zero Trust risk is logged, whether quarantine is triggered, whether OpenFlow rules enforce decisions, and the latency logged per request.

### 50. How do you prove detection?

Repeated denied attempts produce `DENY_COUNT`, then `SUSPICIOUS_HOST`, `QUARANTINE_APPLIED`, and `AAA_SESSION_REVOKED`. These log events show detection and containment.

### 51. How do you prove least privilege?

Tests show that expected communication, such as h2 to h1, can be allowed, while lateral or cross-system communication, such as h2 to h4 or h3 to h1, is denied.

### 52. How do you prove identity enforcement?

Advanced tests change h2's MAC address or IP address. The controller detects the mismatch or unknown source and logs authentication failure.

### 53. How do you prove the system is not just blocking everything?

Allowed tests such as h2 to h1 and h1 to h3 show that the controller permits legitimate communication while denying policy violations.

### 54. What does a successful experiment look like?

A successful experiment is not all pings succeeding. It is expected pings succeeding, prohibited pings failing, and controller logs explaining each decision.

## Limitations

### 55. What are the main limitations?

The system uses simulated devices, a small topology, simplified AAA, IP/MAC identity, a rule-based risk score, static attributes, ICMP-based testing, and WSL-specific environment handling.

### 56. Does using Mininet reduce realism?

Yes, it abstracts real BMS hardware. But it is appropriate for controlled SDN policy evaluation. Real deployment would require testing with actual devices and protocols.

### 57. Why use ICMP if BMS uses BACnet or other protocols?

ICMP makes tests simple and repeatable. The controller also includes BACnet-representative UDP port 47808 handling, but the baseline policy is easiest to demonstrate with ping.

### 58. Would this scale to a large building?

The concept can scale architecturally, but this implementation has not been evaluated for large-scale performance. Future work should test more hosts, more switches, and more realistic traffic.

### 59. What are the security weaknesses of your prototype?

The biggest weaknesses are IP/MAC-based identity, static attributes, no encrypted device authentication, and no production-grade policy engine. These are acknowledged proof-of-concept limitations.

### 60. Could an attacker spoof MAC and IP?

In a real network, yes. The advanced tests show that a MAC mismatch is detected, but if an attacker perfectly spoofed both IP and MAC, stronger identity would be needed. Production deployment should use certificates or 802.1X.

## Challenge Questions

### 61. Why not just use VLANs or firewall rules?

VLANs and firewall rules can provide segmentation, but they are often static. This design adds identity, runtime risk, behavioural response, and dynamic SDN enforcement.

### 62. Why not use machine learning for anomaly detection?

Machine learning could be future work, but it would make the decision harder to explain. For a thesis defense, a transparent rule-based model is easier to validate and justify.

### 63. Is this really Zero Trust or just access control?

It is Zero Trust-inspired because it combines continuous verification, least privilege, identity checking, runtime risk, and dynamic response. It is not a complete commercial Zero Trust platform, and I state that clearly.

### 64. What happens if the controller fails?

This proof of concept does not implement controller redundancy. In a production SDN deployment, controller high availability and fail-safe switch behaviour would be required.

### 65. What happens to existing flows after quarantine?

The controller installs drop rules for suspicious traffic and future packets from quarantined hosts are denied. In production, additional cleanup of existing flow rules would be important.

### 66. Why should a BMS controller be allowed cross-system access?

A central BMS controller may need supervisory control or monitoring across subsystems. The exemption is limited to the BMS controller role, not general devices.

### 67. Why is h3 to h1 denied if h1 to h3 is allowed?

The policy is role-sensitive. h1 is the central BMS controller with cross-system exemption, while h3 is a lighting controller and should not initiate HVAC subsystem communication.

### 68. Could a legitimate device be quarantined by mistake?

Yes, false positives are possible with any behavioural system. The threshold is transparent and tunable. In production, quarantine could require additional confirmation or alerting before full isolation.

### 69. Why does state affect later tests?

The architecture intentionally tracks behaviour over time. Denials increase risk and can cause trust downgrade or quarantine. For independent tests, the controller should be restarted before each test.

### 70. What would you improve first?

I would replace IP/MAC identity with certificate-based authentication or 802.1X, add real BACnet traffic, support larger topologies, and evaluate performance under load.

## Quick Defense Phrases

### 71. If asked whether the project is production-ready

No. It is a proof of concept. Its value is demonstrating an integrated, explainable Zero Trust-inspired SDN architecture for BMS communication.

### 72. If asked why a denied ping is good

In this experiment, denial is often the expected security outcome. The key is whether the controller denied the traffic for the correct reason and logged that reason.

### 73. If asked what the strongest part is

The strongest part is explainability: every decision has a logged reason, risk score, source/destination, and enforcement action.

### 74. If asked what the weakest part is

The weakest part is simplified identity. IP/MAC checks are acceptable for Mininet, but production would require cryptographic identity.

### 75. If asked what you learned

I learned that SDN is useful for centralised and dynamic BMS security, but the design must carefully separate identity, risk, policy, and enforcement so decisions remain explainable.
