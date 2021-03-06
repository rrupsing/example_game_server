"""
Module contains RedisHashDict, which allows users to interact with Redis hashes
as if they were Python dictionaries.
"""
import redis_config
import UserDict

class RedisHashDict(UserDict.DictMixin):
    def __init__(self, hash_key, redis_client=redis_config.CLIENT):
        self._client = redis_client
        self.hash_key = hash_key

    def keys(self):
        return self._client.hkeys(self.hash_key)

    def __len__(self):
        return self._client.hlen(self.hash_key)

    def __getitem__(self, key):
        return self._client.hget(self.hash_key, key)

    def __setitem__(self, key, val):
        return self._client.hset(self.hash_key, key, val)

    def __delitem__(self, key):
        return self._client.hdel(self.hash_key, key)

    def __contains__(self):
        return self._client.hexists(self.hash_key, key)

    def get(self, key, default=None):
        return self.__getitem__(key) or default

    def delete(self):
        return self._client.delete(self.hash_key)
