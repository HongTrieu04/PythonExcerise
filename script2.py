import re
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
result_file = os.path.join(BASE_DIR, "result.txt")

def component_of_log(log_line):
    pattern = r'(\S+) (\S+) (\S+) \[([^\]]+)\] "(.*?)" (\d{3}) (\S+) "(.*?)" "(.*?)"'
    match = re.match(pattern, log_line)
    if match:
        return list(match.groups())
    return []

def write_result(result_line):
    with open(result_file, "a", encoding='utf-8') as f:
        f.write(result_line + "\n")

def analyze_log(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            parts = component_of_log(line)
            if len(parts) == 9:
                # Chỉ lấy 7 trường đầu tiên: host, ident, authuser, [date], "request", status, bytes
                common_log_format = parts[:7]
                result_line = ' '.join(common_log_format)
                write_result(result_line)


# log_file = "/home/lehongtrieu/Documents/Intern/access.log"
# analyze_log(log_file)

if __name__ == "__main__":
    log_combined = input("Log:")
    res = ""
    parts = component_of_log(log_combined)
    if parts:
        for i in range(7):
            res += parts[i] + " "
    
    print("-" * 50)
    print("Common Log Format:")
    print(res)