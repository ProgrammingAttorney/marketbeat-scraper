import datetime
import os
import json

def loadCache(cacheName):
    """
    if cache does not exist, it will create it.
    :param cacheName:
    :return: tuple: cache, cacheFilePath
    """
    today = datetime.datetime.today()  # Create an instance for today
    cacheName = f"{cacheName}-{today.month}-{today.day}-{today.year}.json"  # Create a cache with today's date
    if not os.path.isfile(f"./{cacheName}"):
        cacheFile = open(cacheName, "w")
        cache = {}
    else:
        cacheFile = open(cacheName, "r+")
        cache = json.load(cacheFile)
        cacheFile.close()
    return cache, cacheName