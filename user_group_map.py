from workspace import CACHE
from json_store.json_store import JSONStore

user_map : JSONStore = None

def init():
    global user_map
    user_map = JSONStore(CACHE / "user_group_map.json", mode=0o644)

def set(userid, groupid):
    user_map[userid] = groupid
    user_map.sync()

def get(userid):
    return user_map.get(userid, None)
