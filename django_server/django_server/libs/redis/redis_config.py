"""
Monkey patch configuration here...
"""
import redis

CLIENT = redis.Redis(port=6900, password="test")
