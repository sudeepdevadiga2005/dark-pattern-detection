import re
from urllib.parse import urlparse, urlunparse

# Regex settings
DOMAIN_REGEX = re.compile(r"^(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,63}(?:/.*)?$")
PLAIN_DOMAIN_REGEX = re.compile(r"^(?:www\.)?([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,63}$")
URL_LIKE_REGEX = re.compile(r"^(https?://|www\.)", re.IGNORECASE)

def clean_surrounding_punctuation(value):
    """
    Remove punctuation that may surround a URL/domain in pasted text.
    Keeps dots inside domain names intact.
    """
    if not value:
        return ""
    value = value.strip(' \t\r\n"\'`()[]{}<>')
    value = value.rstrip('.,;:!?')
    return value.strip()

def detect_input_type(user_input):
    """
    Detect whether the input is a URL, plain domain, or just text.
    """
    if not user_input or len(user_input.strip()) < 2:
        return "invalid"
    cleaned = clean_surrounding_punctuation(user_input)
    if URL_LIKE_REGEX.search(cleaned):
        return "url"
    if PLAIN_DOMAIN_REGEX.match(cleaned.lower()):
        return "domain"
    if DOMAIN_REGEX.match(cleaned.lower()):
        return "url"
    return "text"

def ensure_scheme(value):
    """Ensure a protocol scheme is present for parsing."""
    if not value.lower().startswith(("http://", "https://")):
        return "https://" + value
    return value

def extract_domain_from_anything(value):
    """
    Extract clean domain from raw URL/domain text.
    Supports many TLDs.
    """
    if not value:
        return None
    value = clean_surrounding_punctuation(value)
    value = ensure_scheme(value)
    try:
        parsed = urlparse(value)
        domain = parsed.netloc.lower().strip()
        if domain.startswith("www."):
            domain = domain[4:]
        if ":" in domain:
            domain = domain.split(":")[0]
            
        # Enforce that domains must actually have a valid TLD structure (.com, .io, etc.)
        if not re.match(r"^([a-z0-9-]+\.)+[a-z]{2,63}$", domain):
            return None
            
        return domain if domain else None
    except Exception:
        return None

def normalize_full_url(value):
    """
    Normalize URL for exact matching. 
    Keeps path, removes query and fragment for stable exact-url checking.
    """
    if not value:
        return None
    value = clean_surrounding_punctuation(value)
    value = ensure_scheme(value)
    try:
        parsed = urlparse(value)
        netloc = parsed.netloc.lower().strip()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        path = parsed.path or ""
        normalized = urlunparse((
            parsed.scheme.lower() or "https",
            netloc,
            path.rstrip("/"),
            "", "", ""  # ignore queries and fragments
        ))
        return normalized
    except Exception:
        return None
