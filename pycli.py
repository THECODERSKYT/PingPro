#!/usr/bin/env python3
import requests
import time
import argparse
import sys
from datetime import datetime

# असुरक्षित HTTPS अनुरोधों के लिए चेतावनी को अक्षम करें (verify=False के लिए)
try:
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
except ImportError:
    pass

# कमांड-लाइन आर्ग्यूमेंट्स को पार्स करने के लिए argparse का सेटअप
parser = argparse.ArgumentParser(
    description="PingerPro CLI - A command-line website status checker.",
    epilog="Example: python3 pycli.py https://example.com -i 10"
)
parser.add_argument('url', type=str, help='The full URL of the website to ping (e.g., https://example.com)')
parser.add_argument('-i', '--interval', type=int, default=30, help='Interval between pings in seconds. Default: 30.')
parser.add_argument('-s', '--silent', action='store_true', help='Run in silent mode (only prints status changes and errors).')

# यदि कोई आर्ग्यूमेंट नहीं दिया गया है, तो मदद संदेश दिखाएं
if len(sys.argv) == 1:
    parser.print_help(sys.stderr)
    sys.exit(1)

args = parser.parse_args()

# बेसिक वेरिएबल्स
url_to_ping = args.url
interval_seconds = args.interval
is_silent = args.silent
last_status = None
ping_counter = 0

# एक ब्राउज़र जैसा यूजर-एजेंट ताकि वेबसाइट ब्लॉक न करे
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def ping_website(url):
    """एकल पिंग करता है और (status, message) लौटाता है"""
    try:
        # यदि URL में http/https नहीं है, तो https जोड़ें
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        # SSL वेरिफिकेशन को अक्षम करें ताकि सर्टिफिकेट एरर न आए
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        
        # HTTP स्टेटस कोड की जाँच करें
        if 200 <= response.status_code < 400:
            return ("ONLINE", f"HTTP {response.status_code}")
        else:
            return ("OFFLINE", f"HTTP {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        # कनेक्शन एरर को हैंडल करें
        return ("ERROR", "Connection failed")

# --- मुख्य लूप ---
try:
    print("--- PingerPro CLI Started ---")
    print(f"URL: {url_to_ping}")
    print(f"Interval: {interval_seconds} seconds")
    print("Press Ctrl+C to stop.")
    print("-" * 30)

    while True:
        status, message = ping_website(url_to_ping)
        ping_counter += 1
        
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # आउटपुट को मैनेज करें (साइलेंट मोड या नॉर्मल मोड)
        if is_silent:
            if status != last_status and status != "ONLINE":
                print(f"[{current_time}] Status Change: {status} | Reason: {message}")
        else:
            print(f"[{current_time}] Check #{ping_counter}: Status: {status} | Details: {message}")
            
        last_status = status
        time.sleep(interval_seconds)

except KeyboardInterrupt:
    print("\n--- PingerPro CLI Stopped by user ---")
    sys.exit(0)
except Exception as e:
    print(f"\nAn unexpected error occurred: {e}")
    sys.exit(1)
