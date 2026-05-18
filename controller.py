from pox.core import core
import pox.openflow.libopenflow_01 as of
import time
import datetime
import hashlib
import os
import uuid
from collections import defaultdict
import logging

log = core.getLogger()
# Mininet cleanup (`mn -c`) deletes /tmp/*.log. Keep the controller evidence
# file in /tmp, but avoid the .log suffix so it survives Mininet cleanup.
LOG_PATH = "/tmp/bms_controller_events.txt"
HOST_LABELS = {
    "10.0.0.1": "h1",
    "10.0.0.2": "h2",
    "10.0.0.3": "h3",
    "10.0.0.4": "h4",
    "10.0.0.5": "h5",
}

# ---------------------------------------------------------------------------
# ZERO TRUST IDENTITY LAYER: AAA SERVICE
# ---------------------------------------------------------------------------
# In a real deployment this would be a RADIUS server or TACACS+ service
# running on separate infrastructure. Devices would send their credentials
# to the AAA server during a registration handshake before any data traffic.
#
# In this PoC, AAA is the first Zero Trust verification layer. Every new IPv4
# packet must pass identity verification before risk scoring or policy checks.
# The service provides three functions matching the AAA model:
#
#   Authentication — verify device identity using MAC + device_id
#   Authorisation  — confirm the device is permitted to join the network
#   Accounting     — log all authentication events with timestamps
#
# The device_id acts as a pre-shared credential — in production this would
# be a certificate or cryptographic key issued during device commissioning.
# ---------------------------------------------------------------------------


"""
cp /path/to/bms-zero-trust-sdn/controller.py ~/thesis/pox/ext/bms_controller.py
python pox.py bms_controller
"""


