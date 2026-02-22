# Security Policy – AegisCAN-RT

This document outlines the security practices, supported versions, and the process for responsibly reporting vulnerabilities in AegisCAN-RT.

---

## Supported Versions

We actively maintain and provide security updates only for the latest stable release.

| Version      | Supported |
|--------------|-----------|
| Latest (master branch) v3.0.2 | Yes |
| Previous minor release | Limited |
| Older releases v3.0.1 | No |

### Versioning Policy

- The `main` branch always contains the latest secure version.
- Only the latest stable version receives security patches.
- Older versions may not receive updates or fixes.
- Users are strongly encouraged to upgrade to the latest version.

---

## How to Stay Updated

To ensure you are using the most secure version:

1. Pull the latest changes:
   ```bash
   git pull origin main
   ```

2. Regularly update dependencies:
   ```bash
   pip install -r requirements.txt --upgrade
   ```

3. Monitor repository releases and security advisories.

---

## Reporting a Vulnerability

If you discover a security vulnerability, **DO NOT open a public issue.**

Instead, report it privately using one of the following methods:

### Preferred Method (Recommended)

- Use GitHub’s **Private Vulnerability Reporting** feature (if enabled).
- Navigate to the repository → Security → Report a vulnerability.

### Alternative Method

- Contact the maintainer directly via GitHub profile message.

---

## What to Include in Your Report

Please provide:

- A clear description of the vulnerability
- Steps to reproduce the issue
- Potential impact
- Affected version/branch
- Any suggested mitigation (if available)

---

## Response Timeline

- Initial acknowledgment: Within 3–7 days
- Investigation & validation: As soon as possible
- Fix release (if confirmed): In the next security update cycle

We appreciate responsible disclosure and will work to resolve verified issues promptly.

---

## Security Best Practices for Contributors

- Do not commit API keys or `.env` files
- Do not upload private datasets
- Do not expose sensitive logs
- Validate input data to prevent injection attacks
- Keep dependencies updated
- Follow ethical AI development practices

---

## ⚠ Disclaimer

Security vulnerabilities should never be disclosed publicly until reviewed and resolved. Responsible disclosure helps protect users and the project ecosystem.

---

Thank you for helping keep CropVanta.AI secure.
