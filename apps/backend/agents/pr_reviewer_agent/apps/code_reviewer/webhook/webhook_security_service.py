

def extract_event_key(
    provider : str,
    delivery_id : str,
    repo : str,
    pr_number : int,
    action : str,
    sha : str
) -> str:
    return f"{provider}:{delivery_id}:{repo}:{pr_number}:{action}:{sha}"