class AAAService:
    """
    Simulated AAA service for BMS device identity management.

    Devices are pre-registered with their MAC address and a device_id
    (acting as a credential). When a device first appears on the network,
    the controller calls authenticate() which verifies the credentials
    and issues a session token. Subsequent packets are validated using
    validate_session() which checks the cached token — no full
    re-authentication needed for the duration of the session.

    In this Zero Trust design, AAA is not a separate alternative to Zero Trust.
    It is the first verification step: establish device identity, maintain the
    session, and produce accounting evidence before ABAC evaluates policy.
    """

    def __init__(self):
        # Pre-registered device credentials
        # Format: ip -> {mac, device_id, role_hint}
        # device_id simulates a pre-shared key or certificate identifier
        # issued during device commissioning
        self.device_registry = {
            "10.0.0.1": {
                "mac": "00:00:00:00:00:01",
                "device_id": "BMS-CTRL-HVAC-001",
                "label": "BMS Controller HVAC",
            },
            "10.0.0.2": {
                "mac": "00:00:00:00:00:02",
                "device_id": "SENSOR-HVAC-001",
                "label": "HVAC Sensor",
            },
            "10.0.0.3": {
                "mac": "00:00:00:00:00:03",
                "device_id": "CTRL-LIGHT-001",
                "label": "Lighting Controller",
            },
            "10.0.0.4": {
                "mac": "00:00:00:00:00:04",
                "device_id": "SENSOR-LIGHT-001",
                "label": "Lighting Sensor",
            },
            "10.0.0.5": {
                "mac": "00:00:00:00:00:05",
                "device_id": "EXT-UNKNOWN-001",
                "label": "External Device",
            },
        }

        # Active sessions: ip -> {token, issued_at, mac}
        self.active_sessions = {}

        # Session duration in seconds — after this the device must
        # re-authenticate. In production this would be minutes/hours.
        self.session_timeout = 300  # 5 minutes for PoC

        # Accounting log: list of all auth events
        self.accounting_log = []

    def _generate_token(self, ip, mac, device_id):
        """
        Generates a session token from device credentials.
        In production this would be a signed JWT or RADIUS Access-Accept.
        Here it is a hash of the credentials combined with a random UUID
        to make each session token unique.
        """
        raw = "{}:{}:{}:{}".format(ip, mac, device_id, uuid.uuid4())
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def authenticate(self, src_ip, src_mac):
        """
        AUTHENTICATION — verifies device identity.

        Checks:
        1. Is the IP registered?
        2. Does the MAC match the registered MAC?

        If both pass, issues a session token and stores it.
        Returns (success: bool, token_or_reason: str)
        """
        registered = self.device_registry.get(src_ip)

        # Step 1: IP must be registered
        if registered is None:
            reason = "device not registered in AAA — IP {} unknown".format(src_ip)
            self._account("AUTH_FAIL", src_ip, src_mac, reason)
            return False, reason

        # Step 2: MAC must match registered MAC
        registered_mac = registered["mac"].lower()
        if registered_mac != src_mac.lower():
            reason = "MAC mismatch for {} — registered={} presented={}".format(
                src_ip, registered_mac, src_mac.lower()
            )
            self._account("AUTH_FAIL", src_ip, src_mac, reason)
            return False, reason

        # Both checks passed — generate and store session token
        device_id = registered["device_id"]
        token = self._generate_token(src_ip, src_mac, device_id)

        self.active_sessions[src_ip] = {
            "token": token,
            "issued_at": time.time(),
            "mac": src_mac.lower(),
            "device_id": device_id,
            "label": registered["label"],
        }

        reason = "AAA authenticated {} ({}) — session token issued".format(
            src_ip, registered["label"]
        )
        self._account("AUTH_OK", src_ip, src_mac, reason)
        return True, reason

    def validate_session(self, src_ip, src_mac):
        """
        AUTHORISATION — validates an existing session.

        Called for every subsequent packet after the first authentication.
        Checks that a valid session exists and has not expired.
        If the session has expired, triggers re-authentication.
        Returns (valid: bool, reason: str)
        """
        session = self.active_sessions.get(src_ip)

        # No session exists yet — trigger fresh authentication
        if session is None:
            return self.authenticate(src_ip, src_mac)

        # Check session has not expired
        elapsed = time.time() - session["issued_at"]
        if elapsed > self.session_timeout:
            log_event(
                "AAA_SESSION_EXPIRED",
                level="warning",
                src=src_ip,
                reason="session expired after {:.0f} seconds".format(elapsed),
            )
            del self.active_sessions[src_ip]
            return self.authenticate(src_ip, src_mac)

        # Check MAC matches the session MAC (detects mid-session spoofing)
        if session["mac"] != src_mac.lower():
            reason = (
                "mid-session MAC change detected for {} — possible spoofing".format(
                    src_ip
                )
            )
            self._account("AUTH_FAIL", src_ip, src_mac, reason)
            # Revoke the existing session immediately
            del self.active_sessions[src_ip]
            return False, reason

        return True, "session valid for {} ({})".format(src_ip, session["label"])

    def revoke_session(self, src_ip):
        """
        Revokes a device's session — called when a device is quarantined.
        Ensures a quarantined device cannot use a cached session token
        to bypass future authentication checks.
        """
        if src_ip in self.active_sessions:
            del self.active_sessions[src_ip]
            self._account(
                "SESSION_REVOKED", src_ip, "", "quarantine triggered revocation"
            )

    def _account(self, event_type, ip, mac, detail):
        """
        ACCOUNTING — records all authentication events with timestamps.
        This is the third pillar of AAA. In production these records
        would be sent to a SIEM or centralised logging system.
        """
        entry = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "event": event_type,
            "ip": ip,
            "mac": mac,
            "detail": detail,
        }
        self.accounting_log.append(entry)
        log_event(
            "AAA_{}".format(event_type),
            src=ip,
            mac=mac,
            reason=detail,
        )

    def print_accounting_summary(self):
        """Prints the full accounting log at session end."""
        auth_ok = sum(1 for e in self.accounting_log if e["event"] == "AUTH_OK")
        auth_fail = sum(1 for e in self.accounting_log if e["event"] == "AUTH_FAIL")
        revoked = sum(1 for e in self.accounting_log if e["event"] == "SESSION_REVOKED")
        log_event(
            "AAA_SUMMARY",
            total=len(self.accounting_log),
            auth_ok=auth_ok,
            auth_fail=auth_fail,
            revoked=revoked,
            active_sessions=len(self.active_sessions),
        )


# Instantiate the AAA service — single shared instance
aaa = AAAService()


