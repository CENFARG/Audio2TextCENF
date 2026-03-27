**[Español](SECURITY.md) | [English](SECURITY_EN.md)**

# Security Policy

## Supported Versions

We currently support security updates for the following versions of Audio2Text:

| Version | Supported          |
| ------- | ------------------ |
| 0.9.4   | :white_check_mark: |
| 0.9.2   | :white_check_mark: |
| 0.9.0   | :x:                |
| < 0.9.0 | :x:                |

## Reporting a Vulnerability

The security of Audio2Text is a priority. If you discover a security vulnerability, please help us by following these steps:

### 🔒 Confidential Reporting Process

**DO NOT** create a public GitHub issue for security vulnerabilities.

Instead, please report security vulnerabilities to:

**Email:** cenf.arg@gmail.com

### 📋 Information to Include

To help us understand and resolve the issue quickly, please include:

1. **Description of the problem:**
   - Vulnerability type (e.g., XSS, SQL injection, etc.)
   - Affected code location (file and line if possible)
   - Special configuration required to reproduce

2. **Steps to reproduce:**
   - Step-by-step instructions
   - Proof of Concept (PoC) code if applicable
   - Screenshots or videos if helpful

3. **Potential impact:**
   - What can an attacker do?
   - What data is at risk?
   - How many users are affected?

4. **System information:**
   - Audio2Text version
   - Operating system
   - Python version
   - Any other relevant information

### ⏱️ Response Time

- **Initial confirmation:** Within 48 hours
- **Preliminary assessment:** Within 5 business days
- **Regular updates:** Every 7 days until resolution

### 🛡️ Disclosure Process

We follow the principle of **responsible disclosure**:

1. **Investigation:** We evaluate and verify the report (1-5 days)
2. **Development:** We create and test a fix (variable depending on severity)
3. **Notification:** We inform affected users if necessary
4. **Release:** We publish the corrected version
5. **Disclosure:** We publish details after users have had time to update (typically 30 days)

### 🏆 Acknowledgement

We thank security researchers who report vulnerabilities responsibly:

- We will include your name in our [Security Hall of Fame](docs/SECURITY_HALL_OF_FAME.md) (if desired)
- We will give you credit in the release notes (with your permission)

## 🔐 Security Best Practices for Users

### Secure Configuration

1. **API Keys:**
   - Never share your Groq API key
   - Use environment variables or `config.json` (not versioned)
   - Rotate your keys regularly

2. **Updates:**
   - Keep Audio2Text updated
   - Subscribe to release notifications on GitHub

3. **Permissions:**
   - Run with minimum necessary permissions
   - Do not run as administrator unless necessary

### Sensitive Data

- Audio2Text **DOES NOT** send transcription data to CENF servers
- Transcriptions are sent only to Groq API (according to their [privacy policy](https://groq.com/privacy-policy/))
- Audio files are saved locally
- No telemetry or analytics collected

### Executable Verification

Before running the downloaded `.exe`:

1. Verify the SHA256 hash:
   ```powershell
   Get-FileHash Audio2Text_CENF_0.9.4_GENERAL.exe -Algorithm SHA256
   ```

2. Compare with the hash published in the [Release](https://github.com/CENFARG/Audio2Text/releases)

3. Download only from official sources:
   - GitHub Releases: https://github.com/CENFARG/Audio2Text/releases
   - Official Site: https://cenfarg.com.ar

## 🚨 Known Vulnerabilities

Currently, there are no known vulnerabilities in version 0.9.4.

History of fixed vulnerabilities:
- None to date

## 📞 Contact

For security inquiries:

- **Security Email:** cenf.arg@gmail.com
- **General Email:** cenf.arg@gmail.com
- **GitHub:** [@CENFARG](https://github.com/CENFARG)

## 📚 Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE - Common Weakness Enumeration](https://cwe.mitre.org/)
- [CVE - Common Vulnerabilities and Exposures](https://cve.mitre.org/)

---

**Last updated:** 2025-12-31
**Policy version:** 1.0
