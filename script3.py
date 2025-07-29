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

# Lưu các time theo ip vào redis và xóa đi các time nằm ngoài khoảng 60s so với cái vừa lưu vào.
def process_ip_request(ip, dt):
    key = f"req:{ip}"
    ts = dt.timestamp()

    # Dùng counter theo thời gian
    counter_key = f"counter:{ip}:{int(ts)}"     # Tạo key phụ cho các request cùng ip và cùng time
    counter = r.incr(counter_key)           # Tăng giá trị đếm nếu lặp lại cái key đó.

    # Đặt thời hạn tự hủy cho counter (vì chỉ cần tạm trong quá trình xử lý)
    r.expire(counter_key, 120)

    # Tạo member duy nhất dạng "timestamp:counter"
    member = f"{ts}:{counter}"      # Có dạng: 1443436592.0:1, 1443436592.0:2

    r.zadd(key, {member: ts})
    r.zremrangebyscore(key, 0, ts - 60)

    count = r.zcard(key)
    return count >= 120

# Hàm xử lý log
def detect_get_flood(file_path):
    risk_ip = []
    # Đọc từng dòng log
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            ip, dt, method, bot_type = parse_log_line(line)
            if ip and method == "GET":
                # print(ip, method, bot_type, dt)
                if process_ip_request(ip, dt):
                    block_key = f"blocked:{ip}"
                    if r.exists(block_key):
                        continue

                    # Nếu là bot hợp lệ thì bỏ qua
                    if (
                            (bot_type == "google" and verify_bot_ip(ip, "google.com")) or
                            (bot_type == "bing" and verify_bot_ip(ip, "search.msn.com")) or
                            (bot_type == "facebook" and verify_bot_ip(ip, "facebook.com"))
                    ):
                        continue

                    # Cảnh báo IP và set block key
                    risk_ip_log = f"{ip} - {bot_type}"
                    r.set(block_key, "1", ex=604800)  # 7 ngày
                    # Print kết quả để kiểm tra logic.
                    print(f"Added to Redis: {ip} → {risk_ip_log}")

if __name__ == "__main__":
    detect_get_flood(log_access)
