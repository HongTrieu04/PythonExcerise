import re
from collections import defaultdict
import os

def detect_browser(user_agent):
    if "Chrome" in user_agent and "Safari" in user_agent and "Edge" not in user_agent and "OPR" not in user_agent:
        return "Chrome"
    elif "Firefox" in user_agent:
        return "Firefox"
    elif "Safari" in user_agent and "Chrome" not in user_agent:
        return "Safari"
    elif "Edge" in user_agent or "Edg" in user_agent:
        return "Edge"
    elif "OPR" in user_agent or "Opera" in user_agent:
        return "Opera"
    elif "MSIE" in user_agent or "Trident" in user_agent:
        return "Internet Explorer"
    else:
        return "Other"

# Read file
def analyze_log(file_path):
    browser_count = defaultdict(int)
    total = 0

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            matches = re.findall(r'"(.*?)"', line)
            if len(matches) >= 3:
                user_agent = matches[2]
                browser = detect_browser(user_agent)
                browser_count[browser] += 1
                total += 1

    print("Browser Access Statistics:")
    for browser, count in browser_count.items():
        percent = (count / total) * 100
        print(f"{browser}: {count} ({percent:.2f}%)")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(BASE_DIR, "gistfile2.txt")

# log_file = "/home/lehongtrieu/Documents/Intern/gistfile2.txt"
analyze_log(log_file)
