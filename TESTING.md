# Testing and Validation

This file summarises the repeatable tests included with the thesis artifact.

## Evidence Principle

Failed pings are not automatically failed experiments. In this project, a failed ping often means the controller correctly enforced segmentation, least privilege, or quarantine.

The primary evidence is the controller log:

```text
/tmp/bms_controller_events.txt
```

Ping output shows whether traffic passed. Controller events explain why.

## Baseline Test Script

Run from inside the Mininet CLI:

```text
source ping_test.mn
```

| Test | Traffic | Expected meaning |
|---|---|---|
| T01 | h2 -> h1 | Trusted HVAC sensor to HVAC controller should be allowed |
| T02 | h1 -> h2 | BMS controller to HVAC sensor should be allowed |
| T03 | h2 -> h3 | Cross-system sensor traffic should be denied |
| T04 | h2 -> h4 | Sensor-to-sensor lateral movement should be denied |
| T05 | h3 -> h1 | Lighting controller to HVAC subsystem should be denied |
| T06 | h1 -> h3 | BMS controller supervisory exemption should allow cross-system access |
| T07 | h4 -> h3 | Unknown-trust lighting sensor should be denied or monitored then denied |
| T08 | h5 -> h1 | External abnormal device should be denied |
| T09 | h2 -> h5 | Restricted destination should be denied |
| T10 | repeated h4 attempts | Repeated denied behaviour should trigger quarantine |
| T11 | h4 after quarantine | Quarantined host should remain blocked |
| T12 | rapid h2 requests | Rate-limit evidence may appear if enough PacketIn events are produced |

## Advanced Test Script

Run from inside the Mininet CLI:

```text
source advanced_test.mn
```

| Test | Purpose |
|---|---|
| A01 | Show allow decision and OpenFlow table enforcement |
| A02 | Verify MAC spoofing is blocked by AAA |
| A03 | Verify unknown source IP is blocked by AAA |
| A04 | Validate BACnet-representative UDP port `47808` path |
| A05 | Trigger quarantine through repeated denied behaviour |
| A06 | Confirm quarantine persists |
| A07 | Print a compact evidence summary from the controller log |

## Important Events

| Event | Meaning |
|---|---|
| `EVENT=AAA_AUTH_OK` | Source identity/session accepted |
| `EVENT=AAA_AUTH_FAIL` | Source identity failed |
| `EVENT=ZT_ASSESS` | Runtime risk score calculated |
| `EVENT=ALLOW` | Flow allowed and OpenFlow rule installed |
| `EVENT=ABAC_DENY` | Least-privilege policy denied the flow |
| `EVENT=ZT_DENY` | Risk score denied the flow before ABAC |
| `EVENT=DENY_COUNT` | Behavioural denial counter increased |
| `EVENT=SUSPICIOUS_HOST` | Host identified as suspicious |
| `EVENT=QUARANTINE_APPLIED` | Host isolated and session revoked |
| `EVENT=RATE_LIMIT_DENY` | Source exceeded the configured packet threshold |

## Reproducibility Notes

The controller is stateful. Previous denials increase risk and can change later outcomes from `ABAC_DENY` to `ZT_DENY` or `QUARANTINE_DENY`.

For independent test runs, restart POX and clear Mininet flows:

```text
sh ovs-ofctl del-flows s1
```

For a fully clean run, exit Mininet, restart POX, and start `bash mininet.sh` again.
