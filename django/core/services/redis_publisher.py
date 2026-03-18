import json
import redis
from django.conf import settings

redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    decode_responses=True
)

def publish_to_bridge(listener: str, event: str, data: dict):
    message = {
        'listener': listener,
        'event': event,
        'data': data
    }
    
    redis_client.publish('bridge', json.dumps(message))

