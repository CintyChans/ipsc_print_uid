import pylink
from datetime import datetime
import time
import re
import os
import threading
import win32print
import pywintypes
import dl_data
import ui
import json
from env import config_data, cert, ca_cert

import traceback
import subprocess
import os
import glob
import tkinter as tk
from tkinter import messagebox
import pandas as pd
import matplotlib
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ipsc_uid_print_win = ui.Window()


def draw_dis(file_path):
    # 用于判定异常值的最小范围，当箱线图范围小于该值时，使用该值
    min_dis_range = 0.2

    with open(file_path, "r") as file:
        lines = file.readlines()

    # 提取包含 "dis=" 的行并解析时间戳和 dis 值
    dis_pattern = re.compile(
        r"(\d+\s\d{2}:\d{2}:\d{2}\.\d{3}\.\d{3}).*\bdis=(\d+\.\d+)\b"
    )
    data = []
    for line in lines:
        match = dis_pattern.search(line)
        if match:
            timestamp = match.group(1)
            dis_value = float(match.group(2))
            data.append((timestamp, dis_value))

    # 创建 DataFrame
    df = pd.DataFrame(data, columns=["Timestamp", "Dis"])

    # 分离秒和毫秒部分，转换为 datetime 对象
    timestamp_parts = df["Timestamp"].str.extract(
        r"(?P<time>\d{2}:\d{2}:\d{2})\.(?P<millis>\d{3})"
    )
    df["Timestamp"] = pd.to_datetime(
        timestamp_parts["time"], format="%H:%M:%S"
    ) + pd.to_timedelta(timestamp_parts["millis"].astype(int), unit="ms")

    # 将时间戳转换为以毫秒表示的相对时间，并从零开始
    df["Time_ms"] = (
        df["Timestamp"].dt.strftime("%S.%f").astype(float) * 1000
    )  # 转换为毫秒
    df["Time_ms"] = df["Time_ms"] - df["Time_ms"].min()  # 减去起始时间

    # 计算四分位数和 IQR 以检测异常值
    Q1 = df["Dis"].quantile(0.25)
    Q3 = df["Dis"].quantile(0.75)
    IQR = Q3 - Q1

    # 定义异常值边界
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    # 检查 lower_bound 和 upper_bound 的间隔是否小于 0.2，如果是则调整为 0.2
    if (upper_bound - lower_bound) < min_dis_range:
        mid_point = (lower_bound + upper_bound) / 2
        lower_bound = mid_point - min_dis_range / 2
        upper_bound = mid_point + min_dis_range / 2

    # 检测异常值
    outliers = df[(df["Dis"] < lower_bound) | (df["Dis"] > upper_bound)]

    # 计算异常值数量和总数据点数量
    num_outliers = len(outliers)
    total_points = len(df)

    # 计算中值
    median_value = df["Dis"].median()

    # 绘制图表，显示时间随毫秒变化，并高亮异常值
    plt.figure(figsize=(12, 6))
    plt.plot(
        df["Time_ms"],
        df["Dis"],
        marker="o",
        linestyle="-",
        color="b",
        label="Dis Value",
    )
    plt.scatter(outliers["Time_ms"], outliers["Dis"], color="r", label="Outliers")
    plt.title(
        f"Dis Values Over Time with Outliers Highlighted (error: {num_outliers}/{total_points}, median: {median_value:.6f})"
    )
    plt.xlabel("Time (ms)")
    plt.ylabel("Dis Value")
    plt.grid(True)
    plt.tight_layout()
    plt.xticks(
        range(0, int(df["Time_ms"].max()) + 1, 1000)
    )  # 设置整数刻度，步长为1000毫秒
    plt.legend()

    # 绘制箱线图的横线
    plt.axhline(Q1, color="g", linestyle="--", label="Q1")
    plt.axhline(Q3, color="y", linestyle="--", label="Q3")
    plt.axhline(lower_bound, color="m", linestyle=":", label="Lower Bound")
    plt.axhline(upper_bound, color="c", linestyle=":", label="Upper Bound")
    plt.axhline(median_value, color="k", linestyle="-", label="Median")
    plt.legend()

    # 显示图表
    plt.savefig(f"{file_path}_dis.png")


def draw_wakeup_time(file_name, data):

    df = pd.DataFrame(data, columns=["data"])

    # 计算四分位数和 IQR 以检测异常值
    Q1 = df["data"].quantile(0.25)
    Q3 = df["data"].quantile(0.75)
    IQR = Q3 - Q1

    # 定义异常值边界
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    # 检测异常值
    outliers = df[(df["data"] < lower_bound) | (df["data"] > upper_bound)]
    # 计算异常值数量和总数据点数量
    num_outliers = len(outliers)
    total_points = len(df)

    # 计算中值
    median_value = df["data"].median()

    # 绘制图表，显示时间随毫秒变化，并高亮异常值
    plt.figure(figsize=(12, 6))
    plt.scatter(
        range(0, len(data)),
        df["data"],
    )
    plt.title(
        f"wakeup_time Values Over Time with Outliers Highlighted (error: {num_outliers}/{total_points}, median: {median_value:.6f})"
    )
    plt.ylabel("wakeup_time Value")
    plt.grid(True)
    plt.tight_layout()

    # 绘制箱线图的横线
    plt.axhline(Q1, color="g", linestyle="--", label="Q1")
    plt.axhline(Q3, color="y", linestyle="--", label="Q3")
    plt.axhline(lower_bound, color="m", linestyle=":", label="Lower Bound")
    plt.axhline(upper_bound, color="c", linestyle=":", label="Upper Bound")
    plt.axhline(median_value, color="k", linestyle="-", label="Median")
    plt.legend()
    plt.savefig(f"{file_name}_wakeup_time.png")