# ---------------------------------------------------------------------------
# ABAC ATTRIBUTE REGISTRY
# This is separate from the AAA device registry. AAA handles the first Zero
# Trust identity check. ABAC handles access policy after identity and runtime
# risk have been evaluated.
# ---------------------------------------------------------------------------
host_attributes = {
    "10.0.0.1": {
        "role": "bms_controller",
        "device_type": "controller",
        "system": "hvac",
        "trust": "trusted",
        "context": "normal",
    },
    "10.0.0.2": {
        "role": "sensor",
        "device_type": "sensor",
        "system": "hvac",
        "trust": "trusted",
        "context": "normal",
    },
    "10.0.0.3": {
        "role": "lighting_controller",
        "device_type": "controller",
        "system": "lighting",
        "trust": "trusted",
        "context": "normal",
    },
    "10.0.0.4": {
        "role": "sensor",
        "device_type": "sensor",
        "system": "lighting",
        "trust": "unknown",
        "context": "normal",
    },
    "10.0.0.5": {
        "role": "external",
        "device_type": "unknown",
        "system": "unknown",
        "trust": "restricted",
        "context": "abnormal",
    },
}

# ---------------------------------------------------------------------------
# BUSINESS HOURS
# Off-hours restriction applies only to sensors and unknown devices.
# Controllers are always exempt.
# ---------------------------------------------------------------------------
BUSINESS_HOURS_START = 8
BUSINESS_HOURS_END = 18
OFF_HOURS_EXEMPT_ROLES = {"bms_controller", "lighting_controller"}

# ---------------------------------------------------------------------------
# RATE LIMITING
# ---------------------------------------------------------------------------
RATE_LIMIT_PACKETS = 20
RATE_LIMIT_WINDOW = 5

# ---------------------------------------------------------------------------
# BEHAVIORAL TRACKING
# ---------------------------------------------------------------------------
deny_counter = defaultdict(int)
deny_destinations = defaultdict(set)
deny_threshold = 3
multi_destination_threshold = 2
quarantined_hosts = set()
rate_counter = defaultdict(list)

# ---------------------------------------------------------------------------
# EVALUATION METRICS
# ---------------------------------------------------------------------------
metrics = {
    "total_requests": 0,
    "allowed_requests": 0,
    "denied_requests": 0,
    "auth_failures": 0,
    "zero_trust_denies": 0,
    "zero_trust_high_risk": 0,
    "rate_limit_drops": 0,
    "detections": 0,
    "quarantines": 0,
    "latencies": [],
}

# ---------------------------------------------------------------------------
# MAC LEARNING TABLE
# ---------------------------------------------------------------------------
mac_to_port = {}


def learn_mac(connection_id, mac, port):
    if connection_id not in mac_to_port:
        mac_to_port[connection_id] = {}
    mac_to_port[connection_id][mac] = port


def _format_log_value(value):
    text = str(value)
    text = text.replace("\n", " ").replace("|", "/")
    if text == "" or " " in text or ";" in text:
        text = '"' + text.replace('"', "'") + '"'
    return text


def _host_label(ip):
    return HOST_LABELS.get(str(ip), str(ip))


def _flow_direction(src_ip, dst_ip):
    return "{} -> {}".format(_host_label(src_ip), _host_label(dst_ip))


def log_event(event_type, level="info", **fields):
    """
    Write compact event-style logs for experiment evidence.

    Example:
    EVENT=ALLOW | src=10.0.0.2 | dst=10.0.0.1 | score=0 | reason="ICMP allowed"
    """
    if "src" in fields and "dst" in fields and "direction" not in fields:
        fields["direction"] = _flow_direction(fields["src"], fields["dst"])

    preferred_order = [
        "src",
        "dst",
        "direction",
        "mac",
        "decision",
        "score",
        "count",
        "latency_ms",
        "reason",
        "path",
    ]
    parts = ["EVENT={}".format(event_type)]
    used = set()
    for key in preferred_order:
        if key in fields:
            parts.append("{}={}".format(key, _format_log_value(fields[key])))
            used.add(key)
    for key in sorted(k for k in fields if k not in used):
        parts.append("{}={}".format(key, _format_log_value(fields[key])))
    logger = getattr(log, level)
    logger(" | ".join(parts))


def _latency_ms(seconds):
    return "{:.3f}".format(seconds * 1000.0)


def setup_file_logger():
    open(LOG_PATH, "a").close()
    os.chmod(LOG_PATH, 0o666)
    for handler in logging.getLogger().handlers:
        if (
            isinstance(handler, logging.FileHandler)
            and handler.baseFilename == LOG_PATH
        ):
            log_event("LOG_READY", path=LOG_PATH, reason="file logger already active")
            return

    file_handler = logging.FileHandler(LOG_PATH)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    logging.getLogger().addHandler(file_handler)
    log_event("LOG_READY", path=LOG_PATH, reason="file logger started")


