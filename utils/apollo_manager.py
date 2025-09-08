"""
COOGI Apollo.io Manager (compact + production-ready)
- Consistent endpoint usage (/v1/mixed_people/search)
- Reveal work/personal emails + phone numbers on search
- Fallback /v1/people/match reveal if search returns placeholders
- Optional Hunter verification (skip invalid)
- Pagination + per-city limits
- DVM multi-location helper + generic multi-location role search
"""

import csv
import json
import os
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

APOLLO_BASE = "https://api.apollo.io/v1"
APOLLO_KEY = os.getenv("APOLLO_API_KEY", "")
HUNTER_KEY = os.getenv("HUNTER_API_KEY", "")


class ApolloManager:
    def __init__(self, rps: float = 2.0, timeout: int = 30):
        if not APOLLO_KEY:
            logger.warning("⚠️ Apollo API key missing")
        else:
            logger.info("✅ Apollo Manager ready")
        self._last_ts = 0.0
        self._min_gap = max(0.0, 1.0 / rps)  # seconds between calls
        self._timeout = timeout

    # ----------------------- low-level I/O -----------------------

    def _rate_limit(self):
        now = time.time()
        gap = now - self._last_ts
        if gap < self._min_gap:
            time.sleep(self._min_gap - gap)
        self._last_ts = time.time()

    def _request(
        self, method: str, path: str, *, json: Optional[dict] = None, params: Optional[dict] = None
    ) -> Dict[str, Any]:
        self._rate_limit()
        url = f"{APOLLO_BASE}{path}"
        headers = {
            "X-Api-Key": APOLLO_KEY,
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
        }
        try:
            if method == "GET":
                resp = requests.get(url, headers=headers, params=params, timeout=self._timeout)
            else:
                resp = requests.request(method, url, headers=headers, json=json, timeout=self._timeout)
        except Exception as e:
            logger.error(f"Network error: {e}")
            return {"error": str(e)}
        if resp.status_code in (200, 201):
            return resp.json()
        logger.error(f"Apollo API {path} -> {resp.status_code}: {resp.text[:500]}")
        return {"error": f"HTTP {resp.status_code}", "message": resp.text}

    # ----------------------- utilities -----------------------

    @staticmethod
    def _is_placeholder_email(value: Optional[str]) -> bool:
        if not value or "@" not in str(value):
            return True
        s = str(value).lower()
        return "not_unlocked" in s or s.endswith("@domain.com")

    @staticmethod
    def _normalize_location(raw_city: Optional[str], raw_state: Optional[str]) -> str:
        parts = [p for p in [raw_city, raw_state] if p]
        return ", ".join(parts)

    @staticmethod
    def _size_token(label: Optional[str]) -> Optional[str]:
        if not label:
            return None
        m = {
            "startup": "1-10",
            "small": "11-50",
            "medium": "51-200",
            "large": "201-1000",
            "enterprise": "1001+",
        }
        return m.get(label.lower())

    @staticmethod
    def _optimized_titles(job_title: str) -> List[str]:
        t = job_title.lower().strip()
        m = {
            # veterinary
            "vet doctor": ["Veterinarian", "Vet Doctor", "Veterinary Doctor", "Doctor of Veterinary Medicine", "DVM"],
            "veterinarian": ["Veterinarian", "Vet Doctor", "Veterinary Doctor", "DVM"],
            "vet": ["Veterinarian", "Vet Doctor", "Animal Care", "Animal Health"],
            # tech (examples)
            "software engineer": ["Software Engineer", "Software Developer", "Developer", "Engineer"],
            "developer": ["Developer", "Software Engineer", "Software Developer", "Programmer"],
            "fullstack": ["Full Stack Developer", "Full-stack Developer", "Fullstack"],
            "frontend": ["Frontend Developer", "Front-end Developer", "UI Developer"],
            "backend": ["Backend Developer", "Back-end Developer", "Server Developer"],
            "devops": ["DevOps Engineer", "Site Reliability Engineer", "SRE"],
            # business (examples)
            "sales": ["Sales", "Account Executive", "Business Development"],
            "marketing": ["Marketing Manager", "Digital Marketing", "Brand Manager"],
        }
        for k, v in m.items():
            if k in t:
                return v
        return [job_title]

    @staticmethod
    def _vet_industry_tags() -> List[str]:
        # These are example IDs you used before; keep or remove depending on workspace.
        return [
            "5567cd4e69702d4b13af2b7d",  # Veterinary Services
            "5567cd5169702d4b1dbf0d5c",  # Animal Care Services
        ]

    @staticmethod
    def _dedupe_key(person: Dict[str, Any]) -> Tuple:
        # Strong dedupe by Apollo ID, then LinkedIn/email fallback
        return (
            person.get("apollo_id") or "",
            person.get("linkedin_url") or "",
            tuple(person.get("emails") or []),
        )

    @staticmethod
    def _hunter_verify(email: str) -> Optional[str]:
        """Return 'valid' | 'invalid' | 'risky' | None (no key / error)."""
        if not HUNTER_KEY or not email:
            return None
        try:
            r = requests.get(
                "https://api.hunter.io/v2/email-verifier",
                params={"email": email, "api_key": HUNTER_KEY},
                timeout=12,
            )
            if r.status_code == 200:
                return r.json().get("data", {}).get("result")
        except Exception:
            return None
        return None

    # ----------------------- public methods -----------------------

    def test_api_connection(self) -> Dict[str, Any]:
        res = self._request("POST", "/mixed_people/search", json={"q_keywords": "test", "page": 1, "per_page": 1})
        ok = "error" not in res
        return {
            "status": "operational" if ok else "error",
            "api_key_valid": ok,
            "timestamp": datetime.now().isoformat(),
            "note": "Reachability only; not a credits check.",
        }

    def get_person_details(self, apollo_id: str) -> Dict[str, Any]:
        res = self._request("GET", f"/people/{apollo_id}")
        if "error" in res:
            return {"success": False, "error": res.get("error")}
        return {"success": True, "person": res.get("person", {}), "timestamp": datetime.now().isoformat()}

    # ---- core search (single city) ----

    def search_candidates(
        self,
        job_title: str,
        *,
        location: Optional[str] = None,      # "City, ST" or "State"
        domain: Optional[str] = None,        # example.com
        company_size: Optional[str] = None,  # startup/small/medium/large/enterprise
        limit: int = 25,
        require_email: bool = False,
        require_phone: bool = False,
        reveal_emails: bool = True,
        reveal_phones: bool = True,
        hunter_verify: bool = True,
        use_vet_industry_tags: bool = False,
        page_start: int = 1,
        unlock_emails: bool = True,
    ) -> Dict[str, Any]:
        """One-city search with reveal + fallback /people/match; returns LinkedIn, phones, emails."""
        titles = self._optimized_titles(job_title)

        payload: Dict[str, Any] = {
            "page": page_start,
            "per_page": min(max(limit, 1), 25),
            "person_titles": titles,
            "reveal_work_emails": bool(reveal_emails),
            "reveal_personal_emails": bool(reveal_emails),
            "reveal_phone": bool(reveal_phones),
        }
        if location:
            if "," in location:
                city, state = [p.strip() for p in location.split(",", 1)]
                payload["person_locations"] = [f"{city}, {state}", city, state]
            else:
                payload["person_locations"] = [location]
        if domain:
            payload["organization_domains"] = [domain]
        if company_size:
            token = self._size_token(company_size)
            if token:
                payload["organization_num_employees_ranges"] = [token]
        if use_vet_industry_tags:
            payload["organization_industry_tag_ids"] = self._vet_industry_tags()

        res = self._request("POST", "/mixed_people/search", json=payload)
        if "error" in res:
            return {"success": False, "error": res.get("error"), "message": res.get("message")}

        normalized = []
        for p in (res.get("people") or [])[:limit]:
            # Don't require email during normalization - we'll unlock emails later
            person = self._normalize_person_from_search(p, require_email=False, reveal_fallback=True)
            if not person:
                continue
            normalized.append(person)

        # Note: Email unlocking will be done at a higher level (in search_dvm_in_locations)
        # to avoid asyncio conflicts in sync methods

        # Apply filtering (but not email filtering yet - that happens after unlocking)
        filtered_candidates = []
        for person in normalized:
            # Apply Hunter.io verification if enabled
            if hunter_verify and person.get("emails"):
                person["emails"] = self._hunter_filter(person["emails"])
            
            # Skip email requirement for now - will be applied after unlocking
            # Apply phone requirement filter
            if require_phone and not (person.get("phones") or []):
                continue
                
            filtered_candidates.append(person)

        return {
            "success": True,
            "total_found": len(filtered_candidates),
            "candidates": filtered_candidates,
            "timestamp": datetime.now().isoformat(),
            "search_params": {
                "job_title": job_title,
                "location": location,
                "domain": domain,
                "company_size": company_size,
                "require_email": require_email,
                "require_phone": require_phone,
                "reveal_emails": reveal_emails,
                "reveal_phones": reveal_phones,
                "hunter_verify": hunter_verify,
                "page_start": page_start,
                "unlock_emails": unlock_emails,
            },
        }

    # ---- pagination helper (keeps calling pages until per_city_limit) ----

    def paged_city_search(
        self,
        job_title: str,
        location: str,
        *,
        per_city_limit: int = 25,
        require_email: bool = True,
        require_phone: bool = False,
        hunter_verify: bool = True,
        use_vet_industry_tags: bool = False,
        company_size: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        collected: List[Dict[str, Any]] = []
        seen = set()
        page = 0
        while len(collected) < per_city_limit:
            page += 1
            res = self.search_candidates(
                job_title,
                location=location,
                limit=min(25, per_city_limit - len(collected)),
                require_email=require_email,
                require_phone=False,  # filter after normalization to allow fallback reveal
                hunter_verify=hunter_verify,
                use_vet_industry_tags=use_vet_industry_tags,
                company_size=company_size,
                page_start=page,
            )
            if not res.get("success"):
                break
            batch = res.get("candidates") or []
            if not batch:
                break

            for person in batch:
                key = self._dedupe_key(person)
                if key in seen:
                    continue
                seen.add(key)
                if require_phone and not (person.get("phones") or []):
                    continue
                person["search_location"] = location
                collected.append(person)

            # stop early if the API returned fewer than requested (likely last page)
            if len(batch) < min(25, per_city_limit - (len(collected))):
                break

        return collected

    # ---- multi-location helpers ----

    async def search_dvm_in_locations(
        self,
        locations: List[str],
        *,
        per_city_limit: int = 15,
        require_email: bool = True,
        require_phone: bool = False,
        hunter_verify: bool = True,
        unlock_emails: bool = True,
    ) -> Dict[str, Any]:
        """Client real use case: DVM across multiple cities (emails+phones+LinkedIn)."""
        all_rows: List[Dict[str, Any]] = []
        for loc in locations:
            rows = self.paged_city_search(
                job_title="Veterinarian",
                location=loc,
                per_city_limit=per_city_limit,
                require_email=False,  # Don't filter by email yet - do it after unlocking
                require_phone=require_phone,
                hunter_verify=hunter_verify,
                use_vet_industry_tags=False,  # Don't use restrictive vet tags
            )
            all_rows.extend(rows)

        # Unlock emails for candidates that need it
        if unlock_emails and all_rows:
            all_rows = await self.unlock_emails_for_candidates(all_rows)

        # Now apply email filtering after unlocking
        if require_email:
            filtered_rows = []
            for candidate in all_rows:
                if candidate.get("emails"):
                    filtered_rows.append(candidate)
            all_rows = filtered_rows

        return {
            "success": True,
            "total_found": len(all_rows),
            "candidates": all_rows,
            "timestamp": datetime.now().isoformat(),
            "search_params": {
                "specialization": "DVM",
                "locations": locations,
                "per_city_limit": per_city_limit,
                "require_email": require_email,
                "require_phone": require_phone,
                "hunter_verify": hunter_verify,
                "unlock_emails": unlock_emails,
            },
        }

    def search_role_in_locations(
        self,
        job_title: str,
        locations: List[str],
        *,
        per_city_limit: int = 15,
        require_email: bool = True,
        require_phone: bool = False,
        hunter_verify: bool = True,
        company_size: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generic multi-city role search (non-DVM)."""
        all_rows: List[Dict[str, Any]] = []
        seen = set()
        for loc in locations:
            rows = self.paged_city_search(
                job_title,
                location=loc,
                per_city_limit=per_city_limit,
                require_email=require_email,
                require_phone=require_phone,
                hunter_verify=hunter_verify,
                use_vet_industry_tags=False,
                company_size=company_size,
            )
            for r in rows:
                k = self._dedupe_key(r)
                if k in seen:
                    continue
                seen.add(k)
                r["search_location"] = loc
                all_rows.append(r)
        return {
            "success": True,
            "total_found": len(all_rows),
            "candidates": all_rows,
            "timestamp": datetime.now().isoformat(),
            "search_params": {
                "job_title": job_title,
                "locations": locations,
                "per_city_limit": per_city_limit,
                "require_email": require_email,
                "require_phone": require_phone,
                "hunter_verify": hunter_verify,
                "company_size": company_size,
            },
        }

    # ----------------------- normalization + helpers -----------------------

    def _normalize_person_from_search(self, p: Dict[str, Any], require_email: bool, reveal_fallback: bool) -> Optional[Dict[str, Any]]:
        """Turn a raw Apollo person into our unified shape, optionally performing /people/match fallback."""
        org = p.get("organization") or {}
        if not isinstance(org, dict):
            org = {}

        # collect emails (prefer non-placeholders)
        emails: List[str] = []
        primary_email = p.get("email")
        if primary_email and not self._is_placeholder_email(primary_email):
            emails.append(primary_email)

        for e in (p.get("emails") or []):
            addr = e.get("email") or e.get("address")
            if addr and not self._is_placeholder_email(addr):
                emails.append(addr)

        # include any personal emails exposed on search
        for pe in (p.get("personal_emails") or []):
            if pe and not self._is_placeholder_email(pe):
                emails.append(pe)

        # collect phones (direct)
        phones: List[str] = []
        for ph in (p.get("phone_numbers") or []):
            number = ph.get("sanitized_number") or ph.get("raw_number") or ph.get("number")
            if number and len(number) >= 8:
                phones.append(number)

        # include org main line if present (dict or string)
        org_primary = org.get("primary_phone")
        org_num = None
        if isinstance(org_primary, dict):
            org_num = org_primary.get("sanitized_number") or org_primary.get("number")
        elif isinstance(org_primary, str):
            org_num = org_primary
        if org_num and len(org_num) >= 8:
            phones.append(org_num)

        # fallback reveal via /people/match if we still don't have a real email
        if reveal_fallback and require_email and not emails:
            match_payload = {
                "first_name": p.get("first_name", ""),
                "last_name": p.get("last_name", ""),
                "reveal_email": True,
                "reveal_phone": True,
            }
            if org.get("name"):
                match_payload["organization_name"] = org["name"]
            if org.get("primary_domain"):
                match_payload["domain"] = org["primary_domain"]

            match_res = self._request("POST", "/people/match", json=match_payload)
            if "error" not in match_res:
                person = match_res.get("person", {}) or {}
                em = person.get("email")
                if em and not self._is_placeholder_email(em):
                    emails.append(em)
                # phones from match
                for ph in (person.get("phone_numbers") or []):
                    num = ph.get("sanitized_number") or ph.get("raw_number") or ph.get("number")
                    if num and len(num) >= 8:
                        phones.append(num)
                # org phone from match (dict or string)
                m_org_primary = (person.get("organization") or {}).get("primary_phone")
                m_org_num = None
                if isinstance(m_org_primary, dict):
                    m_org_num = m_org_primary.get("sanitized_number") or m_org_primary.get("number")
                elif isinstance(m_org_primary, str):
                    m_org_num = m_org_primary
                if m_org_num and len(m_org_num) >= 8:
                    phones.append(m_org_num)

        # If we require an email and none is available, drop the record
        emails = list(dict.fromkeys(emails))
        if require_email and not emails:
            return None

        # Dedupe phones
        phones = list(dict.fromkeys([x for x in phones if x]))

        return {
            "apollo_id": p.get("id", ""),
            "name": p.get("name", "Unknown"),
            "first_name": p.get("first_name", ""),
            "last_name": p.get("last_name", ""),
            "title": p.get("title", ""),
            "company": org.get("name", ""),
            "domain": org.get("primary_domain", ""),
            "location": self._normalize_location(p.get("city"), p.get("state")),
            "linkedin_url": p.get("linkedin_url", ""),
            "seniority": p.get("seniority", ""),
            "departments": p.get("departments", []),
            "functions": p.get("functions", []),
            "emails": emails,
            "phones": phones,
            "email_status": p.get("email_status", ""),
            "phone_status": p.get("phone_status", ""),
            "source": "apollo.io",
        }

    def _hunter_filter(self, emails: List[str]) -> List[str]:
        """Drop emails that Hunter flags as invalid; keep valid/risky/unknown."""
        out = []
        for addr in emails:
            status = self._hunter_verify(addr)
            if status == "invalid":
                continue
            out.append(addr)
        # ensure uniqueness and preserve order
        seen = set()
        uniq = []
        for e in out:
            if e in seen:
                continue
            seen.add(e)
            uniq.append(e)
        return uniq

    def export_to_csv(self, candidates: List[Dict[str, Any]], file_path: str) -> str:
        """Export candidates to CSV with all common fields and any extra keys."""
        # Ensure the export directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Define standard column order
        standard_cols = [
            "apollo_id", "name", "first_name", "last_name", "title", "company", 
            "domain", "location", "linkedin_url", "emails", "phones", "email_status", 
            "phone_status", "seniority", "departments", "functions", "source", "search_location"
        ]
        
        # Find any extra keys that aren't in standard columns
        all_keys = set()
        for candidate in candidates:
            all_keys.update(candidate.keys())
        extra_cols = sorted(all_keys - set(standard_cols))
        
        # Final column order: standard + extra
        columns = standard_cols + extra_cols
        
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=columns)
            writer.writeheader()
            
            for candidate in candidates:
                row = {}
                for col in columns:
                    value = candidate.get(col, "")
                    
                    # Handle list values (join with semicolon)
                    if isinstance(value, list):
                        if col in ["emails", "phones", "departments", "functions"]:
                            row[col] = ";".join(str(v) for v in value)
                        else:
                            row[col] = json.dumps(value)
                    # Handle dict values (JSON encode)
                    elif isinstance(value, dict):
                        row[col] = json.dumps(value)
                    else:
                        row[col] = str(value) if value is not None else ""
                
                writer.writerow(row)
        
        return file_path

    def upsert_candidates_to_supabase(
        self,
        table: str,
        candidates: List[Dict[str, Any]],
        conflict: str = "apollo_id",
        batch_size: int = 300,
    ) -> Dict[str, Any]:
        """Upsert candidates to Supabase in batches."""
        # Check for Supabase credentials
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            return {"success": False, "error": "Supabase credentials missing"}
        
        try:
            from supabase import create_client
            supabase = create_client(supabase_url, supabase_key)
        except ImportError:
            return {"success": False, "error": "Supabase client not installed"}
        except Exception as e:
            return {"success": False, "error": f"Supabase client error: {str(e)}"}
        
        # Prepare candidates for insertion
        prepared_candidates = []
        for candidate in candidates:
            row = candidate.copy()
            
            # Ensure list fields are JSON-serializable (convert None to empty list)
            for field in ["emails", "phones", "departments", "functions"]:
                if field in row:
                    if row[field] is None:
                        row[field] = []
                    elif not isinstance(row[field], list):
                        row[field] = [row[field]] if row[field] else []
            
            prepared_candidates.append(row)
        
        # Insert in batches
        total_inserted = 0
        errors = []
        
        for i in range(0, len(prepared_candidates), batch_size):
            chunk = prepared_candidates[i:i + batch_size]
            try:
                result = supabase.table(table).upsert(chunk, on_conflict=conflict).execute()
                total_inserted += len(chunk)
                logger.info(f"✅ Upserted batch {i//batch_size + 1}: {len(chunk)} records")
            except Exception as e:
                error_msg = f"Batch {i//batch_size + 1} failed: {str(e)}"
                errors.append(error_msg)
                logger.error(f"❌ {error_msg}")
        
        return {
            "success": len(errors) == 0,
            "inserted": total_inserted,
            "errors": errors
        }

    def unlock_person_email(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """Unlock email for a specific person using Apollo /people/match endpoint"""
        try:
            # Prepare payload for /people/match
            match_payload = {
                "first_name": candidate.get("first_name", ""),
                "last_name": candidate.get("last_name", ""),
                "reveal_email": True,
                "reveal_phone": True,
            }
            
            # Add company/organization info if available
            company = candidate.get("company") or candidate.get("organization", {}).get("name", "")
            if company:
                match_payload["organization_name"] = company
            
            domain = candidate.get("domain") or candidate.get("organization", {}).get("primary_domain", "")
            if domain:
                match_payload["domain"] = domain
            
            # Make API call
            response = self._request("POST", "/people/match", json=match_payload)
            
            if "error" in response:
                return {"success": False, "error": response["error"]}
            
            person = response.get("person", {})
            if not person:
                return {"success": False, "error": "No person found in match result"}
            
            # Extract email
            email = person.get("email", "")
            if not email or self._is_placeholder_email(email):
                return {"success": False, "error": "No valid email found"}
            
            return {
                "success": True,
                "email": email,
                "person": person
            }
            
        except Exception as e:
            logger.error(f"❌ Error unlocking email for {candidate.get('name', 'Unknown')}: {e}")
            return {"success": False, "error": str(e)}

    async def unlock_emails_for_candidates(self, candidates: List[Dict]) -> List[Dict]:
        """Unlock emails for a list of candidates using Apollo professional account"""
        import asyncio
        
        enhanced_candidates = []
        
        for candidate in candidates:
            try:
                current_email = candidate.get("email", "")
                current_phone = candidate.get("phone", "")
                
                # Check if we need to unlock - look for placeholder, missing, or locked emails
                emails_list = candidate.get("emails", [])
                needs_unlock = (
                    "email_not_unlocked" in str(current_email) or 
                    not current_email or 
                    "@" not in str(current_email) or
                    current_email in ["", "N/A", "None"] or
                    "placeholder" in str(current_email).lower() or
                    not emails_list or
                    all(self._is_placeholder_email(e) for e in emails_list)
                )
                
                if needs_unlock:
                    unlock_result = self.unlock_person_email(candidate)
                    
                    if unlock_result.get("success"):
                        new_email = unlock_result["email"]
                        candidate["email"] = new_email
                        candidate["email_status"] = "unlocked"
                        candidate["verified"] = True
                        candidate["confidence_score"] = 0.9
                        
                        # Update emails list
                        if "emails" not in candidate:
                            candidate["emails"] = []
                        if new_email not in candidate["emails"]:
                            candidate["emails"].append(new_email)
                        
                        # Update person data from match result if available
                        if unlock_result.get("person"):
                            person = unlock_result["person"]
                            
                            # Update phone if available
                            if person.get("phone_numbers"):
                                phone_nums = person.get("phone_numbers", [])
                                for phone_data in phone_nums:
                                    if phone_data.get("sanitized_number"):
                                        candidate["phone"] = phone_data["sanitized_number"]
                                        candidate["phone_status"] = "unlocked"
                                        if "phones" not in candidate:
                                            candidate["phones"] = []
                                        if phone_data["sanitized_number"] not in candidate["phones"]:
                                            candidate["phones"].append(phone_data["sanitized_number"])
                                        break
                            
                            # Update organization phone if personal phone not available
                            if not candidate.get("phone") and person.get("organization", {}).get("primary_phone"):
                                org_phone = person["organization"]["primary_phone"]
                                if isinstance(org_phone, dict) and org_phone.get("sanitized_number"):
                                    candidate["phone"] = org_phone["sanitized_number"]
                                    candidate["phone_status"] = "organization"
                                    if "phones" not in candidate:
                                        candidate["phones"] = []
                                    if org_phone["sanitized_number"] not in candidate["phones"]:
                                        candidate["phones"].append(org_phone["sanitized_number"])
                                elif isinstance(org_phone, str):
                                    candidate["phone"] = org_phone
                                    candidate["phone_status"] = "organization"
                                    if "phones" not in candidate:
                                        candidate["phones"] = []
                                    if org_phone not in candidate["phones"]:
                                        candidate["phones"].append(org_phone)
                            
                            # Update organization data
                            if person.get("organization"):
                                candidate["organization"] = person["organization"]
                                if isinstance(person["organization"], dict):
                                    candidate["company"] = person["organization"].get("name", candidate.get("company", ""))
                        
                        logger.info(f"✅ Unlocked contact for {candidate.get('name', 'Unknown')}: {new_email}")
                    else:
                        logger.warning(f"⚠️ Failed to unlock contact for {candidate.get('name', 'Unknown')}: {unlock_result.get('error', 'Unknown error')}")
                else:
                    # Email already exists and is valid
                    candidate["email_status"] = "existing"
                    candidate["verified"] = True
                
                enhanced_candidates.append(candidate)
                
                # Rate limiting - Apollo allows 200 requests per minute for email unlocking
                await asyncio.sleep(0.3)  # ~200 per minute
                
            except Exception as e:
                logger.error(f"❌ Error processing candidate {candidate.get('name', 'Unknown')}: {e}")
                enhanced_candidates.append(candidate)
        
        unlocked_count = sum(1 for c in enhanced_candidates if c.get("email_status") == "unlocked")
        existing_count = sum(1 for c in enhanced_candidates if c.get("email_status") == "existing")
        logger.info(f"📧 Contact processing complete: {unlocked_count} unlocked, {existing_count} existing emails")
        
        return enhanced_candidates

    async def search_dvm_with_auto_campaign(
        self,
        locations: List[str],
        *,
        per_city_limit: int = 15,
        require_email: bool = True,
        require_phone: bool = False,
        hunter_verify: bool = True,
        unlock_emails: bool = True,
        auto_create_campaign: bool = True,
        campaign_name: Optional[str] = None,
        send_immediately: bool = False,
        delay_hours: int = 24,
    ) -> Dict[str, Any]:
        """
        OPTION A: Full Auto-Campaign Integration for DVM searches
        1. Search DVMs across locations
        2. Auto-create campaign with pre-built templates
        3. Schedule sending based on preferences
        """
        try:
            logger.info(f"🚀 AUTO-CAMPAIGN DVM SEARCH: {locations}")
            
            # Step 1: Run async DVM search
            search_result = await self.search_dvm_in_locations(
                locations=locations,
                per_city_limit=per_city_limit,
                require_email=require_email,
                require_phone=require_phone,
                hunter_verify=hunter_verify,
                unlock_emails=unlock_emails,
            )
            
            if not search_result.get("success") or not search_result.get("candidates"):
                logger.warning("⚠️ No candidates found for auto-campaign")
                return {
                    **search_result,
                    "campaign_created": False,
                    "campaign_reason": "No candidates found"
                }
            
            candidates = search_result["candidates"]
            verified_candidates = [c for c in candidates if c.get("emails") and c.get("verified", True)]
            
            logger.info(f"📧 Found {len(verified_candidates)} verified candidates for campaign")
            
            if auto_create_campaign and verified_candidates:
                # Step 2: Auto-create campaign
                campaign_result = self._create_dvm_campaign(
                    candidates=verified_candidates,
                    campaign_name=campaign_name or f"DVM Outreach - {', '.join(locations)} - {datetime.now().strftime('%Y-%m-%d')}",
                    send_immediately=send_immediately,
                    delay_hours=delay_hours,
                    locations=locations
                )
                
                # Step 3: Merge results
                return {
                    **search_result,
                    "campaign_created": campaign_result.get("success", False),
                    "campaign_id": campaign_result.get("campaign_id"),
                    "campaign_name": campaign_result.get("campaign_name"),
                    "campaign_details": campaign_result,
                    "verified_candidates": len(verified_candidates),
                    "auto_campaign_enabled": True,
                    "send_scheduled": not send_immediately,
                    "send_delay_hours": delay_hours if not send_immediately else 0,
                }
            else:
                return {
                    **search_result,
                    "campaign_created": False,
                    "campaign_reason": "Auto-campaign disabled or no verified candidates",
                    "verified_candidates": len(verified_candidates),
                }
                
        except Exception as e:
            logger.error(f"❌ Auto-campaign DVM search failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "campaign_created": False,
                "candidates": [],
                "total_found": 0,
            }

    def _create_dvm_campaign(
        self,
        candidates: List[Dict[str, Any]],
        campaign_name: str,
        send_immediately: bool = False,
        delay_hours: int = 24,
        locations: List[str] = None,
    ) -> Dict[str, Any]:
        """Create auto-campaign for DVM candidates with pre-built templates"""
        try:
            logger.info(f"📧 Creating DVM campaign: {campaign_name}")
            
            # Get DVM email templates
            email_templates = self._get_dvm_email_templates(locations or [])
            
            # Prepare campaign data
            campaign_data = {
                "id": f"dvm_campaign_{int(time.time())}",
                "name": campaign_name,
                "type": "dvm_outreach",
                "status": "ready" if send_immediately else "scheduled",
                "target_audience": "veterinarians",
                "locations": locations or [],
                "candidates": candidates,
                "verified_count": len([c for c in candidates if c.get("verified", True)]),
                "email_templates": email_templates,
                "send_immediately": send_immediately,
                "delay_hours": delay_hours,
                "scheduled_send_time": None if send_immediately else self._calculate_send_time(delay_hours),
                "created_at": datetime.now().isoformat(),
                "platform": "instantly",  # Default to Instantly.ai
                "from_email": os.getenv("CAMPAIGN_FROM_EMAIL", "outreach@coogi.ai"),
                "from_name": os.getenv("CAMPAIGN_FROM_NAME", "Coogi Talent Team"),
                "unsubscribe_url": os.getenv("UNSUBSCRIBE_URL", "https://coogi.ai/unsubscribe"),
                "tracking_enabled": True,
                "personalization_enabled": True,
            }
            
            # Save campaign to database/file for tracking
            campaign_file = f"campaigns/dvm_campaign_{int(time.time())}.json"
            self._save_campaign_data(campaign_data, campaign_file)
            
            # If sending immediately, trigger the send
            if send_immediately:
                send_result = self._trigger_campaign_send(campaign_data)
                campaign_data["send_result"] = send_result
                campaign_data["status"] = "sent" if send_result.get("success") else "failed"
            
            logger.info(f"✅ DVM campaign created: {campaign_data['id']}")
            
            return {
                "success": True,
                "campaign_id": campaign_data["id"],
                "campaign_name": campaign_name,
                "candidates_count": len(candidates),
                "verified_count": campaign_data["verified_count"],
                "status": campaign_data["status"],
                "scheduled_send_time": campaign_data["scheduled_send_time"],
                "email_templates_count": len(email_templates),
                "platform": campaign_data["platform"],
                "campaign_data": campaign_data,
            }
            
        except Exception as e:
            logger.error(f"❌ Campaign creation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "campaign_id": None,
            }

    def _get_dvm_email_templates(self, locations: List[str] = None) -> List[Dict[str, Any]]:
        """Get pre-built DVM email templates with personalization"""
        
        location_text = f" in {', '.join(locations[:2])}" if locations else ""
        if len(locations) > 2:
            location_text += f" and {len(locations)-2} other locations"
        
        templates = [
            {
                "step": 1,
                "delay_days": 0,
                "subject": f"Exciting Veterinary Opportunity{location_text}",
                "body": f"""Hi {{{{first_name}}}},

I hope this message finds you well! I'm reaching out because I came across your profile and was impressed by your expertise in veterinary medicine.

We're currently working with several top-tier veterinary practices{location_text} that are looking for talented DVMs like yourself. These positions offer:

• Competitive salary packages ($90K-$150K+ based on experience)
• Excellent work-life balance with flexible scheduling
• State-of-the-art facilities and equipment
• Continuing education support and career growth opportunities
• Sign-on bonuses and relocation assistance available

Would you be open to a brief conversation about these opportunities? I'd love to learn more about your career goals and see if there's a good match.

Best regards,
{{{{from_name}}}}
{{{{from_email}}}}

P.S. Even if you're not actively looking, I'd be happy to keep you in mind for future opportunities that might be a perfect fit.""",
                "personalization_fields": ["first_name", "company", "location", "title"],
                "tracking_enabled": True,
            },
            {
                "step": 2,
                "delay_days": 3,
                "subject": "Quick follow-up - Veterinary positions still available",
                "body": f"""Hi {{{{first_name}}}},

I wanted to follow up on my previous message about veterinary opportunities{location_text}. 

I understand how busy things can get in veterinary practice, so I'll keep this brief.

Our clients are specifically looking for experienced veterinarians, and based on your background at {{{{company}}}}, I think you'd be a great fit for several positions we're currently filling.

Would you have 10 minutes this week for a quick call? I can share more details about:
• Specific practice types and specializations available
• Salary ranges and benefits packages
• Locations and practice cultures

No pressure at all - just wanted to make sure you had the opportunity to learn more.

Best,
{{{{from_name}}}}""",
                "personalization_fields": ["first_name", "company", "location"],
                "tracking_enabled": True,
            },
            {
                "step": 3,
                "delay_days": 7,
                "subject": "Last note - thought you might find this interesting",
                "body": f"""Hi {{{{first_name}}}},

I hope you don't mind one last follow-up. I wanted to share something that might interest you as a veterinarian.

We just had a DVM join one of our client practices{location_text}, and they mentioned how refreshing it was to find a workplace that truly values:
• Professional development and continuing education
• Work-life balance (no more 60-hour weeks!)
• Modern equipment and technology
• Supportive team environment

If any of this resonates with you, I'd still love to chat. Sometimes the best opportunities come when we're not actively looking.

Feel free to reach out anytime - my contact info is below.

Wishing you all the best in your veterinary career,
{{{{from_name}}}}
{{{{from_email}}}}

P.S. If you know any other great veterinarians who might be interested, referrals are always appreciated!""",
                "personalization_fields": ["first_name", "location"],
                "tracking_enabled": True,
            }
        ]
        
        return templates

    def _calculate_send_time(self, delay_hours: int) -> str:
        """Calculate scheduled send time based on delay"""
        from datetime import timedelta
        send_time = datetime.now() + timedelta(hours=delay_hours)
        return send_time.isoformat()

    def _save_campaign_data(self, campaign_data: Dict[str, Any], file_path: str) -> bool:
        """Save campaign data for tracking and execution"""
        try:
            # Ensure campaigns directory exists
            Path("campaigns").mkdir(exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(campaign_data, f, indent=2, default=str)
            
            logger.info(f"💾 Campaign data saved: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save campaign data: {e}")
            return False

    def _trigger_campaign_send(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger immediate campaign send (placeholder for actual email service integration)"""
        try:
            logger.info(f"📤 Triggering campaign send: {campaign_data['name']}")
            
            # This is where you'd integrate with your actual email service
            # For now, we'll create a mock successful response
            
            candidates = campaign_data.get("candidates", [])
            templates = campaign_data.get("email_templates", [])
            
            if not candidates or not templates:
                return {"success": False, "error": "No candidates or templates"}
            
            # Mock sending logic
            sent_count = 0
            failed_count = 0
            
            for candidate in candidates:
                if candidate.get("emails"):
                    # Here you would actually send the email using:
                    # - Instantly.ai API
                    # - Smartlead.ai API  
                    # - AWS SES
                    # - Your preferred email service
                    
                    # For now, we'll just log and increment counter
                    logger.info(f"📧 [MOCK] Sending to {candidate.get('name', 'Unknown')} ({candidate.get('emails', [])[0] if candidate.get('emails') else 'No email'})")
                    sent_count += 1
                else:
                    failed_count += 1
            
            return {
                "success": True,
                "sent_count": sent_count,
                "failed_count": failed_count,
                "total_candidates": len(candidates),
                "send_time": datetime.now().isoformat(),
                "platform": campaign_data.get("platform", "mock"),
                "campaign_id": campaign_data.get("id"),
            }
            
        except Exception as e:
            logger.error(f"❌ Campaign send failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "sent_count": 0,
                "failed_count": len(campaign_data.get("candidates", [])),
            }

# ----------------------- example usage (optional) -----------------------
if __name__ == "__main__":
    mgr = ApolloManager()

    # Real client use case with email unlocking:
    openings = ["Sebastian, FL", "Cumberland, RI", "Summit, NJ", "West Orange, NJ"]
    result = mgr.search_dvm_in_locations(
        openings,
        per_city_limit=15,
        require_email=True,
        require_phone=False,      # set True if you want to force phones present
        hunter_verify=True,
        unlock_emails=True,       # NEW: automatically unlock emails using /people/match
    )

    print("Total candidates:", result.get("total_found"))
    for c in result.get("candidates", [])[:5]:
        print(
            c.get("search_location"),
            "=>",
            c.get("name"),
            "|",
            c.get("title"),
            "|",
            c.get("company"),
            "| Email(s):", c.get("emails"),
            "| Phone(s):", c.get("phones"),
            "| LinkedIn:", c.get("linkedin_url"),
        )