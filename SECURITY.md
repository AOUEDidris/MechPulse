# Security Policy

The MechPulse team takes the security of our industrial vibration monitoring and predictive maintenance software seriously. This document outlines our policy for reporting and resolving security vulnerabilities.

---

## Supported Versions

We provide security updates for the following versions of MechPulse:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

---

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues or discussions.**

If you discover a potential security vulnerability in MechPulse (such as UDP packet buffer overflows, telemetry injection flaws, arbitrary code execution, or insecure deserialization), please report it responsibly by following these steps:

1. **Email Us Privately**: Send an encrypted or plain email to `security@mechpulse.internal` or open a private advisory via GitHub's [Security Advisory tab](https://github.com/mechpulse/mechpulse/security/advisories/new).
2. **Include Key Information**:
   - Component affected (e.g. C++ Edge DSP Core Engine, UDP Receiver, PySide6 Dashboard)
   - Detailed description of the vulnerability
   - Step-by-step instructions or Proof of Concept (PoC) script to reproduce the issue
   - Assessment of potential impact and exploitability
   - Any proposed fix or remediation (if available)

---

## Response Process

When we receive a security report:

1. **Acknowledgment**: We will acknowledge receipt of your vulnerability report within 48 hours.
2. **Assessment & Validation**: The security and development team will verify and triage the finding within 5 business days.
3. **Remediation**: A fix will be developed and tested across our supported platforms.
4. **Coordinated Disclosure**: We will coordinate with you on a disclosure date and release a patch together with an advisory crediting your contribution (unless you prefer anonymity).

---

## Security Best Practices for Deployments

- **Network Isolation**: When deploying the C++ engine and UDP receiver in industrial environments, isolate telemetry streams onto dedicated VLANs or VPN tunnels.
- **Firewall Rules**: Restrict UDP port `9876` (or configured port) access to authorized edge telemetry nodes only.
- **Process Privileges**: Avoid running the native edge engine or GUI dashboard under elevated root/administrator privileges.
