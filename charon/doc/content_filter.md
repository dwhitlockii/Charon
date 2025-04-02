# Content Filter Documentation

## Overview

The Content Filter module in Charon provides functionality to block unwanted websites and content. It uses a database to store blocked domains organized by categories and applies the filtering rules to the firewall.

## Key Features

- Domain-based content filtering
- Category-based organization
- Wildcard matching for domains
- Cross-platform compatibility (Linux and Windows)
- Integration with platform-specific firewall technologies
- Enable/disable filtering by category

## Basic Concepts

### Categories

Content is organized into categories such as:

- Adult content
- Gambling
- Social media
- Advertisements
- Malware/Phishing

Each category can be independently enabled or disabled.

### Domain Filtering

The filter works by maintaining a database of domains to block. When applied to the firewall, it creates rules to block access to these domains. The module supports:

- Full domain blocking (e.g., example.com)
- Wildcard domain blocking (e.g., *.example.com)

## Usage

### Basic Setup

```python
from charon.src.core.content_filter import ContentFilter

# Initialize the content filter
content_filter = ContentFilter()

# Add domains to block
content_filter.add_domain("example.com", "adult")
content_filter.add_domain("ads.example.com", "ads")

# Apply the filters to the firewall
content_filter.apply_to_firewall()
```

### Managing Categories

```python
# Add a new category
content_filter.add_category("gaming", "Gaming websites", enabled=False)

# Enable or disable a category
content_filter.enable_category("social", enabled=True)

# Get a list of all categories
categories = content_filter.get_categories()
for category in categories:
    print(f"{category['name']}: {category['description']} (Enabled: {category['enabled']})")
```

### Managing Domains

```python
# Add a domain to block
content_filter.add_domain("example.com", "adult")

# Remove a domain from the block list
content_filter.remove_domain("example.com")

# Check if a domain is blocked
if content_filter.is_domain_blocked("example.com"):
    print("Domain is blocked")
else:
    print("Domain is not blocked")

# Get all domains in a category
adult_domains = content_filter.get_domains_by_category("adult")
for domain in adult_domains:
    print(domain)
```

## Cross-Platform Compatibility

The content filter is designed to work across different operating systems:

### Linux

On Linux systems, the content filter:
- Uses `/etc/charon/content_filter.db` as the default database location
- Integrates with nftables for firewall rule application
- Checks for root privileges to ensure proper operation

### Windows

On Windows systems, the content filter:
- Uses `%LOCALAPPDATA%\Charon\content_filter.db` as the default database location
- Integrates with Windows Defender Firewall using `netsh advfirewall` commands
- Creates a combination of firewall rules and hosts-file entries for comprehensive blocking
- Properly handles permission checks without requiring the Linux-specific `geteuid()`

### Database Location

The database location can be customized during initialization for both platforms:

```python
# Custom database location
content_filter = ContentFilter(db_path='/path/to/custom/database.db')
```

If no path is provided, a platform-appropriate default path will be used automatically.

## Integration with Firewall

The content filter integrates with different firewall technologies depending on the platform:

### Linux Integration (nftables)

On Linux systems, when you call `apply_to_firewall()`, it:

1. Retrieves all domains from enabled categories
2. Creates a temporary file with the list of domains
3. Creates or updates an nftables set containing these domains
4. Adds a firewall rule to block DNS requests for those domains

### Windows Integration (Windows Defender Firewall)

On Windows systems, when you call `apply_to_firewall()`, it:

1. Retrieves all domains from enabled categories
2. Creates a rule group named "Charon-ContentFilter" in Windows Firewall
3. Adds blocking rules for outgoing connections to the blocked domains on common web ports (80, 443, 8080)
4. Creates a hosts-file format text file that can be used to supplement the blocking

Note: For comprehensive blocking on Windows, additional host file configuration may be necessary. The module will generate this file and provide instructions in the log.

## Database Structure

The content filter stores its data in an SQLite database with the following structure:

- **domains** table: Stores the domains to block
  - id: Primary key
  - domain: The domain to block
  - category: The category of the domain
  - added_date: When the domain was added

- **categories** table: Stores the categories
  - id: Primary key
  - name: The name of the category
  - description: A description of the category
  - enabled: Whether the category is enabled

## Customization

You can easily extend the content filter by:

1. Adding new categories for specific types of content
2. Importing block lists from external sources
3. Modifying the filtering behavior to suit your needs
4. Adding support for additional platforms by extending the firewall integration

## Example: Setting Up Parental Controls

```python
from charon.src.core.content_filter import ContentFilter

# Initialize the content filter
content_filter = ContentFilter()

# Enable relevant categories
content_filter.enable_category("adult", enabled=True)
content_filter.enable_category("gambling", enabled=True)

# Add custom domains to block
content_filter.add_domain("mygamingsite.com", "gaming")
content_filter.add_domain("socialmedia.com", "social")

# Apply the filter to the firewall
content_filter.apply_to_firewall()
```

## Platform-Specific Considerations

### Linux
- Requires root privileges for firewall configuration
- Uses temporary files in standard locations
- Fully integrated with nftables

### Windows
- Requires administrator privileges for firewall configuration
- Limited to 25 domains in Windows Firewall for performance (additional domains require hosts file)
- Some operations may trigger User Account Control (UAC) prompts
- Web browser restart may be required for changes to take effect 