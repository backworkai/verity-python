"""Verity API Client."""

from typing import Any, Dict, List, Optional, Union
import httpx

from .exceptions import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ValidationError,
    VerityError,
)


class VerityClient:
    """Client for interacting with the Verity API.
    
    Args:
        api_key: Your Verity API key (vrt_live_* or vrt_test_*)
        base_url: Base URL for the API (default: production)
        timeout: Request timeout in seconds
    
    Example:
        >>> client = VerityClient("vrt_live_abc123")
        >>> result = client.lookup_code("76942")
        >>> print(result["data"]["description"])
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://verity.backworkai.com/api/v1",
        timeout: float = 30.0,
    ):
        if not api_key:
            raise ValueError("API key is required")
        
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        
        self._client = httpx.Client(
            headers={
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "verity-python/1.0.0",
            },
            timeout=timeout,
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Close the HTTP client."""
        self._client.close()

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make an HTTP request to the API."""
        url = f"{self.base_url}{path}"
        
        try:
            response = self._client.request(
                method=method,
                url=url,
                params=params,
                json=json,
                headers=headers,
            )
            
            if response.status_code == 200:
                return response.json()
            
            # Handle error responses
            try:
                error_data = response.json()
                error_info = error_data.get("error", {})
                message = error_info.get("message", "Unknown error")
                code = error_info.get("code")
                hint = error_info.get("hint")
                details = error_info.get("details")
            except Exception:
                message = response.text or f"HTTP {response.status_code}"
                code = None
                hint = None
                details = None
            
            if response.status_code == 401:
                raise AuthenticationError(message, code=code, hint=hint, details=details)
            elif response.status_code == 404:
                raise NotFoundError(message, code=code, hint=hint, details=details)
            elif response.status_code == 429:
                raise RateLimitError(
                    message,
                    code=code,
                    hint=hint,
                    details=details,
                    limit=response.headers.get("X-RateLimit-Limit"),
                    remaining=response.headers.get("X-RateLimit-Remaining"),
                    reset=response.headers.get("X-RateLimit-Reset"),
                )
            elif response.status_code == 400:
                raise ValidationError(message, code=code, hint=hint, details=details)
            else:
                raise VerityError(message, code=code, hint=hint, details=details)
                
        except httpx.HTTPError as e:
            raise VerityError(f"HTTP error: {str(e)}")

    # Health Check
    def health(self) -> Dict[str, Any]:
        """Check API health status.
        
        Returns:
            Health status including database and Redis checks.
        """
        return self._request("GET", "/health")

    # Code Lookup
    def lookup_code(
        self,
        code: str,
        code_system: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        include: Optional[List[str]] = None,
        fuzzy: bool = True,
    ) -> Dict[str, Any]:
        """Look up a medical code and get coverage information.
        
        Args:
            code: The medical code to look up (CPT, HCPCS, ICD-10, NDC)
            code_system: Hint for code system (CPT, HCPCS, ICD10CM, ICD10PCS, NDC)
            jurisdiction: Filter policies by MAC jurisdiction code
            include: Additional data to include (rvu, policies)
            fuzzy: Enable fuzzy matching on miss
        
        Returns:
            Code information including description, policies, and optionally RVU data.
        
        Example:
            >>> result = client.lookup_code("76942", include=["rvu", "policies"])
            >>> print(result["data"]["description"])
        """
        params = {"code": code, "fuzzy": str(fuzzy).lower()}
        
        if code_system:
            params["code_system"] = code_system
        if jurisdiction:
            params["jurisdiction"] = jurisdiction
        if include:
            params["include"] = ",".join(include)
        
        return self._request("GET", "/codes/lookup", params=params)

    # Policy Search
    def list_policies(
        self,
        q: Optional[str] = None,
        mode: str = "keyword",
        policy_type: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        payer: Optional[str] = None,
        status: str = "active",
        cursor: Optional[str] = None,
        limit: int = 50,
        include: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Search and list policies.
        
        Args:
            q: Search query (max 500 characters)
            mode: Search mode (keyword or semantic)
            policy_type: Filter by policy type (LCD, Article, NCD, etc.)
            jurisdiction: Filter by MAC jurisdiction code
            payer: Filter by payer name
            status: Filter by status (active, retired, all)
            cursor: Pagination cursor
            limit: Results per page (1-100)
            include: Additional data (summary, criteria, codes)
        
        Returns:
            List of policies with pagination metadata.
        """
        params = {"mode": mode, "status": status, "limit": limit}
        
        if q:
            params["q"] = q
        if policy_type:
            params["policy_type"] = policy_type
        if jurisdiction:
            params["jurisdiction"] = jurisdiction
        if payer:
            params["payer"] = payer
        if cursor:
            params["cursor"] = cursor
        if include:
            params["include"] = ",".join(include)
        
        return self._request("GET", "/policies", params=params)

    # Get Policy by ID
    def get_policy(
        self,
        policy_id: str,
        include: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get a single policy by ID.
        
        Args:
            policy_id: Policy ID (e.g., L33831)
            include: Additional data (criteria, codes, attachments, versions)
        
        Returns:
            Policy details with optional related data.
        
        Example:
            >>> policy = client.get_policy("L33831", include=["criteria", "codes"])
        """
        params = {}
        if include:
            params["include"] = ",".join(include)
        
        return self._request("GET", f"/policies/{policy_id}", params=params)

    # Compare Policies
    def compare_policies(
        self,
        procedure_codes: List[str],
        policy_type: Optional[str] = None,
        jurisdictions: Optional[List[str]] = None,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Compare policies across jurisdictions.
        
        Args:
            procedure_codes: Array of CPT/HCPCS codes to compare (max 10)
            policy_type: Filter by policy type (LCD, Article, NCD)
            jurisdictions: Specific jurisdictions to compare (all if omitted, max 10)
            idempotency_key: Unique request identifier for safe retries
        
        Returns:
            Comparison across jurisdictions with national policies.
        """
        headers = {}
        if idempotency_key:
            headers["X-Idempotency-Key"] = idempotency_key
        
        body = {"procedure_codes": procedure_codes}
        if policy_type:
            body["policy_type"] = policy_type
        if jurisdictions:
            body["jurisdictions"] = jurisdictions
        
        return self._request("POST", "/policies/compare", json=body, headers=headers)

    # Policy Changes
    def get_policy_changes(
        self,
        since: Optional[str] = None,
        policy_id: Optional[str] = None,
        change_type: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Get policy change feed.
        
        Args:
            since: ISO8601 timestamp - only show changes after this date
            policy_id: Filter to a specific policy
            change_type: Filter by change type (created, updated, retired, etc.)
            cursor: Pagination cursor
            limit: Results per page (1-100)
        
        Returns:
            List of policy changes with pagination.
        """
        params = {"limit": limit}
        
        if since:
            params["since"] = since
        if policy_id:
            params["policy_id"] = policy_id
        if change_type:
            params["change_type"] = change_type
        if cursor:
            params["cursor"] = cursor
        
        return self._request("GET", "/policies/changes", params=params)

    # Coverage Criteria Search
    def search_criteria(
        self,
        q: str,
        section: Optional[str] = None,
        policy_type: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """Search coverage criteria.
        
        Args:
            q: Search query for criteria text (max 500 characters)
            section: Filter by section (indications, limitations, documentation, etc.)
            policy_type: Filter by policy type (LCD, Article, NCD, PayerPolicy)
            jurisdiction: Filter by MAC jurisdiction
            cursor: Pagination cursor
            limit: Results per page (1-100)
        
        Returns:
            Matching criteria blocks with policy context.
        """
        params = {"q": q, "limit": limit}
        
        if section:
            params["section"] = section
        if policy_type:
            params["policy_type"] = policy_type
        if jurisdiction:
            params["jurisdiction"] = jurisdiction
        if cursor:
            params["cursor"] = cursor
        
        return self._request("GET", "/coverage/criteria", params=params)

    # Jurisdictions
    def list_jurisdictions(self) -> Dict[str, Any]:
        """List MAC jurisdictions.
        
        Returns:
            List of Medicare Administrative Contractor jurisdictions.
        """
        return self._request("GET", "/jurisdictions")

    # Prior Authorization Check
    def check_prior_auth(
        self,
        procedure_codes: List[str],
        diagnosis_codes: Optional[List[str]] = None,
        state: Optional[str] = None,
        payer: str = "medicare",
        criteria_page: int = 1,
        criteria_per_page: int = 25,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Check prior authorization requirements.
        
        Args:
            procedure_codes: CPT/HCPCS codes to check (max 10)
            diagnosis_codes: ICD-10 diagnosis codes for context (max 10)
            state: Two-letter state code (determines MAC jurisdiction)
            payer: Payer to check (medicare, aetna, uhc, all)
            criteria_page: Page number for criteria results
            criteria_per_page: Criteria items per page (1-100)
            idempotency_key: Unique request identifier for safe retries
        
        Returns:
            Prior auth determination with matched policies and criteria.
        
        Example:
            >>> result = client.check_prior_auth(
            ...     procedure_codes=["76942"],
            ...     diagnosis_codes=["M54.5"],
            ...     state="TX"
            ... )
            >>> print(result["data"]["pa_required"])
        """
        headers = {}
        if idempotency_key:
            headers["X-Idempotency-Key"] = idempotency_key
        
        body = {
            "procedure_codes": procedure_codes,
            "payer": payer,
            "criteria_page": criteria_page,
            "criteria_per_page": criteria_per_page,
        }
        
        if diagnosis_codes:
            body["diagnosis_codes"] = diagnosis_codes
        if state:
            body["state"] = state
        
        return self._request("POST", "/prior-auth/check", json=body, headers=headers)
