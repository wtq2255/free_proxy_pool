import asyncio
from config import get_proxy_url


class ProxyPool(object):
    def __init__(self):
        self._proxy_getter = {}

    def register(self, url, proxy_getter_cls):
        self._proxy_getter[url] = proxy_getter_cls()

    def isregistered(self, url):
        return url in self._proxy_getter

    def get_proxy_getter(self, url):
        return self._proxy_getter[url]

    async def run(self):
        dos = []
        for url in get_proxy_url():
            if self.isregistered(url) is False:
                raise NotImplementedError(url)
            getter_obj = self.get_proxy_getter(url)
            dos.append(getter_obj.do(url))
        results = await asyncio.gather(*dos)
        return results


proxy_pool = ProxyPool()
