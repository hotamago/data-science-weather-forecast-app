import os
import json
import hashlib

class CacheManager:
    def __init__(self, cache_dir="cache"):
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

    def get_cache_key(self, *args):
        key = "_".join(map(str, args))
        # return hashlib.md5(key.encode()).hexdigest()
        return key

    def get_cache_file(self, key):
        return os.path.join(self.cache_dir, f"{key}.json")

    def load(self, *args):
        key = self.get_cache_key(*args)
        cache_file = self.get_cache_file(key)
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                return json.load(f)
        return None

    def save(self, data, *args):
        key = self.get_cache_key(*args)
        cache_file = self.get_cache_file(key)
        with open(cache_file, 'w') as f:
            json.dump(data, f)

    def clear_cache(self, *args):
        key = self.get_cache_key(*args)
        cache_file = self.get_cache_file(key)
        if os.path.exists(cache_file):
            os.remove(cache_file)

cache_manager = CacheManager(
    cache_dir=".cache"
)