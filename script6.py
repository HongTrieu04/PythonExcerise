import re
from collections import defaultdict
from datetime import datetime
import json
import os

LOG_PATTERN = re.compile(r"\[(.*?)\] VERBOSE\[\d+\]\[(.*?)\] (.*?)\.c: (.*)")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
input_file = os.path.join(BASE_DIR, "log_CC")
result_file = os.path.join(BASE_DIR, "result.json")

def extract_kv_pairs(text):
    # Trích xuất các cặp key:value
    return dict(re.findall(r'(\w+):([^\s]+)', text))

def parse_log_line(line):
    match = LOG_PATTERN.match(line)
    if not match:
        return None

    timestamp_str, call_id, module, log_info = match.groups()
    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
    if not timestamp:
        return None  # Định dạng thời gian không hợp lệ

    if module != "app_verbose":
        return None  # Bỏ qua log từ module khác

    # Xác định loại sự kiện
    if log_info.startswith("START"):
        event_type = "START"
    elif log_info.startswith("RECORD"):
        event_type = "RECORD"
    elif log_info.startswith("END"):
        event_type = "END"
    else:
        event_type = "INFO"

    # Tách key:value từ log_info
    kv = extract_kv_pairs(log_info)

    # Trả về dict chứa các trường cần thiết
    return {
        "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "call_id": call_id,
        "event_type": event_type,
        "caller": kv.get("caller"),
        "callee": kv.get("callee"),
        "ip": kv.get("ip"),
        "sound": kv.get("sound"),
        "direct": kv.get("direct"),
        "hotline_number": kv.get("hotline_number"),
    }

def write_output(data, output_file):
    with open(output_file, "a", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        f.write("\n")

def parse_log_file(filepath, output_file):
    with open(filepath, 'r') as f:
        for line in f:
            data_output = parse_log_line(line)
            if data_output:
                write_output(data_output, output_file)

if __name__ == "__main__":
    parse_log_file(input_file, result_file)

