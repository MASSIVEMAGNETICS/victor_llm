# Security Policy

## Supported Versions

Currently, we support the following versions with security updates:

| Version | Supported          |
| ------- | ------------------ |
| main    | :white_check_mark: |
| develop | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of Victor AGI Framework seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### Where to Report

**Please DO NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via one of the following methods:

1. **Email**: Send details to the repository owner (check GitHub profile)
2. **GitHub Security Advisory**: Use the "Security" tab to report a vulnerability privately

### What to Include

Please include the following information in your report:

- Type of vulnerability (e.g., code injection, privilege escalation, etc.)
- Full paths of source file(s) related to the vulnerability
- Location of the affected source code (tag/branch/commit or direct URL)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the vulnerability, including how an attacker might exploit it

### What to Expect

After you submit a report, you can expect:

1. **Acknowledgment**: Within 48 hours
2. **Initial Assessment**: Within 5 business days
3. **Status Updates**: Regular updates as we investigate
4. **Resolution Timeline**: Depends on severity
   - Critical: 7 days
   - High: 30 days
   - Medium: 60 days
   - Low: 90 days

### Security Update Process

When we receive a security report:

1. We confirm the problem and determine affected versions
2. We audit code to find similar problems
3. We prepare fixes for all supported versions
4. We release patches as soon as possible
5. We publicly disclose the vulnerability after patches are available

### Bug Bounty

We do not currently have a bug bounty program, but we greatly appreciate security researchers who report vulnerabilities responsibly.

### Recognition

With your permission, we will:

- Credit you in the security advisory
- Mention you in the release notes
- Add you to our security researchers hall of fame (if we create one)

## Security Best Practices for Contributors

When contributing to Victor AGI Framework:

### Code Security

- **Input Validation**: Always validate and sanitize user inputs
- **Secure Dependencies**: Check dependencies for known vulnerabilities
- **Least Privilege**: Request only necessary permissions
- **Avoid Hardcoding**: Never commit secrets or credentials
- **Use Secure Functions**: Avoid deprecated or insecure functions

### Common Vulnerabilities to Avoid

1. **Code Injection**
   ```python
   # Bad
   eval(user_input)
   
   # Good
   # Use safe alternatives or proper validation
   ```

2. **Path Traversal**
   ```python
   # Bad
   open(user_provided_path)
   
   # Good
   import os
   safe_path = os.path.abspath(user_provided_path)
   if safe_path.startswith(allowed_directory):
       open(safe_path)
   ```

3. **SQL Injection** (if using databases)
   ```python
   # Bad
   query = f"SELECT * FROM users WHERE id = {user_id}"
   
   # Good
   query = "SELECT * FROM users WHERE id = ?"
   cursor.execute(query, (user_id,))
   ```

4. **Command Injection**
   ```python
   # Bad
   os.system(f"ls {user_directory}")
   
   # Good
   subprocess.run(["ls", user_directory], check=True)
   ```

### Dependency Security

- Review new dependencies before adding them
- Keep dependencies up to date
- Use `pip install --upgrade` regularly
- Monitor security advisories for used packages

### API Keys and Secrets

- Use environment variables for sensitive data
- Never commit `.env` files
- Use GitHub Secrets for CI/CD
- Rotate keys regularly
- Use least-privilege API keys

### Example: Secure Configuration

```python
import os

# Bad
OPENAI_API_KEY = "sk-1234567890abcdef"

# Good
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")
```

## Security Scanning

Our CI/CD pipeline includes:

- **Bandit**: Static security analysis for Python
- **Safety**: Dependency vulnerability checking
- **CodeQL**: Advanced semantic code analysis (if enabled)
- **Dependency Review**: Checks for vulnerable dependencies in PRs

All PRs must pass security checks before merging.

## Disclosure Policy

- We will coordinate disclosure with you
- We prefer 90-day disclosure timeline
- We will credit you in security advisories (with your permission)
- We will notify affected users appropriately

## Contact

For security-related questions or concerns:

- Check the repository's Security tab
- Open a security advisory (preferred)
- Contact repository maintainers (for non-sensitive questions)

## Updates to This Policy

We may update this security policy from time to time. We will notify users of any material changes by updating the date at the bottom of this policy.

---

**Last Updated**: October 31, 2025

Thank you for helping keep Victor AGI Framework and its users safe!
