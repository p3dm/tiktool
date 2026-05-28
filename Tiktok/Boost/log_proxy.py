import os
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
    "192.168.1.88:5555",
    "192.168.1.65:5555",
    "192.168.1.67:5555",
    "192.168.1.68:5555",
    "192.168.1.70:5555",
    "192.168.1.71:5555",
    "192.168.1.72:5555",
    "192.168.1.73:5555",
    "192.168.1.74:5555",
    "192.168.1.75:5555",
    "192.168.1.76:5555",
    "192.168.1.77:5555",
    "192.168.1.78:5555",
    "192.168.1.79:5555",
    "192.168.1.80:5555",
    "192.168.1.81:5555",
    "192.168.1.83:5555",
    "192.168.1.87:5555",
    "192.168.1.89:5555",

    # "192.168.1.214:5555",
    # "192.168.1.217:5555",
    # "192.168.1.213:5555",
    # "192.168.1.215:5555",
    # "192.168.1.218:5555",
    # "192.168.1.222:5555",
    # "192.168.1.219:5555",
    # "192.168.1.223:5555",
    # "192.168.1.220:5555",
    # "192.168.1.226:5555",
    # "192.168.1.227:5555",
    # "192.168.1.228:5555",
    # "192.168.1.229:5555",
    # "192.168.1.225:5555",
    # "192.168.1.241:5555",
    # "192.168.1.234:5555",
    # "192.168.1.240:5555",
    # "192.168.1.238:5555",
    # "192.168.1.235:5555",
    # "192.168.1.224:5555",
]

Proxy = [
    # "23.130.124.74:44891:190546c5dp:190546c5dp",
    # "23.130.124.236:44891:190546c5dp:190546c5dp",
    # "23.130.124.87:44891:190546c5dp:190546c5dp",
    # "23.130.124.64:44891:190546c5dp:190546c5dp",
    # "23.130.124.35:44891:190546c5dp:190546c5dp",
    # "23.130.124.239:44891:190546c5dp:190546c5dp",
    # "23.130.124.246:44891:190546c5dp:190546c5dp",
    # "23.130.124.248:44891:190546c5dp:190546c5dp",
    # "23.130.124.140:44891:190546c5dp:190546c5dp",
    # "23.130.124.201:44891:190546c5dp:190546c5dp",
    # "23.130.124.61:44891:190546c5dp:190546c5dp",
    # "23.130.124.38:44891:190546c5dp:190546c5dp",
    # "23.130.124.41:44891:190546c5dp:190546c5dp",
    # "23.130.124.4:44891:190546c5dp:190546c5dp",
    # "23.130.124.92:44891:190546c5dp:190546c5dp",
    # "23.130.124.85:44891:190546c5dp:190546c5dp",
    # "23.130.124.63:44891:190546c5dp:190546c5dp",
    # "23.130.124.10:44891:190546c5dp:190546c5dp",
    # "23.130.124.127:44891:190546c5dp:190546c5dp",
    # "23.130.124.241:44891:190546c5dp:190546c5dp",

]
ADB_PATH = r"../adb/windows/adb.exe"

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