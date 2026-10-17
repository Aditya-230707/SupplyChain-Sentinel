# Security Policy

## Supported Versions

Only the latest release on the primary development branch receives active security updates and vulnerability patches.

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1.0 | :x:                |

---

## Reporting a Vulnerability

We take the security of SupplyChain Sentinel and its underlying decision-making pipelines seriously.

If you discover a security vulnerability or suspect an issue with secret handling, prompt injection vulnerabilities, or policy bypasses:

1. **Do NOT open a public GitHub issue.**
2. Send an email to the project maintainers with the subject `[SECURITY] Potential Vulnerability in SupplyChain Sentinel`.
3. Include detailed steps to reproduce the issue, including:
   - Operating system and environment details.
   - Configuration flags or `.env` settings (ensure your private keys are redacted).
   - Minimal reproduction script or payload.
   - Potential impact of the vulnerability.

We will acknowledge receipt within 48 hours and work with you to analyze and remediate the issue prior to public disclosure.

---

## Security Architecture & Design Principles

SupplyChain Sentinel is designed from the ground up for high-trust industrial environments:

- **Strict Secret Redaction**: Cloud credentials (e.g. `NEBIUS_API_KEY`, `TAVILY_API_KEY`) are managed strictly via environment variables, never hardcoded, never serialized into the database, and explicitly redacted from log files and outbound HTTP error responses.
- **Defense-in-Depth Against LLM Jailbreaks & Injections**: Because the pipeline extracts data from public internet sources, raw web text is treated as completely untrusted. Model outputs are never fed into shell executors or raw SQL queries; they are strictly validated against Pydantic models. Furthermore, rule `E-005` mathematically requires all extracted quotes to exist verbatim in retrieved source text.
- **SQL Injection Prevention**: All database interactions use SQLAlchemy 2.0 async parameter binding; raw string SQL interpolation is prohibited.
- **Zero-Key Local Mode**: Sentinel provides full local offline capabilities using Ollama and local fixtures, eliminating external credential exposure when processing sensitive corporate supplier lists.
