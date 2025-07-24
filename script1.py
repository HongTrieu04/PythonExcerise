from user_agents import parse
import re
from collections import defaultdict
import os

def detect_browser(line):
    return parse(line).browser.family

def analyze_log(file_path):
    browser_count = defaultdict(int)

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            matches = re.findall(r'"(.*?)"', line)
            if len(matches) >= 3:
                user_agent = matches[2]
                browser = detect_browser(user_agent)
                browser_count[browser] += 1

    total = sum(browser_count.values())
    print("Total of user-agent: ", total)

    for browser, count in browser_count.items():
        percent = (count / total) * 100
        print(f"{browser}: {count} ({percent:.2f}%)")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(BASE_DIR, "gistfile1.txt")

# log_file = "/home/lehongtrieu/Documents/Intern/gistfile2.txt"
analyze_log(log_file)
