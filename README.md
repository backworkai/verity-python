# Verity Python SDK

Official Python client for the [Verity API](https://verity.backworkai.com): Medicare coverage policies, medical code intelligence, prior authorization checks, claim validation, compliance review, and drug formulary evidence.

## Installation

Install from GitHub until the first PyPI release is indexed:

```bash
pip install git+https://github.com/backworkai/verity-python.git
```

After the first PyPI release, install it directly:

```bash
pip install verity-api
```

Requires Python 3.8 or newer.

## Quick Start

```python
from verity import VerityClient

client = VerityClient("vrt_live_YOUR_API_KEY")

code = client.lookup_code("76942", include=["rvu", "policies"])
print(code["data"]["description"])

prior_auth = client.check_prior_auth(
    procedure_codes=["76942"],
    diagnosis_codes=["M54.5"],
    state="TX",
    payer="medicare",
)
print(prior_auth["data"]["pa_required"])
```

Get an API key from the [Verity dashboard](https://verity.backworkai.com/dashboard).

## Core Workflows

### Code Lookup

```python
result = client.lookup_code(
    "76942",
    code_system="CPT",
    jurisdiction="JM",
    include=["rvu", "policies", "rates"],
    fuzzy=True,
)
```

### Policy Search and Retrieval

```python
policies = client.list_policies(
    q="ultrasound guidance",
    mode="keyword",
    policy_type="LCD",
    status="active",
    limit=25,
)

policy = client.get_policy("L33831", include=["criteria", "codes"])
```

### Prior Authorization and Claim Validation

```python
pa = client.check_prior_auth(
    procedure_codes=["76942"],
    diagnosis_codes=["M54.5"],
    state="TX",
    payer="medicare",
)

claim = client.validate_claim(
    procedure_codes=["99213"],
    diagnosis_codes=["E11.9"],
    payer="Medicare",
    state="TX",
    date_of_service="2026-05-23",
)

print(claim["data"]["coverage_status"], claim["data"]["denial_risk"])
print(claim["data"]["issues"], claim["data"]["matched_policies"])
```

### Coverage, Spending, and Compliance

```python
criteria = client.search_criteria(q="diabetes", section="indications", limit=10)
print(criteria["data"][0]["policy_id"], criteria["data"][0]["policy_title"])
spending = client.get_spending_by_code(codes=["T1019", "T1020"], year=2023)
changes = client.list_unreviewed_changes(limit=10)
stats = client.get_compliance_stats()
```

### Drug Formulary Evidence

```python
formulary = client.search_drug_formulary_evidence(
    "ozempic",
    payer="all",
    limit=5,
)
```

## Error Handling

```python
from verity import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ValidationError,
    VerityError,
)

try:
    result = client.lookup_code("76942")
except AuthenticationError:
    print("Invalid API key")
except ValidationError as error:
    print(f"Invalid request: {error.message}")
except NotFoundError:
    print("Resource not found")
except RateLimitError as error:
    print(f"Rate limit exceeded. Reset: {error.reset}")
except VerityError as error:
    print(f"Verity API error: {error.message}")
```

## Configuration

```python
client = VerityClient(
    api_key="vrt_live_YOUR_API_KEY",
    base_url="https://verity.backworkai.com/api/v1",
    timeout=30.0,
)
```

The client can also be used as a context manager:

```python
with VerityClient("vrt_live_YOUR_API_KEY") as client:
    result = client.lookup_code("76942")
```

## Development

```bash
python -m pip install -e ".[dev]"
PYTHONPATH=src python -m pytest
```

## Release

The package publishes to PyPI as `verity-api` and imports as `verity`.

1. Configure PyPI Trusted Publishing for `backworkai/verity-python`, workflow `publish.yml`, environment `pypi`, project `verity-api`.
2. Update `setup.py` and `src/verity/__init__.py` to the new version.
3. Push a matching tag, for example `v1.0.0`.
4. The publish workflow builds, checks, and uploads the distributions to PyPI via OIDC.

## Support

- Documentation: https://verity.backworkai.com/docs
- Issues: https://github.com/backworkai/verity-python/issues
- Email: support@verity.backworkai.com

## License

MIT
