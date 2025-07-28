import re
from collections import defaultdict
from datetime import datetime, timedelta
import socket
import os
import redis

r = redis.Redis(host='localhost', port=6379, db=0)  # Run redis server on localhost.

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
log_access = os.path.join(BASE_DIR, "access.log")
result_file = os.path.join(BASE_DIR, "result_ip.txt")

# Hàm parse dòng log để lấy IP, timestamp và method
def parse_log_line(line):
    pattern = r'(\S+) (\S+) (\S+) \[([^\]]+)\] "(.*?)" (\d{3}) (\S+) "(.*?)" "(.*?)"'
    match = re.match(pattern, line)
    if match:
        ip = match.group(1)
        timestamp_str = match.group(4)
        request = match.group(5)
        user_agent = match.group(9)
        user_agent = user_agent.lower()
        # Parse timestamp thành datetime object
        dt = datetime.strptime(timestamp_str.split()[0], "%d/%b/%Y:%H:%M:%S")

        bot_type = "common-user"
        if "google" in user_agent:
            bot_type = "google"
        elif "bing" in user_agent:
            bot_type = "bing"
        elif "facebook" in user_agent:
            bot_type = "facebook"

        # Parse method
        method = request.split()[0] if request else None

        return ip, dt, method, bot_type
    return None, None, None, None


def verify_bot_ip(ip, domain):
    try:
        # Reverse DNS
        host = socket.gethostbyaddr(ip)[0]
        if not domain in host:
            return False
        # Forward lookup
        forward_ips = socket.gethostbyname_ex(host)[2]
        return ip in forward_ips
    except:
        return False


# Return True if user-agent has over 120 requests per 60 sec
def count_requests(times, threshold=120, time_check=60):
    start = 0
    for end in range(len(times)):
        while (times[end] - times[start]).total_seconds() > time_check:
            start += 1
        if end - start + 1 >= threshold:
            return True
    return False


# Hàm xử lý log
def detect_get_flood(file_path):
    ip_times = defaultdict(list)
    risk_ip = []
    # Đọc từng dòng log
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            ip, dt, method, bot_type = parse_log_line(line)
            if ip and method == "GET":
                ip_times[(ip, bot_type)].append(dt)

    # Kiểm tra IP nào có >120 request trong vòng 60s
    for (ip, bot_type), times in ip_times.items():

        if not count_requests(times):
            continue
        else:
            if ((bot_type == "google" and verify_bot_ip(ip, "google.com"))
                    or (bot_type == "bing" and verify_bot_ip(ip, "search.msn.com"))
                    or (bot_type == "facebook" and verify_bot_ip(ip, "facebook.com"))
            ):
                continue
            else:
                risk_ip_log = f"{ip} - {bot_type}"
                log_key = f"{ip}:{datetime.now().isoformat()}"
                r.set(name=log_key, value=risk_ip_log, ex=604800)
                # Thêm vào list để in ra kiểm tra.
                risk_ip.append((ip, bot_type))

    # Print the results to fix bug.
    for (ip, bot_type) in risk_ip:
        print(ip, bot_type)

if __name__ == "__main__":
    detect_get_flood(log_access)
