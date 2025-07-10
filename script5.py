import re
from collections import defaultdict, Counter
from datetime import datetime, timedelta, time
import redis

r = redis.Redis(decode_responses=True)

# Write log as Sorted Set
# is unique so add timestamp with ssl
def write_log_to_redis(ssl_pro, ssl_cip, time_stamp):
    r.zadd("ssl_protocol log", {f"{time_stamp.timestamp()}|{ssl_pro}": time_stamp.timestamp()})
    r.zadd("ssl_cipher log", {f"{time_stamp.timestamp()}|{ssl_cip}": time_stamp.timestamp()})

# Parse log into ssl and time
def analyze_log(log_file):
    with open(log_file, "r", encoding='utf-8') as l:
        for line in l:
            parts = line.strip().split()
            if len(parts) < 5:
                continue
            time_str = parts[0]
            ssl_protocol = parts[3]
            ssl_cipher = parts[4]
            time_stamp = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S.%f%z")
            time_stamp = time_stamp.replace(tzinfo=None)
            write_log_to_redis(ssl_protocol, ssl_cipher, time_stamp)

def get_logs_last_1_minute():
    current_time = datetime.now()
    one_minute_ago = current_time - timedelta(seconds=60)  # 60s
    logs_protocol = r.zrangebyscore("ssl_protocol log", one_minute_ago.timestamp(), current_time.timestamp())
    logs_cipher = r.zrangebyscore("ssl_cipher log", one_minute_ago.timestamp(), current_time.timestamp())
    return logs_protocol, logs_cipher

# Delete Log after about minutes.
def delete_logs_older_than(minutes=5):
    threshold = time.time() - minutes * 60
    r.zremrangebyscore("ssl_protocol log", 0, threshold)
    r.zremrangebyscore("ssl_cipher log", 0, threshold)

def count_ssl():
    protocol_counter = Counter()
    cipher_counter = Counter()

    list_protocol, list_cipher = get_logs_last_1_minute()

    for item in list_protocol:
        _, proto = item.split("|", 1)
        protocol_counter[proto] += 1
    for pro, count in protocol_counter.items():
        print(f"Protocol: {pro}, Count: {count}")

    for item in list_cipher:
        _, cip = item.split("|", 1)
        cipher_counter[cip] += 1
    for cip, count in cipher_counter.items():
        print(f"Cipher: {cip}, Count: {count}")