# ---------------------------------------------------------------------------
# RATE LIMITING
# ---------------------------------------------------------------------------
def check_rate_limit(src_ip):
    now = time.time()
    rate_counter[src_ip].append(now)
    rate_counter[src_ip] = [
        t for t in rate_counter[src_ip] if now - t <= RATE_LIMIT_WINDOW
    ]
    count = len(rate_counter[src_ip])
    if count >= RATE_LIMIT_PACKETS:
        return False, "rate limit exceeded — {} packets in {}s".format(
            count, RATE_LIMIT_WINDOW
        )
    return True, "rate within limit"


# ---------------------------------------------------------------------------
# DYNAMIC ATTRIBUTE FUNCTIONS
# ---------------------------------------------------------------------------
def get_dynamic_trust(ip):
    base_trust = host_attributes.get(ip, {}).get("trust", "unknown")
    denial_count = deny_counter[ip]
    if base_trust == "trusted" and denial_count >= 2:
        log_event(
            "TRUST_DOWNGRADE",
            level="warning",
            src=ip,
            count=denial_count,
            reason="trusted device demoted to limited after repeated denials",
        )
        return "limited"
    return base_trust


def get_dynamic_context(ip):
    base_context = host_attributes.get(ip, {}).get("context", "normal")
    if base_context == "abnormal":
        return "abnormal"
    role = host_attributes.get(ip, {}).get("role", "")
    if role in OFF_HOURS_EXEMPT_ROLES:
        return "normal"
    current_hour = datetime.datetime.now().hour
    if current_hour < BUSINESS_HOURS_START or current_hour >= BUSINESS_HOURS_END:
        log_event(
            "OFF_HOURS_CONTEXT",
            level="warning",
            src=ip,
            reason="non-exempt role active outside business hours",
            current_hour=current_hour,
        )
        return "off-hours"
    return "normal"


def refresh_attributes(ip):
    if ip not in host_attributes:
        return None
    attrs = dict(host_attributes[ip])
    attrs["trust"] = get_dynamic_trust(ip)
    attrs["context"] = get_dynamic_context(ip)
    return attrs


# ---------------------------------------------------------------------------
# ZERO TRUST RISK ENGINE
# ---------------------------------------------------------------------------
class ZeroTrustEngine:
    """
    Implements continuous verification for the Zero Trust experiment.

    AAA is the first Zero Trust control because every packet must be tied to a
    known device identity. This engine then scores the already-authenticated
    flow using runtime context and behaviour before rate enforcement and ABAC.
    """

    monitor_threshold = 40
    deny_threshold = 70

    def assess(self, src_ip, dst_ip, src_attr, dst_attr):
        score = 0
        reasons = []

        self._add_if(
            src_attr["trust"] == "unknown",
            35,
            "source trust is unknown",
            reasons,
        )
        self._add_if(
            src_attr["trust"] == "limited",
            45,
            "source trust has been dynamically limited",
            reasons,
        )
        self._add_if(
            src_attr["trust"] == "restricted",
            50,
            "source trust is restricted",
            reasons,
        )
        self._add_if(
            src_attr["context"] == "off-hours",
            35,
            "source is active outside business hours",
            reasons,
        )
        self._add_if(
            src_attr["context"] == "abnormal",
            60,
            "source context is abnormal",
            reasons,
        )
        self._add_if(
            dst_attr["context"] == "abnormal",
            30,
            "destination context is abnormal",
            reasons,
        )
        self._add_if(
            dst_attr["trust"] == "restricted",
            35,
            "destination trust is restricted",
            reasons,
        )
        self._add_if(
            src_attr["device_type"] == "sensor"
            and dst_attr["device_type"] != "controller",
            15,
            "sensor is attempting non-controller communication",
            reasons,
        )
        self._add_if(
            src_attr["system"] != dst_attr["system"]
            and src_attr["role"] != "bms_controller",
            20,
            "non-BMS-controller cross-system communication",
            reasons,
        )
        self._add_if(
            deny_counter[src_ip] >= 1,
            min(deny_counter[src_ip] * 10, 30),
            "source has previous denied attempts",
            reasons,
        )
        self._add_if(
            len(deny_destinations[src_ip]) >= 1,
            min(len(deny_destinations[src_ip]) * 10, 20),
            "source has attempted denied destinations",
            reasons,
        )
        self._add_if(
            len(rate_counter[src_ip]) >= RATE_LIMIT_PACKETS // 2,
            10,
            "source is generating elevated packet volume",
            reasons,
        )

        score = sum(weight for weight, _ in reasons)
        reason_text = (
            "; ".join(reason for _, reason in reasons) or "baseline verified flow"
        )

        if score >= self.deny_threshold:
            decision = "deny"
        elif score >= self.monitor_threshold:
            decision = "monitor"
        else:
            decision = "allow"

        return decision, score, reason_text

    def _add_if(self, condition, weight, reason, reasons):
        if condition:
            reasons.append((weight, reason))


