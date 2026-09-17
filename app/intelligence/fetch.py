import ipaddress, socket
from urllib.parse import urlparse
import httpx
from app.core.errors import UnsafeExternalContentError

class SafeFetcher:
    def validate_url(self, url: str) -> None:
        parsed=urlparse(url)
        if parsed.scheme not in {'http','https'} or not parsed.hostname:
            raise UnsafeExternalContentError('Unsupported or malformed URL')
        infos=socket.getaddrinfo(parsed.hostname, None)
        for info in infos:
            addr=ipaddress.ip_address(info[4][0])
            if addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved or addr.is_multicast:
                raise UnsafeExternalContentError('Blocked non-public destination')
    def get(self, url: str, max_bytes: int=2_000_000):
        self.validate_url(url)
        with httpx.Client(follow_redirects=False, timeout=20, headers={'User-Agent':'USBCSD-Intelligence/1.0'}) as client:
            response=client.get(url)
            if response.is_redirect:
                location=response.headers.get('location')
                if not location: raise UnsafeExternalContentError('Redirect missing location')
                self.validate_url(location)
                response=client.get(location)
            response.raise_for_status()
            if len(response.content)>max_bytes: raise ValueError('Response too large')
            return response
