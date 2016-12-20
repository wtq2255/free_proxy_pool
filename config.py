import configparser

conf=configparser.ConfigParser()
conf.read('./proxy.conf')


def get_redis(name):
    redis_conf = conf.get('redis', name)
    t1, t2 = redis_conf.strip().split(':')[-2:]
    password, host = t1.strip().split('@')
    port, db = t2.strip().split('/')
    return {'host': host,
            'port': int(port),
            'password': password or None,
            'db': int(db)}


def get_proxy_url(name=None):
    if name is None:
        return list(zip(*conf.items('proxy_url')))[1]
    else:
        if conf.has_option('proxy_url', name):
            return conf.get('proxy_url', name)
        else:
            return None

def get_check(option=None):
    if option is None:
        return dict(conf.items('check'))
    else:
        if conf.has_option('check', option):
            return conf.get('check', option)
        else:
            return None
