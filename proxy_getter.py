import asyncio

from utils import httpclient, RedisSaver
from config import get_proxy_url, get_redis
from proxy_pool import proxy_pool

def register(url):
    def _model_wrapper(cls):
        if not issubclass(cls, ProxyGetterBase):
            raise ValueError('Wrapped class must subclass ProxyGetterBase.')
        proxy_pool.register(url, cls)
        return cls
    return _model_wrapper


redis_saver = RedisSaver('proxy_pool', **get_redis('redis_saver'))


class ProxyGetterBase(object):
    async def do(self, url):
        resp = await httpclient(url)
        if resp.code != 200 or not resp.html:
            return False
        data_list = self.format_proxy_data(resp.html.decode())
        if not data_list or not isinstance(data_list, list):
            return False
        redis_saver.save(*data_list)

    def format_proxy_data(self, data):
        raise NotImplementedError("'%s' object does not implemented method 'format_proxy_data'." % self.__class__.__name__)


@register(url=get_proxy_url('xici'))
class XCProxyGetter(ProxyGetterBase):
    pass


def run():
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(proxy_pool.run())
    print(result)

if __name__ == '__main__':
    run()