zero_trust = ZeroTrustEngine()


# ---------------------------------------------------------------------------
# ARP HANDLER
# ---------------------------------------------------------------------------
def handle_arp(event):
    packet = event.parsed
    learn_mac(event.connection.ID, str(packet.src), event.port)
    msg = of.ofp_packet_out()
    msg.data = event.ofp
    msg.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
    event.connection.send(msg)


# ---------------------------------------------------------------------------
# BEHAVIORAL TRACKING AND QUARANTINE
# ---------------------------------------------------------------------------
def update_deny_behavior(src_ip, dst_ip):
    deny_counter[src_ip] += 1
    deny_destinations[src_ip].add(dst_ip)
    log_event(
        "DENY_COUNT",
        level="warning",
        src=src_ip,
        dst=dst_ip,
        count=deny_counter[src_ip],
        reason="denied attempt recorded",
    )
    repeated_denies = deny_counter[src_ip] >= deny_threshold
    multi_dest_denies = len(deny_destinations[src_ip]) >= multi_destination_threshold
    if repeated_denies or multi_dest_denies:
        if src_ip not in quarantined_hosts:
            quarantined_hosts.add(src_ip)
            metrics["detections"] += 1
            metrics["quarantines"] += 1
            if src_ip in host_attributes:
                host_attributes[src_ip]["context"] = "abnormal"
            # Revoke AAA session when quarantine is applied
            aaa.revoke_session(src_ip)
            log_event(
                "SUSPICIOUS_HOST",
                level="warning",
                src=src_ip,
                count=deny_counter[src_ip],
                reason="repeated or multi-destination denials detected",
            )
            log_event(
                "QUARANTINE_APPLIED",
                level="warning",
                src=src_ip,
                reason="host context set to abnormal and session revoked",
            )


# ---------------------------------------------------------------------------
# ABAC POLICY ENGINE
# ---------------------------------------------------------------------------
def evaluate_abac(src_ip, dst_ip, ip_packet):
    src_attr = refresh_attributes(src_ip)
    dst_attr = refresh_attributes(dst_ip)

    if src_attr is None:
        return False, "unknown source attributes"
    if dst_attr is None:
        return False, "unknown destination attributes"

    # Rule 2: Source context
    if src_attr["context"] == "abnormal":
        return False, "source context is flagged as abnormal"
    if src_attr["context"] == "off-hours":
        return False, "off-hours context: sensor communication restricted"

    # Bidirectional: Destination context
    if dst_attr["context"] == "abnormal":
        return False, "destination context is flagged as abnormal"

    # Rule 3: Source trust
    if src_attr["trust"] != "trusted":
        return False, "source trust level is '{}', access denied".format(
            src_attr["trust"]
        )

    # Bidirectional: Destination trust
    if dst_attr["trust"] == "restricted":
        return False, "destination trust is restricted"

    # Rule 4: Device type
    if src_attr["device_type"] == "sensor" and dst_attr["device_type"] != "controller":
        return False, "sensor can only communicate with a controller device"

    # Rule 5: System segmentation
    if (
        src_attr["system"] != dst_attr["system"]
        and src_attr["role"] != "bms_controller"
    ):
        return False, "cross-system communication denied"

    # Rule 6: Protocol
    udp_seg = ip_packet.find("udp")
    if udp_seg and udp_seg.dstport == 47808:
        return True, "BACnet-representative UDP traffic allowed by ABAC policy"
    icmp_seg = ip_packet.find("icmp")
    if icmp_seg:
        return True, "ICMP allowed by ABAC policy"
    return True, "general IPv4 traffic allowed by ABAC policy"


