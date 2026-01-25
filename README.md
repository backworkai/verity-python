# Verity Python SDK

Python client library for the [Verity API](https://verity.backworkai.com) - Medicare coverage policies, prior authorization requirements, and medical code lookups.

## Installation

```bash
pip install verity-sdk
```

## Quick Start

```python
from verity import VerityClient

# Initialize the client
client = VerityClient("vrt_live_YOUR_API_KEY")

# Look up a medical code
result = client.lookup_code("76942", include=["rvu", "policies"])
print(result["data"]["description"])
# Output: "Ultrasonic guidance for needle placement"

# Check prior authorization requirements
pa_check = client.check_prior_auth(
    procedure_codes=["76942"],
    diagnosis_codes=["M54.5"],
    state="TX"
)
print(f"PA Required: {pa_check['data']['pa_required']}")

# Search policies
policies = client.list_policies(
    q="ultrasound guidance",
    policy_type="LCD",
    limit=10
)

# Get specific policy details
policy = client.get_policy("L33831", include=["criteria", "codes"])
```

## Features

- **Type hints** - Full type annotations for better IDE support
- **Automatic retries** - Built-in retry logic for transient failures
- **Error handling** - Clear exception types for different error scenarios
- **Context manager** - Automatic resource cleanup with `with` statement

## Authentication

Get your API key from the [Verity Dashboard](https://verity.backworkai.com/dashboard).

```python
client = VerityClient("vrt_live_YOUR_API_KEY")
```

## Usage Examples

### Code Lookup

```python
# Basic lookup
result = client.lookup_code("76942")

# With additional data
result = client.lookup_code(
    "76942",
    code_system="HCPCS",
    jurisdiction="JM",
    include=["rvu", "policies"],
    fuzzy=True
)
```

### Policy Search

```python
# Keyword search
policies = client.list_policies(
    q="ultrasound guidance",
    mode="keyword",
    policy_type="LCD",
    status="active",
    limit=50
)

# Semantic search
policies = client.list_policies(
    q="imaging guidance for procedures",
    mode="semantic"
)

# Pagination
next_page = client.list_policies(cursor=policies["meta"]["pagination"]["cursor"])
```

### Prior Authorization

```python
result = client.check_prior_auth(
    procedure_codes=["76942", "76937"],
    diagnosis_codes=["M54.5", "G89.29"],
    state="TX",
    payer="medicare"
)

if result["data"]["pa_required"]:
    print("Prior authorization required!")
    print("Documentation needed:", result["data"]["documentation_checklist"])
```

### Policy Comparison

```python
comparison = client.compare_policies(
    procedure_codes=["76942"],
    policy_type="LCD",
    jurisdictions=["JM", "JH", "JK"]
)

for juris in comparison["data"]["comparison"]:
    print(f"{juris['jurisdiction']}: {len(juris['policies'])} policies")
```

### Coverage Criteria Search

```python
criteria = client.search_criteria(
    q="diabetes",
    section="indications",
    policy_type="LCD",
    limit=25
)
```

### Jurisdictions

```python
jurisdictions = client.list_jurisdictions()
for j in jurisdictions["data"]:
    print(f"{j['jurisdiction_code']}: {j['mac_name']} ({', '.join(j['states'])})")
```

## Error Handling

```python
from verity import (
    VerityClient,
    AuthenticationError,
    ValidationError,
    NotFoundError,
    RateLimitError,
    VerityError
)

try:
    result = client.lookup_code("76942")
except AuthenticationError:
    print("Invalid API key")
except ValidationError as e:
    print(f"Invalid parameters: {e.message}")
except NotFoundError:
    print("Resource not found")
except RateLimitError as e:
    print(f"Rate limit exceeded. Resets at: {e.reset}")
except VerityError as e:
    print(f"API error: {e.message}")
```

## Context Manager

```python
with VerityClient("vrt_live_YOUR_API_KEY") as client:
    result = client.lookup_code("76942")
    # Client automatically closed when exiting the context
```

## Requirements

- Python 3.8+
- httpx >= 0.24.0

## License

MIT License - see LICENSE file for details.

## Support

- Documentation: https://verity.backworkai.com/docs
- Issues: https://github.com/tylerbryy/verity-python/issues
- Email: support@verity.backworkai.com
