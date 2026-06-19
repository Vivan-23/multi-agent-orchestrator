def compute_diff(old_output: dict, new_output: dict) -> dict:
    """
    Compares two scan outputs and returns what changed.
    """
    if not isinstance(old_output, dict) or not isinstance(new_output, dict):
        return {}

    try:
        # Subdomains
        old_subs = set(old_output.get("subdomains") or [])
        new_subs = set(new_output.get("subdomains") or [])
        added_subs = sorted(list(new_subs - old_subs))
        removed_subs = sorted(list(old_subs - new_subs))

        # Endpoints
        old_ends = set(old_output.get("endpoints") or [])
        new_ends = set(new_output.get("endpoints") or [])
        added_ends = sorted(list(new_ends - old_ends))
        removed_ends = sorted(list(old_ends - new_ends))

        # Risk Level
        old_risk = old_output.get("risk_level")
        new_risk = new_output.get("risk_level")
        risk_changed = old_risk != new_risk

        # Malicious Votes
        old_malicious = old_output.get("malicious_votes", 0)
        new_malicious = new_output.get("malicious_votes", 0)
        
        if old_malicious is None:
            old_malicious = 0
        if new_malicious is None:
            new_malicious = 0
            
        try:
            old_malicious = int(old_malicious)
        except (ValueError, TypeError):
            old_malicious = 0
        try:
            new_malicious = int(new_malicious)
        except (ValueError, TypeError):
            new_malicious = 0
        
        malicious_delta = new_malicious - old_malicious

        return {
            "added_subdomains": added_subs,
            "removed_subdomains": removed_subs,
            "added_endpoints": added_ends,
            "removed_endpoints": removed_ends,
            "risk_changed": risk_changed,
            "previous_risk_level": old_risk,
            "current_risk_level": new_risk,
            "malicious_votes_delta": malicious_delta
        }
    except Exception:
        return {}
