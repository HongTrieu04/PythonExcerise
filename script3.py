import re
from collections import defaultdict
from datetime import datetime, timedelta
import socket
import os

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
        if "google" in user_agent or "googlebot" in user_agent:
            bot_type = "google"
        elif "bing" in user_agent or "bingbot" in user_agent:
            bot_type = "bing"
        elif "facebook" in user_agent or "facebookexternalhit" in user_agent:
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

def write_result(result_line):
    with open(result_file, "a", encoding='utf-8') as f:
        f.write(result_line + "\n")

def delete_log(file_log):
    lines_to_delete = []
    with open(file_log, "r", encoding='utf-8') as f:
        for line in f:
            time_str = line.strip("Time-Log")[1].strip()
            old_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            cur_time = datetime.now()
            if cur_time - old_time < timedelta(days=7):
                break
            else:
                lines_to_delete.append(line)

    with open(file_log, "r", encoding='utf-8') as f:
        all_lines = f.readlines()

    with open(file_log, "w", encoding='utf-8') as f:
        for line in all_lines:
            if line not in lines_to_delete:
                f.write(line)

# Hàm xử lý log
def detect_get_flood(file_path):
    ip_times = defaultdict(list)

    # Đọc từng dòng log
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            ip, dt, method, bot_type = parse_log_line(line)
            if ip and method == "GET":
                ip_times[(ip, bot_type)].append(dt)

    # Kiểm tra IP nào có >120 request trong vòng 60s
    iptables = []

    for (ip, bot_type), times in ip_times.items():
        times.sort()  # Sắp xếp thời gian tăng dần

        for i in range(len(times)):
            start = times[i]
            count = 1

            # Đếm số request trong 60s từ thời điểm hiện tại
            for j in range(i + 1, len(times)):
                if (times[j] - start).total_seconds() <= 60:
                    count += 1
                else:
                    break
            
            

            if count > 120:
                # bot hợp lệ, không chặn
                if ((bot_type == "google" and verify_bot_ip(ip, "google.com"))
                    or (bot_type == "bing" and verify_bot_ip(ip, "search.msn.com"))
                    or (bot_type == "facebook" and verify_bot_ip(ip, "facebook.com"))
                ):
                    break

                iptables.append((ip, count, start.strftime("%d/%b/%Y:%H:%M:%S")))
                break

    for ip, count, start_time in iptables:
        time_write_log =  datetime.now()
        res = f"{ip} {count} Start Time: {start_time} Time-Log: {time_write_log}"
        write_result(res)
        # print(f"[!] IP {ip} có {count} GET requests trong vòng 60s tại {start_time}")



if __name__ == "__main__":
    detect_get_flood(log_access)
    delete_log(log_access)