def run_jlink_command(p1):
    try:

        process = subprocess.Popen(
            ["jlink"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        process.stdin.write("connect" + "\n")
        process.stdin.flush()

        process.stdin.write("nRF52840_xxAA" + "\n")
        process.stdin.flush()

        process.stdin.write("SWD" + "\n")
        process.stdin.flush()

        process.stdin.write("4000kHZ" + "\n")
        process.stdin.flush()
        if p1:
            process.stdin.write("erase  " + "\n")
        else:
            process.stdin.write("erase 0x00000000   0x000FFFFF" + "\n")

        process.stdin.flush()

        output, _ = process.communicate()

        return output.strip()
    except Exception as e:
        return f"Error: {e}"


class jlink:
    def __init__(self):
        if not os.path.exists("logs"):
            os.makedirs("logs")
        self.duration = 0
        self.in_test = 0
        self.product_test_master_start_time = 0
        self.get_uid_flag = 0
        self.product_test_io_flag = 0
        self.product_test_master_flag = 0
        self.short_uid = ""
        self.logging = 0
        self.rtt_is_running = False
        self.firmware_version = ""

        self.manufacture_device_postUrl = config_data["manufacture_device"]["url"]
        self.jlink = pylink.JLink()

    def set_hardware_info(self):
        try:
            if not self.jlink.target_connected():
                self.connect_target()

            now = datetime.now()
            year = now.year
            month = now.month
            day = now.day
            cmd = ""
            if ipsc_uid_print_win.var1.get():
                version = ipsc_uid_print_win.gateway_version_dropdown.get().split(".")
                cmd = f" arg_hardware_info {0} {version[0]} {version[1]} {ipsc_uid_print_win.gateway_batch_dropdown.get()} {year} {month} {day} { ipsc_uid_print_win.gateway_model_dropdown.get() }"
            elif ipsc_uid_print_win.var2.get():
                version = ipsc_uid_print_win.anchor_version_dropdown.get().split(".")
                cmd = f" arg_hardware_info {0}  {version[0]} {version[1]} {ipsc_uid_print_win.anchor_batch_dropdown.get()} {year} {month} {day} { ipsc_uid_print_win.anchor_model_dropdown.get() }"
            elif ipsc_uid_print_win.var3.get():
                version = ipsc_uid_print_win.tag_version_dropdown.get().split(".")
                cmd = f" arg_hardware_info {0} {version[0]} {version[1]} {ipsc_uid_print_win.tag_batch_dropdown.get()} {year} {month} {day} { ipsc_uid_print_win.tag_model_dropdown.get() }"
            ipsc_uid_print_win.add_log(cmd)
            _ = self.jlink.rtt_write(0, list(bytearray(cmd, "utf-8") + b"\x0A\x00"))
            time.sleep(0.1)
            _ = self.jlink.rtt_write(
                0, list(bytearray("arg_flush", "utf-8") + b"\x0A\x00")
            )
            time.sleep(0.1)
            self.post_request(self.get_chipid())
            self.set_short_uid()
            time.sleep(0.5)
            i = 1

            while i < 20:
                if self.short_uid == self.get_uid():
                    ipsc_uid_print_win.add_log("uid 配置成功")
                    self.print_uid()
                    break
                else:
                    i += 1
                    self.set_short_uid()
                    time.sleep(0.5)
            if i > 20:
                ipsc_uid_print_win.add_log("uid 配置失败")
            _ = self.jlink.rtt_write(
                0, list(bytearray(f"arg_config", "utf-8") + b"\x0A\x00")
            )
            ipsc_uid_print_win.add_log("arg_config")
            time.sleep(1)
            _ = self.jlink.rtt_write(
                0, list(bytearray(f"arg_pin_iic_slave 0 8 0 7", "utf-8") + b"\x0A\x00")
            )
            ipsc_uid_print_win.add_log("arg_pin_iic_slave 0 8 0 7")
            _ = self.jlink.rtt_write(
                0, list(bytearray(f"arg_flush", "utf-8") + b"\x0A\x00")
            )
            ipsc_uid_print_win.add_log("arg_flush")

        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            ipsc_uid_print_win.add_log(f"{tb}:{e}")

    def connect_target(self, chip_name="nRF52840_xxAA"):
        try:
            self.jlink = pylink.JLink()
            self.jlink.open()
            if self.jlink.opened():
                self.jlink.set_tif(pylink.enums.JLinkInterfaces.SWD)
                self.jlink.connect(chip_name=chip_name, verbose=True)
                if self.jlink.connected():
                    ipsc_uid_print_win.add_log(f"连接成功")
                else:
                    ipsc_uid_print_win.add_log(f"连接失败")
            else:
                ipsc_uid_print_win.add_log(f"未检测到jlink")

        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            ipsc_uid_print_win.add_log(f"{tb}:{e}")

    def flash_firmware(self, addr=0x0000000):
        self.in_test = 0
        if ipsc_uid_print_win.var1.get():
            file = ipsc_uid_print_win.gateway_filepath_val.get()
        elif ipsc_uid_print_win.var2.get():
            file = ipsc_uid_print_win.anchor_filepath_val.get()
        elif ipsc_uid_print_win.var3.get():
            file = ipsc_uid_print_win.tag_filepath_val.get()
        else:
            file = ""
            ipsc_uid_print_win.add_log(f"未选择固件")
        self.firmware_version = file.split("/")[-1]
        ipsc_uid_print_win.add_log(run_jlink_command(ipsc_uid_print_win.p1_check.get()))
        self.connect_target()
        if self.jlink.target_connected() and file:
            ipsc_uid_print_win.add_log("连接成功")
            ipsc_uid_print_win.add_log(f"固件: {file}")
            try:
                self.jlink.flash_file(file, addr)
            except Exception as e:
                tb = traceback.extract_tb(e.__traceback__)
                ipsc_uid_print_win.add_log(f"{tb}:{e}")
                return False
            ipsc_uid_print_win.add_log("烧录成功")
            self.jlink.reset()
            self.jlink.restart()
            ipsc_uid_print_win.add_log("重启成功")
            time.sleep(1)
            self.start_rtt()

            return True
        else:
            ipsc_uid_print_win.add_log("连接失败")

    def start_rtt(self):
        if not self.jlink.rtt_get_status().IsRunning:
            self.jlink.rtt_start()
            time.sleep(1)

    def post_request(self, uid):
        data = ipsc_uid_print_win.version_batch

        data["longUid"] = uid
        ipsc_uid_print_win.add_log(data)
        response = requests.post(
            self.manufacture_device_postUrl,
            json=data,
            cert=cert,
            verify=ca_cert,
        )
        if response.status_code == 200:
            ipsc_uid_print_win.add_log("POST 请求成功！")
            ipsc_uid_print_win.add_log(f"响应内容：{response.json()}")
            self.short_uid = response.json()["data"]["shortUid"]
        else:
            ipsc_uid_print_win.add_log("POST 请求失败，状态码：", response.status_code)

    def set_short_uid(self):
        try:
            self.start_rtt()
            cmd = f"arg_uid {self.short_uid}"
            bytes = list(
                bytearray(
                    cmd,
                    "utf-8",
                )
                + b"\x0A\x00"
            )
            ipsc_uid_print_win.short_id_val.set(self.short_uid)
            if self.jlink.rtt_write(0, bytes):
                ipsc_uid_print_win.add_log(cmd)

        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            ipsc_uid_print_win.add_log(f"{tb}:{e}")

    def get_chipid(self):
        try:
            self.start_rtt()
            running = 1
            while running:

                bytes = list(bytearray("arg_list", "utf-8") + b"\x0A\x00")
                bytes_written = self.jlink.rtt_write(0, bytes)

                if bytes_written:
                    while 1:
                        terminal_bytes = self.jlink.rtt_read(0, 4096)
                        if terminal_bytes:
                            data = "".join(map(chr, terminal_bytes))
                            if "uid" in data:
                                match = re.findall(r"chip_id=([a-fA-F0-9]+)", data)
                                if match:
                                    uid = match[0]
                                    ipsc_uid_print_win.add_log(f"get  chip_id = { uid}")

                                    running = 0
                                    return uid
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            ipsc_uid_print_win.add_log(f"{tb}:{e}")

    def get_uid(self):
        try:
            self.start_rtt()
            running = 1
            while running:

                bytes = list(bytearray("arg_list", "utf-8") + b"\x0A\x00")
                bytes_written = self.jlink.rtt_write(0, bytes)

                if bytes_written:
                    while 1:
                        terminal_bytes = self.jlink.rtt_read(0, 2048)
                        if terminal_bytes:
                            data = "".join(map(chr, terminal_bytes))
                            if "uid" in data:
                                match = re.findall(r"uid=([a-fA-F0-9]+)", data)

                                if match:
                                    uid = match[0]
                                    ipsc_uid_print_win.add_log(f"get uid = { uid}")

                                    running = 0
                                    return uid
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            ipsc_uid_print_win.add_log(f"{tb}:{e}")

    def print_uid(self):
        try:
            if not self.jlink.target_connected():
                self.connect_target()
            if self.jlink.target_connected():
                if not self.short_uid:
                    self.short_uid = self.get_uid()

                ipsc_uid_print_win.print_res_val.set(f"{self.short_uid}")
                logo = ipsc_uid_print_win.logoval.get()
                p = ipsc_uid_print_win.pval.get()
                if ipsc_uid_print_win.var1.get():
                    print_zpl_label(uid=self.short_uid, hardware=1, logo=logo, p=p)
                elif ipsc_uid_print_win.var2.get():
                    print_zpl_label(uid=self.short_uid, hardware=2, logo=logo, p=p)
                elif ipsc_uid_print_win.var3.get():
                    print_zpl_label(uid=self.short_uid, hardware=3, logo=logo, p=p)
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            ipsc_uid_print_win.add_log(f"{tb}:{e}")

    def product_test_io(self):
        try:

            bytes = list(bytearray(f"product_test_io", "utf-8") + b"\x0A\x00")
            _ = self.jlink.rtt_write(0, bytes)
            ipsc_uid_print_win.add_log("product_test_io")
            running = 1
            while running:
                terminal_bytes = self.jlink.rtt_read(0, 1024)
                data = "".join(map(chr, terminal_bytes))
                if data:
                    if "product_test_io passed" in data:
                        running = 0
                        ipsc_uid_print_win.add_log("product_test_io passed")

                    if "product_test_io failed" in data:
                        running = 0
                        ipsc_uid_print_win.add_log("product_test_io failed")

        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            ipsc_uid_print_win.add_log(f"{tb}:{e}")

    def power_consumption_test(self):
        try:
            if not self.jlink.target_connected():
                self.connect_target()

            bytes = list(
                bytearray(
                    f"arg_config 0",
                    "utf-8",
                )
                + b"\x0A\x00"
            )
            _ = self.jlink.rtt_write(0, bytes)
            time.sleep(1)
            ipsc_uid_print_win.add_log("arg_config 0")
            bytes = list(
                bytearray(
                    f"arg_run_mode power",
                    "utf-8",
                )
                + b"\x0A\x00"
            )
            n = self.jlink.rtt_write(0, bytes)
            ipsc_uid_print_win.add_log(f"arg_run_mode power:send {n} bytes")

        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            ipsc_uid_print_win.add_log(f"{tb}:{e}")

    def product_test_master(self):
        try:

            if not self.jlink.target_connected():
                self.connect_target()

            slave_addr = ipsc_uid_print_win.slave_anchor
            test_time = ipsc_uid_print_win.test_time_val.get()
            cmd = f"product_test_master  5 {slave_addr} 10 {test_time*10}"
            ipsc_uid_print_win.add_log(cmd)
            bytes2 = list(
                bytearray(
                    cmd,
                    "utf-8",
                )
                + b"\x0A\x00"
            )

            bytes_written = self.jlink.rtt_write(0, bytes2)
            if bytes_written:
                self.t = threading.Thread(
                    target=self.logging_data,
                    args=(test_time,),
                    daemon=True,
                )
                self.t.start()

        except Exception as e:

            tb = traceback.extract_tb(e.__traceback__)
            ipsc_uid_print_win.add_log(f"{tb}:{e}")

    def logging_data(self, test_time):

        try:

            if ipsc_uid_print_win.var1.get():
                filename = f"logs/{datetime.now().strftime('%Y%m%d_%H%M%S')}-{self.short_uid}-{"gateway"}-{self.firmware_version}.log"

            elif ipsc_uid_print_win.var2.get():
                filename = f"logs/{datetime.now().strftime('%Y%m%d_%H%M%S')}-{self.short_uid}-{"anchor"}-{self.firmware_version}.log"
            elif ipsc_uid_print_win.var3.get():
                filename = f"logs/{datetime.now().strftime('%Y%m%d_%H%M%S')}-{self.short_uid}-{"tag"}-{self.firmware_version}.log"
            else:
                filename = f"logs/{datetime.now().strftime('%Y%m%d_%H%M%S')}-{self.short_uid}-{""}-{""}.log"

            duration = test_time + 1
            start_time = time.time()
            ipsc_uid_print_win.add_log("Recording...")
            running = 1
            with open(filename, "w", encoding="utf-8", buffering=1) as file:
                while running:
                    terminal_bytes = self.jlink.rtt_read(0, 4096)
                    data = "".join(map(chr, terminal_bytes))
                    if data:
                        file.write(data)
                        if "resp signal rx info: master_tx_cnt=200" in data:
                            running = 0
                    if time.time() - start_time > duration:
                        running = 0
            file.close()
            ipsc_uid_print_win.add_log("recorded end")
            ipsc_uid_print_win.test_res_val.set(filename)
            ipsc_uid_print_win.analysis_res_val.set(filename)
            self.cal_data_file()
        except Exception as e:

            tb = traceback.extract_tb(e.__traceback__)
            ipsc_uid_print_win.add_log(f"{tb}:{e}")
        finally:
            self.in_test = 0

    def test(self):

        if self.in_test == 1:
            ipsc_uid_print_win.add_log("勿重复点击...")
            return

        self.in_test = 1
        try:
            if not self.jlink.target_connected():
                self.connect_target()
                self.start_rtt()
            _ = self.jlink.rtt_write(
                0, list(bytearray(f"arg_config", "utf-8") + b"\x0A\x00")
            )
            ipsc_uid_print_win.add_log("arg_config")
            time.sleep(3)
            ipsc_uid_print_win.add_log("start test")
        except Exception as e:
            self.in_test = 0
            tb = traceback.extract_tb(e.__traceback__)
            ipsc_uid_print_win.add_log(f"{tb}:{e}")
            return
        if ipsc_uid_print_win.io_test_val.get():
            self.product_test_io()
        if ipsc_uid_print_win.product_test_master_val.get():
            self.product_test_master()

    def cal_data_file(self):
        filename = ipsc_uid_print_win.analysis_res_val.get()
        ipsc_uid_print_win.add_log(f"test_res_val:{filename}")
        if filename:
            try:
                res, wakeup_time = dl_data.cal(
                    filename, ipsc_uid_print_win.get_test_params(), ipsc_uid_print_win
                )
                if res != -1:
                    draw_wakeup_time(filename, wakeup_time)
                    draw_dis(filename)
                ipsc_uid_print_win.add_log(f"fialed= {res}")

                if res:
                    ipsc_uid_print_win.add_log(f"cal failed")
                    if res == -1:
                        ipsc_uid_print_win.add_log(f"no data")
                else:
                    ipsc_uid_print_win.add_log(f"cal pass")

            except Exception as e:
                tb = traceback.extract_tb(e.__traceback__)
                ipsc_uid_print_win.add_log(f"{tb}:{e}")

    def encrypt_firmware(self):
        try:
            if self.jlink.target_connected():
                self.start_rtt()
                bytes = list(bytearray("encrypt_firmware", "utf-8") + b"\x0A\x00")
                bytes_written = self.jlink.rtt_write(0, bytes)
                if bytes_written:
                    ipsc_uid_print_win.add_log("加密成功")
                    self.jlink.rtt_stop()
                    self.jlink.close()
                    ipsc_uid_print_win.add_log("jlink close")
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            ipsc_uid_print_win.add_log(f"{tb}:{e}")

    def finish(self):
        try:
            self.connect_target()
            if self.jlink.target_connected():
                self.start_rtt()
                bytes = list(bytearray("arg_config 0", "utf-8") + b"\x0A\x00")
                bytes_written = self.jlink.rtt_write(0, bytes)
                if bytes_written:
                    ipsc_uid_print_win.add_log("arg_config 0")
                    time.sleep(0.1)
                    bytes = list(
                        bytearray("arg_run_mode normal", "utf-8") + b"\x0A\x00"
                    )
                    bytes_written = self.jlink.rtt_write(0, bytes)
                    if bytes_written:
                        ipsc_uid_print_win.add_log("退出测试模式")
                        self.encrypt_firmware()
                        filename = ipsc_uid_print_win.analysis_res_val.get()
                        new_last_file = filename.replace(".log", "_finished.log")
                        if not os.path.exists(new_last_file):
                            os.rename(filename, new_last_file)
                        if os.path.exists(filename):
                            os.remove(filename)

                        # 检查前一个日志文件
                        self.check_previous_file()

                else:
                    ipsc_uid_print_win.add_log("退出测试模式失败")

            else:
                ipsc_uid_print_win.add_log("连接失败")
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            ipsc_uid_print_win.add_log(f"{tb}:{e}")
            # 检查上一个文件

    def check_previous_file(self):
        # 获取目录中的所有日志文件
        files = glob.glob(os.path.join("logs", "*.log"))
        # 如果没有日志文件，直接返回
        if not files:
            return

        # 按文件修改时间排序
        files.sort(key=os.path.getmtime)
        # 获取最新的日志文件
        latest_file = files[-1]
        # 获取前一个日志文件
        if len(files) > 1:
            previous_file = files[-2]
        else:
            # 如果没有前一个文件，返回
            return
        # 检查前一个文件是否已经添加了 "finished" 标志
        if "finished" not in os.path.basename(previous_file):
            # 弹出警告
            root = tk.Tk()
            root.withdraw()  # 隐藏主窗口
            messagebox.showwarning(
                "警告",
                "前一个日志文件没有添加 'finished' 标志！请确认测试人员是否遗漏了最后一步。",
            )
            root.destroy()

    def auto(self):
        try:
            if self.flash_firmware():  # 下载运行打印

                self.set_hardware_info()
                time.sleep(1)
                self.test()  # 进入配置模式，io测试， product_test_master
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            ipsc_uid_print_win.add_log(f"{tb}:{e}")


def print_zpl_label(
    printer_name="ZDesigner 110Xi4 600 dpi", uid="123456", hardware=0, logo=1, p=0
):

    if p:
        pval = "P"
    else:
        pval = ""

    lvar = ipsc_uid_print_win.Lvar.get() * 23.6
    hvar = ipsc_uid_print_win.Hvar.get() * 23.6
    match logo:
        case 1:
            match hardware:
                case 2:
                    dll = 27 * 23.6
                    zpl_data = f"""
                ^XA
                ^SZ2^JMA
                ^MCY^PMN
                ^PW1957
                ~JSN
                ^JZY
                ^LH0,0^LRN
                ~DGR:SSGFX000.GRF,2160,30,:Z64:eJx9lbFyGjEQhvcsg1wwVpokLpi7PpVLCuYOF+ntGbtN/AbBFRQElEmRdLyByZPYSmNK8gAZ+yYUlBZxYXmskbLSYYgxui2Yhe/+ZVe7twJgVsK7HxAwinTQClFmFWR5WKshk2FqSmjVGIiDlFjLM1VCRRKg9snyTbTT6Vh7P7Cd1ibacJEV05sj70FkrS6lhpnNtAZgjKkGtLs+7WFAW/V0HKDE05kN0gEWHKK8OC6+kUbCaS1qW7D9EucF5ejsvKQt6GPBhoPAU92gzbyW5bBs4ypIu6CC5rAckL0lbSwok5Fc/bZ6LsHDeE7bS1pH7S3+b6JI/lTlagZrqJ1jvYmKCnpSOSro6/eH2KSCZopMrR1ZY4eP6AytGQwVNik2so8jrbeujImN7sdy6eBB44uUGUg1nVibWW0Gj5jHJTo45ZF7zRINvR4d39wkN0p9vPeO1oOFlino9dmQpyk8SDIb8jiFrsLcI4EvIZVIaQL1HpzJaPYN4qZzMPecWU0UqJSdQ6rgMSe3GKTngmCJp6jFp1SWxNDswjwnEx9kLrH3jhrslMpGKTRUNEV64YLc5U67XzUauyzjuA5dCX9E9RqDtOFvvoXaBkEtRCq5aIJSZCbYuU94mlOk9YLK5LdPeCzoeRODOAdpjbiZIzkzXZ8wZxjEVS0YB9iOPBVUt2Eu6BhYE4PkZMwpNmrXLQ6n1S5POuSsqHrCnZZ6LUWtjKaCjiDptSMMMoEEteSL01JBlCRTwUaQFgnjYfshcNNcFVtSwtWvN/Fxz1XtnA9uirjTMk4e7OUEm2q1ssOZcWPipAInEscr+qkHdK4TK/GDSnT89OduWe0A+aoMm6rM5ndPjqOnA9S+gig6Oq5UDj+fHJwdHlcODrOTlp/tZ4sO9wv3Tlp833fapfXWnMYzqtacet/wFW2vObXs/63xfc3ZzgIbx1u1lNIksOm8kcsyGo0CG3ZBgzeKs+vgbeTstlT7qVQbvkGdvRWl2lKa8DLKSmm1DLo7qcQ23AcL+wfbpuq9:FCA9
                ^FO{lvar+36,hvar}
                ^XGR:SSGFX000.GRF,1,1^FS
                ^IDR:SSGFX000.GRF
                ^FO{lvar+330.4},{hvar+30} 
                ^BQN,2,8
                ^FDMM,AUID:{uid}^FS 
                ^FO{lvar+159},{hvar+150}^A@N,60,60,E:TIMESNER.FNT^FDU1{pval}^FS
                ^FO{lvar+49.623},{hvar+280}^A@N,45,43,E:TIMESNER.FNT^FDUID:{uid}^FS

                ^SZ2^JMA
                ^MCY^PMN
                ^PW1957
                ~JSN
                ^JZY
                ^LH0,0^LRN
                ~DGR:SSGFX000.GRF,2160,30,:Z64:eJx9lbFyGjEQhvcsg1wwVpokLpi7PpVLCuYOF+ntGbtN/AbBFRQElEmRdLyByZPYSmNK8gAZ+yYUlBZxYXmskbLSYYgxui2Yhe/+ZVe7twJgVsK7HxAwinTQClFmFWR5WKshk2FqSmjVGIiDlFjLM1VCRRKg9snyTbTT6Vh7P7Cd1ibacJEV05sj70FkrS6lhpnNtAZgjKkGtLs+7WFAW/V0HKDE05kN0gEWHKK8OC6+kUbCaS1qW7D9EucF5ejsvKQt6GPBhoPAU92gzbyW5bBs4ypIu6CC5rAckL0lbSwok5Fc/bZ6LsHDeE7bS1pH7S3+b6JI/lTlagZrqJ1jvYmKCnpSOSro6/eH2KSCZopMrR1ZY4eP6AytGQwVNik2so8jrbeujImN7sdy6eBB44uUGUg1nVibWW0Gj5jHJTo45ZF7zRINvR4d39wkN0p9vPeO1oOFlino9dmQpyk8SDIb8jiFrsLcI4EvIZVIaQL1HpzJaPYN4qZzMPecWU0UqJSdQ6rgMSe3GKTngmCJp6jFp1SWxNDswjwnEx9kLrH3jhrslMpGKTRUNEV64YLc5U67XzUauyzjuA5dCX9E9RqDtOFvvoXaBkEtRCq5aIJSZCbYuU94mlOk9YLK5LdPeCzoeRODOAdpjbiZIzkzXZ8wZxjEVS0YB9iOPBVUt2Eu6BhYE4PkZMwpNmrXLQ6n1S5POuSsqHrCnZZ6LUWtjKaCjiDptSMMMoEEteSL01JBlCRTwUaQFgnjYfshcNNcFVtSwtWvN/Fxz1XtnA9uirjTMk4e7OUEm2q1ssOZcWPipAInEscr+qkHdK4TK/GDSnT89OduWe0A+aoMm6rM5ndPjqOnA9S+gig6Oq5UDj+fHJwdHlcODrOTlp/tZ4sO9wv3Tlp833fapfXWnMYzqtacet/wFW2vObXs/63xfc3ZzgIbx1u1lNIksOm8kcsyGo0CG3ZBgzeKs+vgbeTstlT7qVQbvkGdvRWl2lKa8DLKSmm1DLo7qcQ23AcL+wfbpuq9:FCA9
                ^FO{lvar+36+dll*1,0}
                ^XGR:SSGFX000.GRF,1,1^FS
                ^IDR:SSGFX000.GRF
                ^FO{lvar+330.4+dll*1},{hvar+30} 
                ^BQN,2,8
                ^FDMM,AUID:{uid}^FS 
                ^FO{lvar+159+dll*1},{hvar+150}^A@N,60,60,E:TIMESNER.FNT^FDU1{pval}^FS
                ^FO{lvar+49.623+dll*1},{hvar+280}^A@N,45,43,E:TIMESNER.FNT^FDUID:{uid}^FS

                ^SZ2^JMA
                ^MCY^PMN
                ^PW1957
                ~JSN
                ^JZY
                ^LH0,0^LRN
                ~DGR:SSGFX000.GRF,2160,30,:Z64:eJx9lbFyGjEQhvcsg1wwVpokLpi7PpVLCuYOF+ntGbtN/AbBFRQElEmRdLyByZPYSmNK8gAZ+yYUlBZxYXmskbLSYYgxui2Yhe/+ZVe7twJgVsK7HxAwinTQClFmFWR5WKshk2FqSmjVGIiDlFjLM1VCRRKg9snyTbTT6Vh7P7Cd1ibacJEV05sj70FkrS6lhpnNtAZgjKkGtLs+7WFAW/V0HKDE05kN0gEWHKK8OC6+kUbCaS1qW7D9EucF5ejsvKQt6GPBhoPAU92gzbyW5bBs4ypIu6CC5rAckL0lbSwok5Fc/bZ6LsHDeE7bS1pH7S3+b6JI/lTlagZrqJ1jvYmKCnpSOSro6/eH2KSCZopMrR1ZY4eP6AytGQwVNik2so8jrbeujImN7sdy6eBB44uUGUg1nVibWW0Gj5jHJTo45ZF7zRINvR4d39wkN0p9vPeO1oOFlino9dmQpyk8SDIb8jiFrsLcI4EvIZVIaQL1HpzJaPYN4qZzMPecWU0UqJSdQ6rgMSe3GKTngmCJp6jFp1SWxNDswjwnEx9kLrH3jhrslMpGKTRUNEV64YLc5U67XzUauyzjuA5dCX9E9RqDtOFvvoXaBkEtRCq5aIJSZCbYuU94mlOk9YLK5LdPeCzoeRODOAdpjbiZIzkzXZ8wZxjEVS0YB9iOPBVUt2Eu6BhYE4PkZMwpNmrXLQ6n1S5POuSsqHrCnZZ6LUWtjKaCjiDptSMMMoEEteSL01JBlCRTwUaQFgnjYfshcNNcFVtSwtWvN/Fxz1XtnA9uirjTMk4e7OUEm2q1ssOZcWPipAInEscr+qkHdK4TK/GDSnT89OduWe0A+aoMm6rM5ndPjqOnA9S+gig6Oq5UDj+fHJwdHlcODrOTlp/tZ4sO9wv3Tlp833fapfXWnMYzqtacet/wFW2vObXs/63xfc3ZzgIbx1u1lNIksOm8kcsyGo0CG3ZBgzeKs+vgbeTstlT7qVQbvkGdvRWl2lKa8DLKSmm1DLo7qcQ23AcL+wfbpuq9:FCA9
                ^FO{lvar+36+dll*2,0}
                ^XGR:SSGFX000.GRF,1,1^FS
                ^IDR:SSGFX000.GRF
                ^FO{lvar+330.4+dll*2},{hvar+30} 
                ^BQN,2,8
                ^FDMM,AUID:{uid}^FS 
                ^FO{lvar+159+dll*2},{hvar+150}^A@N,60,60,E:TIMESNER.FNT^FDU1{pval}^FS
                ^FO{lvar+49.623+dll*2},{hvar+280}^A@N,45,43,E:TIMESNER.FNT^FDUID:{uid}^FS
                ^XZ
        """
                case 1:
                    dll = 27 * 23.6
                    zpl_data = f"""
                ^XA
                ^SZ2^JMA
                ^MCY^PMN
                ^PW1957
                ~JSN
                ^JZY
                ^LH0,0^LRN
                ~DGR:SSGFX000.GRF,2160,30,:Z64:eJx9lbFyGjEQhvcsg1wwVpokLpi7PpVLCuYOF+ntGbtN/AbBFRQElEmRdLyByZPYSmNK8gAZ+yYUlBZxYXmskbLSYYgxui2Yhe/+ZVe7twJgVsK7HxAwinTQClFmFWR5WKshk2FqSmjVGIiDlFjLM1VCRRKg9snyTbTT6Vh7P7Cd1ibacJEV05sj70FkrS6lhpnNtAZgjKkGtLs+7WFAW/V0HKDE05kN0gEWHKK8OC6+kUbCaS1qW7D9EucF5ejsvKQt6GPBhoPAU92gzbyW5bBs4ypIu6CC5rAckL0lbSwok5Fc/bZ6LsHDeE7bS1pH7S3+b6JI/lTlagZrqJ1jvYmKCnpSOSro6/eH2KSCZopMrR1ZY4eP6AytGQwVNik2so8jrbeujImN7sdy6eBB44uUGUg1nVibWW0Gj5jHJTo45ZF7zRINvR4d39wkN0p9vPeO1oOFlino9dmQpyk8SDIb8jiFrsLcI4EvIZVIaQL1HpzJaPYN4qZzMPecWU0UqJSdQ6rgMSe3GKTngmCJp6jFp1SWxNDswjwnEx9kLrH3jhrslMpGKTRUNEV64YLc5U67XzUauyzjuA5dCX9E9RqDtOFvvoXaBkEtRCq5aIJSZCbYuU94mlOk9YLK5LdPeCzoeRODOAdpjbiZIzkzXZ8wZxjEVS0YB9iOPBVUt2Eu6BhYE4PkZMwpNmrXLQ6n1S5POuSsqHrCnZZ6LUWtjKaCjiDptSMMMoEEteSL01JBlCRTwUaQFgnjYfshcNNcFVtSwtWvN/Fxz1XtnA9uirjTMk4e7OUEm2q1ssOZcWPipAInEscr+qkHdK4TK/GDSnT89OduWe0A+aoMm6rM5ndPjqOnA9S+gig6Oq5UDj+fHJwdHlcODrOTlp/tZ4sO9wv3Tlp833fapfXWnMYzqtacet/wFW2vObXs/63xfc3ZzgIbx1u1lNIksOm8kcsyGo0CG3ZBgzeKs+vgbeTstlT7qVQbvkGdvRWl2lKa8DLKSmm1DLo7qcQ23AcL+wfbpuq9:FCA9
                ^FO{lvar+36,hvar}
                ^XGR:SSGFX000.GRF,1,1^FS
                ^IDR:SSGFX000.GRF
                ^FO{lvar+330.4},{hvar+30} 
                ^BQN,2,8
                ^FDMM,AUID:{uid}^FS 
                ^FO{lvar+159},{hvar+150}^A@N,60,60,E:TIMESNER.FNT^FDG1{pval}^FS
                ^FO{lvar+49.623},{hvar+280}^A@N,45,43,E:TIMESNER.FNT^FDUID:{uid}^FS

                ^SZ2^JMA
                ^MCY^PMN
                ^PW1957
                ~JSN
                ^JZY
                ^LH0,0^LRN
                ~DGR:SSGFX000.GRF,2160,30,:Z64:eJx9lbFyGjEQhvcsg1wwVpokLpi7PpVLCuYOF+ntGbtN/AbBFRQElEmRdLyByZPYSmNK8gAZ+yYUlBZxYXmskbLSYYgxui2Yhe/+ZVe7twJgVsK7HxAwinTQClFmFWR5WKshk2FqSmjVGIiDlFjLM1VCRRKg9snyTbTT6Vh7P7Cd1ibacJEV05sj70FkrS6lhpnNtAZgjKkGtLs+7WFAW/V0HKDE05kN0gEWHKK8OC6+kUbCaS1qW7D9EucF5ejsvKQt6GPBhoPAU92gzbyW5bBs4ypIu6CC5rAckL0lbSwok5Fc/bZ6LsHDeE7bS1pH7S3+b6JI/lTlagZrqJ1jvYmKCnpSOSro6/eH2KSCZopMrR1ZY4eP6AytGQwVNik2so8jrbeujImN7sdy6eBB44uUGUg1nVibWW0Gj5jHJTo45ZF7zRINvR4d39wkN0p9vPeO1oOFlino9dmQpyk8SDIb8jiFrsLcI4EvIZVIaQL1HpzJaPYN4qZzMPecWU0UqJSdQ6rgMSe3GKTngmCJp6jFp1SWxNDswjwnEx9kLrH3jhrslMpGKTRUNEV64YLc5U67XzUauyzjuA5dCX9E9RqDtOFvvoXaBkEtRCq5aIJSZCbYuU94mlOk9YLK5LdPeCzoeRODOAdpjbiZIzkzXZ8wZxjEVS0YB9iOPBVUt2Eu6BhYE4PkZMwpNmrXLQ6n1S5POuSsqHrCnZZ6LUWtjKaCjiDptSMMMoEEteSL01JBlCRTwUaQFgnjYfshcNNcFVtSwtWvN/Fxz1XtnA9uirjTMk4e7OUEm2q1ssOZcWPipAInEscr+qkHdK4TK/GDSnT89OduWe0A+aoMm6rM5ndPjqOnA9S+gig6Oq5UDj+fHJwdHlcODrOTlp/tZ4sO9wv3Tlp833fapfXWnMYzqtacet/wFW2vObXs/63xfc3ZzgIbx1u1lNIksOm8kcsyGo0CG3ZBgzeKs+vgbeTstlT7qVQbvkGdvRWl2lKa8DLKSmm1DLo7qcQ23AcL+wfbpuq9:FCA9
                ^FO{lvar+36+dll*1,0}
                ^XGR:SSGFX000.GRF,1,1^FS
                ^IDR:SSGFX000.GRF
                ^FO{lvar+330.4+dll*1},{hvar+30} 
                ^BQN,2,8
                ^FDMM,AUID:{uid}^FS 
                ^FO{lvar+159+dll*1},{hvar+150}^A@N,60,60,E:TIMESNER.FNT^FDG1{pval}^FS
                ^FO{lvar+49.623+dll*1},{hvar+280}^A@N,45,43,E:TIMESNER.FNT^FDUID:{uid}^FS

                ^SZ2^JMA
                ^MCY^PMN
                ^PW1957
                ~JSN
                ^JZY
                ^LH0,0^LRN
                ~DGR:SSGFX000.GRF,2160,30,:Z64:eJx9lbFyGjEQhvcsg1wwVpokLpi7PpVLCuYOF+ntGbtN/AbBFRQElEmRdLyByZPYSmNK8gAZ+yYUlBZxYXmskbLSYYgxui2Yhe/+ZVe7twJgVsK7HxAwinTQClFmFWR5WKshk2FqSmjVGIiDlFjLM1VCRRKg9snyTbTT6Vh7P7Cd1ibacJEV05sj70FkrS6lhpnNtAZgjKkGtLs+7WFAW/V0HKDE05kN0gEWHKK8OC6+kUbCaS1qW7D9EucF5ejsvKQt6GPBhoPAU92gzbyW5bBs4ypIu6CC5rAckL0lbSwok5Fc/bZ6LsHDeE7bS1pH7S3+b6JI/lTlagZrqJ1jvYmKCnpSOSro6/eH2KSCZopMrR1ZY4eP6AytGQwVNik2so8jrbeujImN7sdy6eBB44uUGUg1nVibWW0Gj5jHJTo45ZF7zRINvR4d39wkN0p9vPeO1oOFlino9dmQpyk8SDIb8jiFrsLcI4EvIZVIaQL1HpzJaPYN4qZzMPecWU0UqJSdQ6rgMSe3GKTngmCJp6jFp1SWxNDswjwnEx9kLrH3jhrslMpGKTRUNEV64YLc5U67XzUauyzjuA5dCX9E9RqDtOFvvoXaBkEtRCq5aIJSZCbYuU94mlOk9YLK5LdPeCzoeRODOAdpjbiZIzkzXZ8wZxjEVS0YB9iOPBVUt2Eu6BhYE4PkZMwpNmrXLQ6n1S5POuSsqHrCnZZ6LUWtjKaCjiDptSMMMoEEteSL01JBlCRTwUaQFgnjYfshcNNcFVtSwtWvN/Fxz1XtnA9uirjTMk4e7OUEm2q1ssOZcWPipAInEscr+qkHdK4TK/GDSnT89OduWe0A+aoMm6rM5ndPjqOnA9S+gig6Oq5UDj+fHJwdHlcODrOTlp/tZ4sO9wv3Tlp833fapfXWnMYzqtacet/wFW2vObXs/63xfc3ZzgIbx1u1lNIksOm8kcsyGo0CG3ZBgzeKs+vgbeTstlT7qVQbvkGdvRWl2lKa8DLKSmm1DLo7qcQ23AcL+wfbpuq9:FCA9
                ^FO{lvar+36+dll*2,0}
                ^XGR:SSGFX000.GRF,1,1^FS
                ^IDR:SSGFX000.GRF
                ^FO{lvar+330.4+dll*2},{hvar+30} 
                ^BQN,2,8
                ^FDMM,AUID:{uid}^FS 
                ^FO{lvar+159+dll*2},{hvar+150}^A@N,60,60,E:TIMESNER.FNT^FDG1{pval}^FS
                ^FO{lvar+49.623+dll*2},{hvar+280}^A@N,45,43,E:TIMESNER.FNT^FDUID:{uid}^FS
                ^XZ
        """

                case 3:
                    dll = 14 * 23.6
                    zpl_data = f"""^XA
                ^SZ2^JMA
                ^MCY^PMN
                ^PW1694
                ~JSN
                ^JZY
                ^LH{lvar,hvar}^LRN
                ~DGR:SSGFX000.GRF,960,20,:Z64:eJxtkkFvEkEUx98wZLlQaBMPkECHo0eIB6EYt4f6ETya4qnXJRzUWMukHJp48QuYqicTD2jSgyQSd4xNelM/gKaT9sCNJcEohmWfb7c0gR3+h3+yv/3vezPvLXAXbkBMHOVBnDFUbTOnbWnkRnYMdT0McKiX2LMHONv9tb3ESgyDeL115roixnKA+EqZ7DzG0sS85baQhDZijFmUQ52A6gJLhLmRBc4C42ATE3D1eSlyBvZH94NgrxcYSHsaTuYqN2+mxD9UgoVH3LkX+Q5oe0K5znd0g8nMIz/woSH8tmp9OUfbb87Ig6YPJeHb8unX4+5W/+LT8fut7kUP1oUvoHlWsJyiqrxMOQWVg5wIsnI86GVGNV3vZZyirhL7zOHN23K6lJe3q1a5KMuQzgYJ0F41o+tqQF5TDiRTCEz9oToVuUe+QczKInAdODXdkkPnjq7TlXiU23fy6hF8o94taAB/gZLLgN4P5JCq/aUcS6Fkcv+0+WPv/s/fT8jp0p0wV5uOLz3sT8djD2mz3JVJqJwcHaXc4kmHnGZzieGEDg+fZ97djJyeHuJ8vYX5ckm3wgKh7ka+GdoGgqH8dW5Baytya4HJkn2TJXyTsccm45MVuZHJrn+SJW2vYI04+A9dst+V:15D5
                ^XGR:SSGFX000.GRF,1,1^FS
                ^IDR:SSGFX000.GRF
                ^FO{lvar+140+dll*0},{hvar+51.92} 
                ^BQN,2,5
                ^FDMM,AUID:{uid}^FS 
                ^FO{lvar+50+dll*0},{hvar+100}^A@N,38,38,E:TIMESNER.FNT^FDTag^FS
                ^FO{lvar+30+dll*0},{hvar+180}^A@N,25,20,E:TIMESNER.FNT^FDModel:PM12T^FS
                ^FO{lvar+30+dll*0},{hvar+210}^A@N,25,20,E:TIMESNER.FNT^FDUID:{uid}^FS

                ^SZ2^JMA
                ^MCY^PMN
                ^PW1694
                ~JSN
                ^JZY
                ^LH{lvar,hvar}^LRN
                ~DGR:SSGFX000.GRF,960,20,:Z64:eJxtkkFvEkEUx98wZLlQaBMPkECHo0eIB6EYt4f6ETya4qnXJRzUWMukHJp48QuYqicTD2jSgyQSd4xNelM/gKaT9sCNJcEohmWfb7c0gR3+h3+yv/3vezPvLXAXbkBMHOVBnDFUbTOnbWnkRnYMdT0McKiX2LMHONv9tb3ESgyDeL115roixnKA+EqZ7DzG0sS85baQhDZijFmUQ52A6gJLhLmRBc4C42ATE3D1eSlyBvZH94NgrxcYSHsaTuYqN2+mxD9UgoVH3LkX+Q5oe0K5znd0g8nMIz/woSH8tmp9OUfbb87Ig6YPJeHb8unX4+5W/+LT8fut7kUP1oUvoHlWsJyiqrxMOQWVg5wIsnI86GVGNV3vZZyirhL7zOHN23K6lJe3q1a5KMuQzgYJ0F41o+tqQF5TDiRTCEz9oToVuUe+QczKInAdODXdkkPnjq7TlXiU23fy6hF8o94taAB/gZLLgN4P5JCq/aUcS6Fkcv+0+WPv/s/fT8jp0p0wV5uOLz3sT8djD2mz3JVJqJwcHaXc4kmHnGZzieGEDg+fZ97djJyeHuJ8vYX5ckm3wgKh7ka+GdoGgqH8dW5Baytya4HJkn2TJXyTsccm45MVuZHJrn+SJW2vYI04+A9dst+V:15D5
                ^FO{lvar+30+dll*1},{hvar} 
                ^XGR:SSGFX000.GRF,1,1^FS
                ^IDR:SSGFX000.GRF
                ^FO{lvar+140+dll*1},{hvar+51.92} 
                ^BQN,2,5
                ^FDMM,AUID:{uid}^FS 
                ^FO{lvar+50+dll*1},{hvar+100}^A@N,38,38,E:TIMESNER.FNT^FDTag^FS
                ^FO{lvar+30+dll*1},{hvar+180}^A@N,25,20,E:TIMESNER.FNT^FDModel:PM12T^FS
                ^FO{lvar+30+dll*1},{hvar+210}^A@N,25,20,E:TIMESNER.FNT^FDUID:{uid}^FS

                ^SZ2^JMA
                ^MCY^PMN
                ^PW1694
                ~JSN
                ^JZY
                ^LH{lvar,hvar}^LRN
                ~DGR:SSGFX000.GRF,960,20,:Z64:eJxtkkFvEkEUx98wZLlQaBMPkECHo0eIB6EYt4f6ETya4qnXJRzUWMukHJp48QuYqicTD2jSgyQSd4xNelM/gKaT9sCNJcEohmWfb7c0gR3+h3+yv/3vezPvLXAXbkBMHOVBnDFUbTOnbWnkRnYMdT0McKiX2LMHONv9tb3ESgyDeL115roixnKA+EqZ7DzG0sS85baQhDZijFmUQ52A6gJLhLmRBc4C42ATE3D1eSlyBvZH94NgrxcYSHsaTuYqN2+mxD9UgoVH3LkX+Q5oe0K5znd0g8nMIz/woSH8tmp9OUfbb87Ig6YPJeHb8unX4+5W/+LT8fut7kUP1oUvoHlWsJyiqrxMOQWVg5wIsnI86GVGNV3vZZyirhL7zOHN23K6lJe3q1a5KMuQzgYJ0F41o+tqQF5TDiRTCEz9oToVuUe+QczKInAdODXdkkPnjq7TlXiU23fy6hF8o94taAB/gZLLgN4P5JCq/aUcS6Fkcv+0+WPv/s/fT8jp0p0wV5uOLz3sT8djD2mz3JVJqJwcHaXc4kmHnGZzieGEDg+fZ97djJyeHuJ8vYX5ckm3wgKh7ka+GdoGgqH8dW5Baytya4HJkn2TJXyTsccm45MVuZHJrn+SJW2vYI04+A9dst+V:15D5
                ^FO{lvar+30+dll*2},{hvar} 
                ^XGR:SSGFX000.GRF,1,1^FS
                ^IDR:SSGFX000.GRF
                ^FO{lvar+140+dll*2},{hvar+51.92} 
                ^BQN,2,5
                ^FDMM,AUID:{uid}^FS 
                ^FO{lvar+50+dll*2},{hvar+100}^A@N,38,38,E:TIMESNER.FNT^FDTag^FS
                ^FO{lvar+30+dll*2},{hvar+180}^A@N,25,20,E:TIMESNER.FNT^FDModel:PM12T^FS
                ^FO{lvar+30+dll*2},{hvar+210}^A@N,25,20,E:TIMESNER.FNT^FDUID:{uid}^FS

            
                ^XZ"""

                case _:
                    return
        case _:
            match hardware:
                case 2:
                    dll = 27 * 23.6
                    zpl_data = f"""
                ^XA
                ^SZ2^JMA
                ^MCY^PMN
                ^PW1957
                ~JSN
                ^JZY
                ^LH0,0^LRN
                ^FO{lvar+36,hvar}
                ^XGR:SSGFX000.GRF,1,1^FS
                ^IDR:SSGFX000.GRF
                ^FO{lvar+330.4},{hvar+30} 
                ^BQN,2,8
                ^FDMM,AUID:{uid}^FS 
                ^FO{lvar+159},{hvar+150}^A@N,60,60,E:TIMESNER.FNT^FDU1{pval}^FS
                ^FO{lvar+49.623},{hvar+280}^A@N,45,43,E:TIMESNER.FNT^FDUID:{uid}^FS

                ^SZ2^JMA
                ^MCY^PMN
                ^PW1957
                ~JSN
                ^JZY
                ^LH0,0^LRN
                ^FO{lvar+36+dll*1,0}
                ^XGR:SSGFX000.GRF,1,1^FS
                ^IDR:SSGFX000.GRF
                ^FO{lvar+330.4+dll*1},{hvar+30} 
                ^BQN,2,8
                ^FDMM,AUID:{uid}^FS 
                ^FO{lvar+159+dll*1},{hvar+150}^A@N,60,60,E:TIMESNER.FNT^FDU1{pval}^FS
                ^FO{lvar+49.623+dll*1},{hvar+280}^A@N,45,43,E:TIMESNER.FNT^FDUID:{uid}^FS

                ^SZ2^JMA
                ^MCY^PMN
                ^PW1957
                ~JSN
                ^JZY
                ^LH0,0^LRN
                ^FO{lvar+36+dll*2,0}
                ^XGR:SSGFX000.GRF,1,1^FS
                ^IDR:SSGFX000.GRF
                ^FO{lvar+330.4+dll*2},{hvar+30} 
                ^BQN,2,8
                ^FDMM,AUID:{uid}^FS 
                ^FO{lvar+159+dll*2},{hvar+150}^A@N,60,60,E:TIMESNER.FNT^FDU1{pval}^FS
                ^FO{lvar+49.623+dll*2},{hvar+280}^A@N,45,43,E:TIMESNER.FNT^FDUID:{uid}^FS
                ^XZ
        """
                case 1:
                    dll = 27 * 23.6
                    zpl_data = f"""
                ^XA
                ^SZ2^JMA
                ^MCY^PMN
                ^PW1957
                ~JSN
                ^JZY
                ^LH0,0^LRN
                ^FO{lvar+36,hvar}
                ^XGR:SSGFX000.GRF,1,1^FS
                ^IDR:SSGFX000.GRF
                ^FO{lvar+330.4},{hvar+30} 
                ^BQN,2,8
                ^FDMM,AUID:{uid}^FS 
                ^FO{lvar+159},{hvar+150}^A@N,60,60,E:TIMESNER.FNT^FDG1{pval}^FS
                ^FO{lvar+49.623},{hvar+280}^A@N,45,43,E:TIMESNER.FNT^FDUID:{uid}^FS

                ^SZ2^JMA
                ^MCY^PMN
                ^PW1957
                ~JSN
                ^JZY
                ^LH0,0^LRN
                ^FO{lvar+36+dll*1,0}
                ^XGR:SSGFX000.GRF,1,1^FS
                ^IDR:SSGFX000.GRF
                ^FO{lvar+330.4+dll*1},{hvar+30} 
                ^BQN,2,8
                ^FDMM,AUID:{uid}^FS 
                ^FO{lvar+159+dll*1},{hvar+150}^A@N,60,60,E:TIMESNER.FNT^FDG1{pval}^FS
                ^FO{lvar+49.623+dll*1},{hvar+280}^A@N,45,43,E:TIMESNER.FNT^FDUID:{uid}^FS

                ^SZ2^JMA
                ^MCY^PMN
                ^PW1957
                ~JSN
                ^JZY
                ^LH0,0^LRN
                ^FO{lvar+36+dll*2,0}
                ^XGR:SSGFX000.GRF,1,1^FS
                ^IDR:SSGFX000.GRF
                ^FO{lvar+330.4+dll*2},{hvar+30} 
                ^BQN,2,8
                ^FDMM,AUID:{uid}^FS 
                ^FO{lvar+159+dll*2},{hvar+150}^A@N,60,60,E:TIMESNER.FNT^FDG1{pval}^FS
                ^FO{lvar+49.623+dll*2},{hvar+280}^A@N,45,43,E:TIMESNER.FNT^FDUID:{uid}^FS
                ^XZ
        """

                case 3:
                    dll = 14 * 23.6
                    zpl_data = f"""^XA
                ^SZ2^JMA
                ^MCY^PMN
                ^PW1694
                ~JSN
                ^JZY
                ^FO{lvar+278+dll*0},{hvar+270}
                ^GE20,21,21^FS
                ^FO{lvar+30+dll*0},{hvar+9} 
                ^XGR:SSGFX000.GRF,1,1^FS
                ^IDR:SSGFX000.GRF
                ^FO{lvar+140+dll*0},{hvar+51.92} 
                ^BQN,2,5
                ^FDMM,AUID:{uid}^FS 
                ^FO{lvar+50+dll*0},{hvar+100}^A@N,38,38,E:TIMESNER.FNT^FDTag^FS
                ^FO{lvar+30+dll*0},{hvar+180}^A@N,25,20,E:TIMESNER.FNT^FDModel:PM12T^FS
                ^FO{lvar+30+dll*0},{hvar+210}^A@N,25,20,E:TIMESNER.FNT^FDUID:{uid}^FS

                ^SZ2^JMA
                ^MCY^PMN
                ^PW1694
                ~JSN
                ^JZY
                ^FO{lvar+278+dll*1},{hvar+270}
                ^GE20,21,21^FS
                ^FO{lvar+30+dll*1},{hvar+9} 
                ^XGR:SSGFX000.GRF,1,1^FS
                ^IDR:SSGFX000.GRF
                ^FO{lvar+140+dll*1},{hvar+51.92} 
                ^BQN,2,5
                ^FDMM,AUID:{uid}^FS 
                ^FO{lvar+50+dll*1},{hvar+100}^A@N,38,38,E:TIMESNER.FNT^FDTag^FS
                ^FO{lvar+30+dll*1},{hvar+180}^A@N,25,20,E:TIMESNER.FNT^FDModel:PM12T^FS
                ^FO{lvar+30+dll*1},{hvar+210}^A@N,25,20,E:TIMESNER.FNT^FDUID:{uid}^FS

                ^SZ2^JMA
                ^MCY^PMN
                ^PW1694
                ~JSN
                ^JZY
                ^FO{lvar+278+dll*2},{hvar+270}
                ^GE20,21,21^FS
                ^FO{lvar+30+dll*2},{hvar+9} 
                ^XGR:SSGFX000.GRF,1,1^FS
                ^IDR:SSGFX000.GRF
                ^FO{lvar+140+dll*2},{hvar+51.92} 
                ^BQN,2,5
                ^FDMM,AUID:{uid}^FS 
                ^FO{lvar+50+dll*2},{hvar+100}^A@N,38,38,E:TIMESNER.FNT^FDTag^FS
                ^FO{lvar+30+dll*2},{hvar+180}^A@N,25,20,E:TIMESNER.FNT^FDModel:PM12T^FS
                ^FO{lvar+30+dll*2},{hvar+210}^A@N,25,20,E:TIMESNER.FNT^FDUID:{uid}^FS

            
                ^XZ"""

                case _:
                    return
    try:
        # 获取打印机的句柄
        hPrinter = win32print.OpenPrinter(printer_name)
        ipsc_uid_print_win.add_log(f"Opened printer: {printer_name}")

        try:
            # 启动打印任务
            job_info = ("Print Job", None, "RAW")
            hJob = win32print.StartDocPrinter(hPrinter, 1, job_info)
            ipsc_uid_print_win.add_log("Started print job")

            try:
                # 开始打印页面
                win32print.StartPagePrinter(hPrinter)

                # 打印ZPL数据
                win32print.WritePrinter(hPrinter, zpl_data.encode("utf-8"))

                # 结束打印页面
                win32print.EndPagePrinter(hPrinter)

            except pywintypes.error as e:
                ipsc_uid_print_win.add_log(f"Error during printing: {e}")

            finally:
                # 结束打印任务
                if hJob:
                    try:
                        win32print.EndDocPrinter(hPrinter)
                        ipsc_uid_print_win.add_log("Ended print job")
                    except pywintypes.error as e:
                        ipsc_uid_print_win.add_log(f"Error ending print job: {e}")

        except pywintypes.error as e:
            ipsc_uid_print_win.add_log(f"Error starting print job: {e}")

        finally:
            # 关闭打印机句柄
            if hPrinter:
                win32print.ClosePrinter(hPrinter)
                ipsc_uid_print_win.add_log("Closed printer")

    except pywintypes.error as e:
        ipsc_uid_print_win.add_log(f"Failed to open printer: {e}")


jlink = jlink()

ipsc_uid_print_win.flash_btn.bind(
    "<Button-1>",
    lambda e: threading.Thread(target=jlink.flash_firmware, daemon=True).start(),
)
ipsc_uid_print_win.test_btn.bind(
    "<Button-1>",
    lambda e: threading.Thread(target=jlink.test, daemon=True).start(),
)
ipsc_uid_print_win.analysis_btn.bind(
    "<Button-1>",
    lambda e: threading.Thread(target=jlink.cal_data_file, daemon=True).start(),
)
ipsc_uid_print_win.print_uid_btn.bind(
    "<Button-1>",
    lambda e: threading.Thread(target=jlink.print_uid, daemon=True).start(),
)
ipsc_uid_print_win.auto_btn.bind(
    "<Button-1>", lambda e: threading.Thread(target=jlink.auto, daemon=True).start()
)
ipsc_uid_print_win.power_consumption_test_btn.bind(
    "<Button-1>",
    lambda e: threading.Thread(
        target=jlink.power_consumption_test, daemon=True
    ).start(),
)
ipsc_uid_print_win.test_end_btn.bind(
    "<Button-1>",
    lambda e: threading.Thread(target=jlink.finish, daemon=True).start(),
)
ipsc_uid_print_win.set_btn.bind(
    "<Button-1>",
    lambda e: threading.Thread(target=jlink.set_hardware_info, daemon=True).start(),
)

ipsc_uid_print_win.mainloop()

config_data["HVar"] = ipsc_uid_print_win.Hvar.get()
config_data["LVar"] = ipsc_uid_print_win.Lvar.get()
config_data["set_value"] = ipsc_uid_print_win.get_test_params()


config_data["logo"] = ipsc_uid_print_win.logoval.get()
with open("config.json", "w") as file:
    json.dump(config_data, file, indent=4)

try:
    jlink.jlink.close()

except Exception as e:
    print(e)
