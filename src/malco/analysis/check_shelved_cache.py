# check shelved cache. Can maxsize be changed at a later point in time?

from cachetools import LRUCache
from cachetools.keys import hashkey
from shelved_cache import PersistentCache

file_name = "test_increasing_cache"

pc = PersistentCache(LRUCache, file_name, maxsize=4096)        

pc["a"] = 42

pc.close()
breakpoint()

pc2 = PersistentCache(LRUCache, file_name, maxsize=16384)        

breakpoint()
pc2.close()

