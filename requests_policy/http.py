import requests
from .http_hooks import hook_raise_for_status, logging_hook
from urllib3.util.retry import Retry
from .http_adapters import TimeoutHTTPAdapter
from .config import DEBUG

retry_policy = Retry(
    total=2,
    backoff_factor=1.5,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
)

adapter = TimeoutHTTPAdapter(max_retries=retry_policy)

http = requests.Session()
http.mount('http://', adapter)
http.mount('https://', adapter)

http.hooks['response'] = [hook_raise_for_status]

if DEBUG:
    http.hooks['response'].append(logging_hook)
