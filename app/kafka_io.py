import json
from confluent_kafka import Producer, Consumer, KafkaException
from app.config import settings

def make_producer() -> Producer:
    conf = {
        "bootstrap.servers": settings.kafka_bootstrap_servers,
        # keep latency low
        "linger.ms": 5,
        "batch.num.messages": 1000,
        "enable.idempotence": False,  # can turn on later
    }
    return Producer(conf)

def make_consumer(topic: str) -> Consumer:
    conf = {
        "bootstrap.servers": settings.kafka_bootstrap_servers,
        "group.id": settings.consumer_group,
        "auto.offset.reset": "latest",
        "enable.auto.commit": True,
        # low-latency polling
        "fetch.wait.max.ms": 25,
        "max.poll.interval.ms": 300000,
    }
    c = Consumer(conf)
    c.subscribe([topic])
    return c

def send_json(producer: Producer, topic: str, value: dict) -> None:
    payload = json.dumps(value).encode("utf-8")
    producer.produce(topic, payload)
    producer.poll(0)  # serve delivery callbacks

def poll_json(consumer: Consumer, timeout: float = 0.05) -> dict | None:
    msg = consumer.poll(timeout)
    if msg is None:
        return None
    if msg.error():
        # Ignore benign errors; raise the rest if you want strictness
        # raise KafkaException(msg.error())
        return None
    return json.loads(msg.value().decode("utf-8"))
