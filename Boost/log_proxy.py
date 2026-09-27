import os
import sys
import uiautomator2 as u2
import time
from multiprocessing import Process
import subprocess

XPATH = {
    'app': "com.vat.proxyconnector",
    'protocol_type': '//*[@resource-id="com.vat.proxyconnector:id/spinnerItemText"]',
    'ip_address': '//*[@resource-id="com.vat.proxyconnector:id/edtAddressContainer"]',
    'port': '//*[@resource-id="com.vat.proxyconnector:id/edtPortContainer"]',
    'username': '//*[@resource-id="com.vat.proxyconnector:id/edtUsernameContainer"]',
    'password': '//*[@resource-id="com.vat.proxyconnector:id/edtPasswordContainer"]',
    'connect': '//*[@text="CONNECT"]|//*[@resource-id="com.vat.proxyconnector:id/btConnect"]',
    'connect_vn': '//*[@text="KẾT NỐI"]',
    'connect_rs': '',
    'socks5': '//*[@text="socks5"]',
    'https': '//*[@text="https"]',
    'time-zone': '//androidx.recyclerview.widget.RecyclerView/android.widget.LinearLayout[2]/android.widget.LinearLayout[1]/android.widget.LinearLayout[1]/android.widget.Switch[1][@checked="true"]',
    'menu': '//*[@resource-id="com.android.settings:id/sesl_action_bar_overflow_button"]',
}

Device_ID = [
    "192.168.1.132:5555",
    "192.168.1.133:5555",
    "192.168.1.120:5555",
    "192.168.1.135:5555",
    "192.168.1.129:5555",
    "192.168.1.121:5555",
    "192.168.1.130:5555",
    "192.168.1.122:5555",
    "192.168.1.128:5555",
    "192.168.1.117:5555",
    "192.168.1.126:5555",
    "192.168.1.113:5555",
    "192.168.1.118:5555",
    "192.168.1.116:5555",
    "192.168.1.131:5555",
    "192.168.1.123:5555",
    "192.168.1.114:5555",
    "192.168.1.124:5555",
    "192.168.1.158:5555"

]

Proxy = [
    "23.191.248.44:30029:2807gjcjxs:2807gjcjxs",
    "23.191.248.97:30029:2807gjcjxs:2807gjcjxs",
    "23.191.248.118:30029:2807gjcjxs:2807gjcjxs",
    "23.191.248.213:30029:2807gjcjxs:2807gjcjxs",
    "23.191.248.169:30029:2807gjcjxs:2807gjcjxs",
    "23.191.248.89:30029:2807gjcjxs:2807gjcjxs",
    "23.191.248.246:30029:2807gjcjxs:2807gjcjxs",
    "23.191.248.240:30029:2807gjcjxs:2807gjcjxs",
    "23.191.248.31:30029:2807gjcjxs:2807gjcjxs",
    "23.191.248.73:30029:2807gjcjxs:2807gjcjxs",
    "23.191.248.5:30029:2807gjcjxs:2807gjcjxs",
    "23.191.248.164:30029:2807gjcjxs:2807gjcjxs",
    "23.191.248.152:30029:2807gjcjxs:2807gjcjxs",
    "23.191.248.74:30029:2807gjcjxs:2807gjcjxs",
    "23.191.248.70:30029:2807gjcjxs:2807gjcjxs",
    "23.191.248.67:30029:2807gjcjxs:2807gjcjxs",
    "23.191.248.37:30029:2807gjcjxs:2807gjcjxs",
    "23.191.248.134:30029:2807gjcjxs:2807gjcjxs",
    "23.191.248.209:30029:2807gjcjxs:2807gjcjxs",
    # "23.191.248.20:30029:2807gjcjxs:2807gjcjxs"

]
if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ADB_PATH = os.path.join(BASE_DIR, "adb", "windows", "adb.exe")

def parse_data(data):
    ip, port, username, password = data.split(":")
    return ip, port, username, password

def rotate(device_id):
    subprocess.run([
        ADB_PATH, "-s", device_id,
        "shell", "settings", "put",
        "system", "accelerometer_rotation",
        "0"
    ])

def choose_zone(d):
    d.xpath('//*[@text="Select time zone"]').click()
    time.sleep(2)
    d.xpath(XPATH['menu']).click()
    time.sleep(2)
    d.xpath('//*[@text="Select by UTC offset"]').click()
    time.sleep(2)
    d.swipe(500, 1500, 500, 500, duration=0.2)
    time.sleep(1)
    d.swipe(500, 1500, 500, 500, duration=0.2)
    time.sleep(1)
    d.swipe(500, 1500, 500, 500, duration=0.2)
    time.sleep(2)
    d.xpath('//*[@text="GMT+08:00"]').click()
    

def main(device_id, proxy):
    ip, port, username, password = parse_data(proxy)
    d = u2.connect(device_id)
    d.press("home")
    d.app_clear("com.genfarmer.uiautomator")
    d.app_start(XPATH['app'])
    rotate(device_id)
    time.sleep(10)
    d.xpath(XPATH['protocol_type']).click()
    rotate(device_id)
    time.sleep(5)
    d.xpath(XPATH['socks5']).click()

    time.sleep(2)
    d.xpath(XPATH['ip_address']).click()

    time.sleep(2)
    d.send_keys(ip)
    time.sleep(2)
    d.xpath(XPATH['port']).click()
    rotate(device_id)
    time.sleep(2)
    d.send_keys(port)
    time.sleep(2)
    d.xpath(XPATH['username']).click()
    rotate(device_id)
    time.sleep(2)
    d.send_keys(username)
    time.sleep(2)
    d.xpath(XPATH['password']).click()
    rotate(device_id)
    time.sleep(2)
    d.send_keys(password)
    time.sleep(2)
    d.xpath(XPATH['connect']).click()
    rotate(device_id)
    time.sleep(5)
    if d.xpath('//*[@text="OK"]').exists:
        d.xpath('//*[@text="OK"]').click()
        time.sleep(2)
    if d.xpath('//*[@text="Allow"]').exists:
        d.xpath('//*[@text="Allow"]').click()
        time.sleep(2)
    d.press("home")
    time.sleep(2)
    # subprocess.run([
    #     ADB_PATH, "-s", device_id,
    #     "shell", "am", "start", "-a","android.settings.DATE_SETTINGS"
    # ])
    # rotate(device_id)
    # time.sleep(5)
    # if d.xpath(XPATH['time-zone']).exists:
    #     d.xpath(XPATH['time-zone']).click()
    #     choose_zone(d)
    # else:
    #     choose_zone(d)
    # time.sleep(2)
    # d.press("home")
        


if __name__ == "__main__":
    processes = []
    for device_id, proxy in zip(Device_ID, Proxy):
        p = Process(target=main, args=(device_id, proxy))
        processes.append(p)
        p.start()
    for p in processes:
        p.join()