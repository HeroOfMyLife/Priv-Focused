# 🎭 Kegorak-ID Vault

> **A cyberpunk-styled identity management system with military-grade encryption, breach monitoring, and hacker aesthetics.**

## 🚀 Features

### 🔐 Security
- **AES-256-GCM Encryption**: Bank-level encryption for all stored identities
- **PBKDF2 Key Derivation**: 100,000 iterations to prevent brute-force attacks
- **Zero-Knowledge Architecture**: Master password never leaves your device
- **Custom .AADI Format**: Proprietary encrypted container with integrity checking

### 🛡️ Protection
- **Breach Monitoring**: Detects if usernames appear in known breach databases
- **Security Scoring**: Visual password strength indicators (☠️🤷✅)
- **Hold-to-Shred**: 2-second hold requirement prevents accidental deletion
- **Master Password Recovery**: Security question fallback (with vault reset warning)

### 🎨 User Experience
- **Cyberpunk UI**: Dark mode with animated floating skulls and terminal-style header
- **Sound Feedback**: Audio cues for actions (Windows) or silent fallback
- **Demo Mode**: One-click load of test identities for presentations
- **Responsive Design**: Works on Windows, macOS, and Linux

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Language** | Python 3.8+ | Main programming language |
| **GUI Framework** | CustomTkinter | Modern, themed user interface |
| **Cryptography** | `cryptography` library | AES-256-GCM, PBKDF2, secure key handling |
| **Storage** | Custom `.aadi` binary format | Encrypted vault file |
| **Hashing** | `hashlib` (PBKDF2-HMAC-SHA256) | Master password verification |
| **Sound** | `winsound` (Windows) / fallback | UI feedback audio |

---

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Quick Start
```bash
# Clone the repository
git clone https://github.com/HerOfMYLife/kegorak-id-vault.git
cd kegorak-id-vault

# Install dependencies
pip install customtkinter cryptography

# Run the application
python Dash.py
