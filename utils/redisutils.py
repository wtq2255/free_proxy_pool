import redis

class RedisSaver(object):
    def __init__(self, name, host='127.0.0.1', port=6379, db=0, password=''):
        password = password or None
        self.name = name
        self.r = redis.Redis(host=host, port=port, db=db, password=password)

    def save(self, *items):
        self.r.sadd(self.name, *items)
