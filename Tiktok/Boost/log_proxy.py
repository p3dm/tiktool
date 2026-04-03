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
    "192.168.1.140:5555",
    # "192.168.1.141:5555",
    "192.168.1.145:5555",
    "192.168.1.148:5555",
    # "192.168.1.149:5555",
    # "192.168.1.152:5555",
    # "192.168.1.154:5555",
    # "192.168.1.155:5555",
    # "192.168.1.156:5555",
    # "192.168.1.159:5555",
    # "192.168.1.160:5555",
    "192.168.1.162:5555",
    # "192.168.1.163:5555",
    "192.168.1.71:5555",
    "192.168.1.72:5555",
    # "192.168.1.73:5555",
    "192.168.1.74:5555",
    # "192.168.1.75:5555",
    # "192.168.1.76:5555",
    # "192.168.1.77:5555",
]

Proxy = [
"51.81.76.65:30885:jfde2n8m:jFDE2n8M", 
# "23.131.196.223:44328:230340la75:230340la75",
"88.216.99.151:36972:gvpw6y7l:gVpW6y7L",
"135.148.11.203:31280:PUS37118:ihYegmaf",
# "23.131.196.64:44328:230340la75:230340la75",
# "23.131.196.30:44328:230340la75:230340la75",
# "23.131.196.128:44328:230340la75:230340la75",
# "23.131.196.128:44328:230340la75:230340la75",
# "23.131.196.153:44328:230340la75:230340la75",
# "23.131.196.34:44328:230340la75:230340la75",
# "23.131.196.115:44328:230340la75:230340la75", 
"135.148.11.203:31280:PUS37118:ihYeglmaf", 
# "23.131.196.222:44328:230340la75:230340la75",
"135.148.11.203:31280:mela0n5h:mELA0n5H",
"51.91.67.218:7777:5eft078l:NdMXvJPxhSM5",
# "23.131.196.18:44328:230340la75:230340la75", 
"135.148.11.203:31280:aibf2m1c:aIBF2m1C", 
# "23.131.196.159:44328:230340la75:230340la75",
# "23.131.196.60:44328:230340la75:230340la75",
# "23.131.196.76:44328:230340la75:230340la75",
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
    # d.app_start(XPATH['app'])
    # rotate(device_id)
    # time.sleep(10)
    # d.xpath(XPATH['protocol_type']).click()
    # rotate(device_id)
    # time.sleep(5)
    # d.xpath(XPATH['socks5']).click()

    # time.sleep(2)
    # d.xpath(XPATH['ip_address']).click()

    # time.sleep(2)
    # d.send_keys(ip)
    # time.sleep(2)
    # d.xpath(XPATH['port']).click()
    # rotate(device_id)
    # time.sleep(2)
    # d.send_keys(port)
    # time.sleep(2)
    # d.xpath(XPATH['username']).click()
    # rotate(device_id)
    # time.sleep(2)
    # d.send_keys(username)
    # time.sleep(2)
    # d.xpath(XPATH['password']).click()
    # rotate(device_id)
    # time.sleep(2)
    # d.send_keys(password)
    # time.sleep(2)
    # d.xpath(XPATH['connect']).click()
    # rotate(device_id)
    # time.sleep(5)
    # if d.xpath('//*[@text="OK"]').exists:
    #     d.xpath('//*[@text="OK"]').click()
    #     time.sleep(2)
    # if d.xpath('//*[@text="Allow"]').exists:
    #     d.xpath('//*[@text="Allow"]').click()
    #     time.sleep(2)
    # d.press("home")
    time.sleep(2)
    subprocess.run([
        ADB_PATH, "-s", device_id,
        "shell", "am", "start", "-a","android.settings.DATE_SETTINGS"
    ])
    rotate(device_id)
    time.sleep(5)
    if d.xpath(XPATH['time-zone']).exists:
        d.xpath(XPATH['time-zone']).click()
        choose_zone(d)
    else:
        choose_zone(d)
    time.sleep(2)
    d.press("home")
        


if __name__ == "__main__":
    processes = []
    for device_id, proxy in zip(Device_ID, Proxy):
        p = Process(target=main, args=(device_id, proxy))
        processes.append(p)
        p.start()
    for p in processes:
        p.join()