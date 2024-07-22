from requests import PreparedRequest, Response
from requests.adapters import HTTPAdapter
from .config import DEFAULT_TIMEOUT
from urllib3.util.retry import Retry


class TimeoutHTTPAdapter(HTTPAdapter):
     
    def __init__(self, *args, **kwargs):
        self.timeout = DEFAULT_TIMEOUT

        if 'timeout' in kwargs:
            self.timeout = kwargs['timeout']
            del kwargs['timeout']
        
        super().__init__(*args, **kwargs)
    
    def send(self, request:PreparedRequest, **kwargs) -> Response:
        
        timeout = kwargs.get('timeout')
        
        if timeout is None:
            kwargs['timeout'] = self.timeout
        
        return super().send(request, **kwargs)
        
            