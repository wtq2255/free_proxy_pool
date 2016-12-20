#!/usr/bin/env python3
# coding: utf-8

import json as _json
import urllib.parse
from http.cookies import SimpleCookie
from tornado.httputil import url_concat
from tornado.curl_httpclient import CurlAsyncHTTPClient
from tornado.httpclient import AsyncHTTPClient, HTTPError
from tornado.platform.asyncio import AsyncIOMainLoop, to_asyncio_future

AsyncIOMainLoop().install()
AsyncHTTPClient.configure(CurlAsyncHTTPClient)


async def curl_request(method, url, params=None, data=None, json=None, headers=None, cookies=None,
                       compress=None, allow_redirects=True, proxy=None, conn_timeout=10, req_timeout=30):
    headers = headers or {}
    headers['Connection'] = headers.get('Connection') or 'Close'

    kwargs = {
        'method': method
    }
    if params is not None:
        url = url_concat(url, params)

    if data is not None:
        if isinstance(data, list) or isinstance(data, dict):
            if isinstance(data, dict):
                data = data.items()
            data = '&'.join(['%s=%s' % (k, urllib.parse.quote_plus('%s' % v)) for k, v in data])
        kwargs['body'] = data
    elif json is not None:
        kwargs['body'] = _json.dumps(json)

    if cookies is not None:
        headers['Cookie'] = '; '.join(['%s=%s' % (k, v) for k, v in cookies.items()])

    kwargs['headers'] = headers

    if proxy is not None:
        proxy_host, proxy_port = proxy.split(':')
        kwargs['proxy_host'], kwargs['proxy_port'] = proxy_host, int(proxy_port)

    kwargs['connect_timeout'] = conn_timeout
    kwargs['request_timeout'] = req_timeout
    kwargs['use_gzip'] = compress
    kwargs['follow_redirects'] = allow_redirects
    kwargs['validate_cert'] = False

    http = AsyncHTTPClient()
    try:
        resp = await to_asyncio_future(http.fetch(url, **kwargs))
    except tornado.httpclient.HTTPError as httperror:
        url = (url[:128] + '...') if len(url) > 128 else url
        log.error('HTTPError [%s] %s from url(%s)' % (httperror.code, getattr(httperror, 'message', None), url))
        resp = httperror.response
    finally:
        del http
    return resp


class HTTPResp:
    def __init__(self, resp, proxy=None):
        if resp is not None:
            self.html = resp.body
            self.code = resp.code
            self.url = resp.effective_url
            self.cookies = self.get_cookies(resp.headers)
            self.headers = self.get_headers(resp.headers)
        else:
            self.html = b''
            self.code = -1
            self.url = ''
            self.cookies = {}
            self.headers = {}

        self.proxy = proxy

    @staticmethod
    def get_cookies(headers):
        cookies = SimpleCookie()
        cookies.load('; '.join(headers.get_list('Set-Cookie')))
        return dict([(key, cookies[key].value) for key in cookies.keys()])

    @staticmethod
    def get_headers(headers):
        headers.pop('Set-Cookie', None)
        return dict([(key, value) for key, value in headers.items()])

    def __str__(self):
        _items = {'html', 'code', 'url', 'cookies', 'headers', 'proxy'}
        # map(lambda k: (k, ), _items)
        return _json.dumps({k: getattr(self, k, None).decode() if isinstance(getattr(self, k, None), bytes) else getattr(self, k, None)  for k in _items})


class CurlHTTPClient(object):

    def __init__(self, retry=0, timeout=15):
        self.retry = retry
        self.timeout = timeout

    @staticmethod
    def get_cookies(headers):
        cookies = SimpleCookie()
        cookies.load('; '.join(headers.get_list('Set-Cookie')))
        return dict([(key, cookies[key].value) for key in cookies.keys()])

    @staticmethod
    def get_headers(headers):
        headers.pop('Set-Cookie', None)
        return dict([(key, value) for key, value in headers.items()])

    async def request(self, *args, **kwargs):
        ret = HTTPResp(None)
        proxy = kwargs.pop('proxy', None)

        for i in range(self.retry + 1):
            try:
                resp = await curl_request(*args, proxy=proxy, **kwargs)
            except Exception as e:
                log.error('CurlHTTPClient.request: %s' % e)
                continue
            else:
                ret = HTTPResp(resp, proxy)
                if ret.code in [200, 201, 202, 203, 204, 301, 302, 303, 304, 400, 404, 503]:
                    break
        return ret


client = CurlHTTPClient()

async def httpclient(url, method='GET', *args, **kwargs):
    return await client.request(method, url, *args, **kwargs)