# ---------------------------------------------------------------------------
# FLOW RULE INSTALLATION
# ---------------------------------------------------------------------------
def install_allow_rule(event, packet):
    learn_mac(event.connection.ID, str(packet.src), event.port)
    conn_table = mac_to_port.get(event.connection.ID, {})
    dst_mac = str(packet.dst)
    out_port = conn_table.get(dst_mac, of.OFPP_FLOOD)
    msg = of.ofp_flow_mod()
    msg.match = of.ofp_match.from_packet(packet, event.port)
    msg.idle_timeout = 30
    msg.hard_timeout = 60
    msg.actions.append(of.ofp_action_output(port=out_port))
    msg.data = event.ofp
    event.connection.send(msg)


def install_drop_rule(event, packet):
    msg = of.ofp_flow_mod()
    msg.match = of.ofp_match.from_packet(packet, event.port)
    msg.idle_timeout = 30
    msg.hard_timeout = 60
    event.connection.send(msg)


# ---------------------------------------------------------------------------
# MAIN PACKET HANDLER
# ---------------------------------------------------------------------------
def _handle_PacketIn(event):
    packet = event.parsed
    if not packet.parsed:
        return

    if packet.find("arp"):
        handle_arp(event)
        return

    ip_packet = packet.find("ipv4")
    if ip_packet is None:
        return

    src_ip = str(ip_packet.srcip)
    dst_ip = str(ip_packet.dstip)
    src_mac = str(packet.src)

    start_time = time.time()
    metrics["total_requests"] += 1

    # ── ZERO TRUST STEP 1: AAA IDENTITY VERIFICATION ─────────────────────────
    # validate_session() handles both first-time authentication and
    # subsequent session validation in one call.
    # The packet cannot proceed to rate, risk, or ABAC checks until its source
    # identity has been verified.
    auth_ok, auth_reason = aaa.validate_session(src_ip, src_mac)
    if not auth_ok:
        install_drop_rule(event, packet)
        latency = time.time() - start_time
        metrics["denied_requests"] += 1
        metrics["auth_failures"] += 1
        metrics["latencies"].append(latency)
        log_event(
            "AAA_DENY",
            level="warning",
            src=src_ip,
            dst=dst_ip,
            mac=src_mac,
            latency_ms=_latency_ms(latency),
            reason=auth_reason,
        )
        return

    # ── ZERO TRUST STEP 2: DESTINATION REGISTRY CHECK ────────────────────────
    if host_attributes.get(dst_ip) is None:
        install_drop_rule(event, packet)
        latency = time.time() - start_time
        metrics["denied_requests"] += 1
        metrics["auth_failures"] += 1
        metrics["latencies"].append(latency)
        log_event(
            "AAA_DESTINATION_DENY",
            level="warning",
            src=src_ip,
            dst=dst_ip,
            latency_ms=_latency_ms(latency),
            reason="destination is not registered",
        )
        return

    src_attr = refresh_attributes(src_ip)
    dst_attr = refresh_attributes(dst_ip)
    if src_attr is None or dst_attr is None:
        install_drop_rule(event, packet)
        latency = time.time() - start_time
        metrics["denied_requests"] += 1
        metrics["latencies"].append(latency)
        log_event(
            "ATTRIBUTE_DENY",
            level="warning",
            src=src_ip,
            dst=dst_ip,
            latency_ms=_latency_ms(latency),
            src_registered=bool(src_attr),
            dst_registered=bool(dst_attr),
            reason="source or destination attributes missing",
        )
        return

    # ── ZERO TRUST STEP 3: CONTINUOUS RISK ASSESSMENT ────────────────────────
    # AAA has verified identity. The controller now evaluates runtime risk
    # before rate/quarantine enforcement and ABAC policy evaluation.
    zt_decision, zt_score, zt_reason = zero_trust.assess(
        src_ip, dst_ip, src_attr, dst_attr
    )
    log_event(
        "ZT_ASSESS",
        src=src_ip,
        dst=dst_ip,
        decision=zt_decision.upper(),
        score=zt_score,
        reason=zt_reason,
    )

    if zt_decision == "deny":
        install_drop_rule(event, packet)
        latency = time.time() - start_time
        metrics["denied_requests"] += 1
        metrics["zero_trust_denies"] += 1
        metrics["zero_trust_high_risk"] += 1
        metrics["latencies"].append(latency)
        log_event(
            "ZT_DENY",
            level="warning",
            src=src_ip,
            dst=dst_ip,
            score=zt_score,
            latency_ms=_latency_ms(latency),
            reason=zt_reason,
        )
        update_deny_behavior(src_ip, dst_ip)
        return

    if zt_decision == "monitor":
        metrics["zero_trust_high_risk"] += 1

    # ── ZERO TRUST STEP 4: RATE LIMITING ─────────────────────────────────────
    rate_ok, rate_reason = check_rate_limit(src_ip)
    if not rate_ok:
        install_drop_rule(event, packet)
        latency = time.time() - start_time
        metrics["denied_requests"] += 1
        metrics["rate_limit_drops"] += 1
        metrics["latencies"].append(latency)
        log_event(
            "RATE_LIMIT_DENY",
            level="warning",
            src=src_ip,
            dst=dst_ip,
            score=zt_score,
            latency_ms=_latency_ms(latency),
            reason=rate_reason,
        )
        return

    # ── ZERO TRUST STEP 5: QUARANTINE FAST-PATH ──────────────────────────────
    if src_ip in quarantined_hosts:
        install_drop_rule(event, packet)
        latency = time.time() - start_time
        metrics["denied_requests"] += 1
        metrics["latencies"].append(latency)
        log_event(
            "QUARANTINE_DENY",
            level="warning",
            src=src_ip,
            dst=dst_ip,
            score=zt_score,
            latency_ms=_latency_ms(latency),
            reason="source is already quarantined",
        )
        return

    # ── ZERO TRUST STEP 6: ABAC LEAST-PRIVILEGE POLICY ───────────────────────
    decision, reason = evaluate_abac(src_ip, dst_ip, ip_packet)
    latency = time.time() - start_time
    metrics["latencies"].append(latency)

    if decision:
        metrics["allowed_requests"] += 1
        log_event(
            "ALLOW",
            src=src_ip,
            dst=dst_ip,
            score=zt_score,
            latency_ms=_latency_ms(latency),
            reason=reason,
        )
        install_allow_rule(event, packet)
    else:
        metrics["denied_requests"] += 1
        log_event(
            "ABAC_DENY",
            src=src_ip,
            dst=dst_ip,
            score=zt_score,
            latency_ms=_latency_ms(latency),
            reason=reason,
        )
        update_deny_behavior(src_ip, dst_ip)
        install_drop_rule(event, packet)


