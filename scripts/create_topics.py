from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka import KafkaException
from app.config import settings

def main():
    admin = AdminClient({"bootstrap.servers": settings.kafka_bootstrap_servers})

    topics = [
        NewTopic(settings.topic_match_events, num_partitions=3, replication_factor=1),
        NewTopic(settings.topic_player_events, num_partitions=3, replication_factor=1),
        NewTopic(settings.topic_predictions, num_partitions=3, replication_factor=1),
    ]

    fs = admin.create_topics(topics)

    ok = True
    for name, f in fs.items():
        try:
            f.result()
            print(f"✅ Created topic: {name}")
        except KafkaException as e:
            # TopicAlreadyExists is fine
            msg = str(e)
            if "TOPIC_ALREADY_EXISTS" in msg or "TopicAlreadyExists" in msg:
                print(f"Topic already exists: {name}")
            else:
                ok = False
                print(f"Failed creating topic {name}: {e}")

    if ok:
        print("Topic setup done.")
    else:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
