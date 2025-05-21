
🔥 Charon - A Lightweight, Extensible Linux Firewall

Charon is a custom-built, iptables-driven Linux firewall designed to be simple, readable, and extensible for home or small business use. Built with Bash, it emphasizes clarity over complexity — making it easy to audit, modify, and extend without diving into arcane configurations or bloated UIs.

    Like its mythological namesake, Charon stands at the gate — letting only the trusted pass.

📌 Overview

Charon is a minimalist yet powerful firewall framework built entirely in Bash. It's ideal for headless Debian-based routers, Raspberry Pi setups, or virtualized gateway machines. It aims to give sysadmins and enthusiasts total control over their network boundaries without depending on third-party interfaces or undocumented behavior.
⚙️ Features

    🔐 Stateful packet inspection using iptables

    🚫 Explicit default-deny policy

    📋 Organized rules by interface and purpose (LAN, WAN, DMZ)

    🌐 NAT and port forwarding support

    🧩 Easy to extend and customize

    🖥️ Designed for Debian-based systems (e.g., Ubuntu, Raspbian)

🛠️ Tech Stack

    Bash scripting

    iptables (legacy, not nftables)

    Linux (Debian/Ubuntu compatible)

🚀 Installation

# Clone the repo
git clone https://github.com/dwhitlockii/Charon.git
cd Charon

# Run setup (you may need sudo privileges)
sudo ./install.sh

    ⚠️ This modifies iptables rules directly — only use on non-production systems unless you know what you're doing!

🔧 Configuration

Charon organizes its rules into logical components. You can modify rules/ to customize:

    Interfaces (eth0, wlan0, etc.)

    Allowed ports/services

    NAT and forwarding behaviors

Each file is sourced in order, making it easy to insert or override rule sets.
🧪 Testing

# Simulate the firewall rules without applying
./charon.sh --dry-run

# Apply the rules
sudo ./charon.sh --apply

Use iptables -L -v or iptables-save to verify the ruleset after applying.
📎 Roadmap / To-Do

IPv6 support

nftables version

Web UI (optional lightweight dashboard)

    Logging enhancements

🤝 Contributing

Contributions are welcome! Fork, improve, and send a pull request — especially for more advanced rulesets, performance tweaks, or broader system support.
🪦 License

MIT — use it, tweak it, fork it, break it. Just don't blame me if your network melts.