# ---------------------------------------------------------------------------
# METRICS SUMMARY ON SHUTDOWN
# ---------------------------------------------------------------------------
def print_final_metrics():
    summary = {
        "total": metrics["total_requests"],
        "allowed": metrics["allowed_requests"],
        "denied": metrics["denied_requests"],
        "auth_failures": metrics["auth_failures"],
        "zt_denies": metrics["zero_trust_denies"],
        "zt_high_risk": metrics["zero_trust_high_risk"],
        "rate_limit_drops": metrics["rate_limit_drops"],
        "detections": metrics["detections"],
        "quarantines": metrics["quarantines"],
    }
    if metrics["latencies"]:
        avg_lat = sum(metrics["latencies"]) / len(metrics["latencies"])
        summary["avg_latency_ms"] = _latency_ms(avg_lat)
        summary["min_latency_ms"] = _latency_ms(min(metrics["latencies"]))
        summary["max_latency_ms"] = _latency_ms(max(metrics["latencies"]))
    summary["quarantined_hosts"] = ",".join(sorted(quarantined_hosts)) or "none"
    log_event("FINAL_SUMMARY", **summary)
    aaa.print_accounting_summary()
    log_event("LOG_SAVED", path=LOG_PATH)


# ---------------------------------------------------------------------------
# LAUNCH
# ---------------------------------------------------------------------------
def launch():
    import atexit

    setup_file_logger()
    atexit.register(print_final_metrics)
    core.openflow.addListenerByName("PacketIn", _handle_PacketIn)
    log_event(
        "STARTUP",
        controller="BMS Zero Trust SDN",
        model="AAA identity + runtime risk + ABAC policy",
        path=LOG_PATH,
    )
    log_event(
        "BUSINESS_HOURS",
        start="{:02d}:00".format(BUSINESS_HOURS_START),
        end="{:02d}:00".format(BUSINESS_HOURS_END),
        exempt_roles="bms_controller,lighting_controller",
        reason="controllers exempt; sensors and non-exempt roles restricted off-hours",
    )
    log_event("AAA_READY", devices=len(aaa.device_registry))
    log_event(
        "ZT_READY",
        monitor_threshold=zero_trust.monitor_threshold,
        deny_threshold=zero_trust.deny_threshold,
    )
