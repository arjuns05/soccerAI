import json 
from kafka import KafkaProducer, KafkaConsumer 
from app.config import settings 

def make_producer() -> KafkaProducer: 
    return KafkaProducer(
        bootstrap_servers = settings.kafka_bootstrap_servers.split(","), 
        value_serializer = lambda v: json.dumps(v).encode("utf-8"), 
        linger_ms = 5, #helps batching, lowlatency
        acks = 1
    )
def make_consumer(topic:str) -> KafkaConsumer:
    return KafkaConsumer(
        topic, 
        bootstrap_servers = settings.kafka_bootstrap_servers.split(','), 
        group_id = settings.consumer_group, 
        auto_offset_reset = "latest", 
        enable_auto_commit = True, 
        value_deserializer= lambda b: json.loads(b.decode("utf-8")), 
        consumer_timeout_ms = 1000, 
        max_poll_records = 500
    )