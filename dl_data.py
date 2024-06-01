import numpy as np
import re


pattern = {
    "dis": r"twr distance: .*, dis=(-?\d+\.\d+)",
    "wakeup_time": r"wakeup took (\d+) us",
    "plr": r"packet loss rate: master_tx_cnt=(\d+), master_rx_cnt=(\d+), slave_tx_cnt=(\d+), slave_rx_cnt=(\d+)",
    "signal": r"(\w+) signal rx info:.*clock_offset_ppm=(-?\d+\.\d+),.* rx_rssi=(-?\d+\.\d+)",
    "rtc_clock_offset": r"mcu_clock_offset: .* master_tx_time=(\d+), master_rx_time=(\d+), slave_tx_time=(\d+), slave_rx_time=(\d+)",
}


def cal(filename, set_data, win):
    dis = []
    wakeup_time = []
    last_slave_master_cnt = []
    init_rx_rssi = []
    init_clock_offset_ppm = []
    resp_rx_rssi = []
    resp_clock_offset_ppm = []
    init_rtc_clock_offset = []
    last_rtc_clock_offset = []
    with open(filename, "r", encoding="utf-8") as file:
        lines = file.readlines()

    for line in lines:
        match = re.findall(
            pattern["dis"],
            line,
        )
        if match:
            dis.append(eval(match[0]))

        match = re.findall(
            pattern["wakeup_time"],
            line,
        )
        if match:
            wakeup_time.append(eval(match[0]))

        match = re.findall(
            pattern["plr"],
            line,
        )
        if match:
            last_slave_master_cnt = [eval(i) for i in match[0]]

        match = re.findall(
            pattern["signal"],
            line,
        )
        if match:
            data = match[0]
            if data[0] == "init":
                init_rx_rssi.append(eval(data[2]))
                init_clock_offset_ppm.append(eval(data[1]))
            else:
                resp_rx_rssi.append(eval(data[2]))
                resp_clock_offset_ppm.append(eval(data[1]))

        match = re.findall(
            pattern["rtc_clock_offset"],
            line,
        )
        if match:
            if init_rtc_clock_offset:
                last_rtc_clock_offset = [eval(i) for i in match[0]]
            else:
                init_rtc_clock_offset = [eval(i) for i in match[0]]

    dis = np.array(dis)
    wakeup_time = np.array(wakeup_time)
    init_rx_rssi = np.array(init_rx_rssi)
    resp_rx_rssi = np.array(resp_rx_rssi)
    init_clock_offset_ppm = np.array(init_clock_offset_ppm)
    resp_clock_offset_ppm = np.array(resp_clock_offset_ppm)
    data = {
        "dis": [np.mean(dis), np.std(dis)],
        "wakeup_time": [np.mean(wakeup_time), np.std(wakeup_time)],
        "master2slave_plr": 1 - last_slave_master_cnt[3] / last_slave_master_cnt[0],
        "slave2master_plr": 1 - last_slave_master_cnt[1] / last_slave_master_cnt[2],
        "master2slave_rx_rssi": [np.mean(init_rx_rssi), np.std(init_rx_rssi)],
        "slave2master_rx_rssi": [np.mean(resp_rx_rssi), np.std(resp_rx_rssi)],
        "master2slave_uwb_clock_offset_ppm": [
            np.mean(init_clock_offset_ppm),
            np.std(init_clock_offset_ppm),
        ],
        "slave2master_uwb_clock_offset_ppm": [
            np.mean(resp_clock_offset_ppm),
            np.std(resp_clock_offset_ppm),
        ],
        "master2slave_rtc_clock_offset_ppm": (
            1
            - (last_rtc_clock_offset[0] - init_rtc_clock_offset[0])
            / (last_rtc_clock_offset[3] - init_rtc_clock_offset[3])
        )
        * 1000000,
        "slave2master_rtc_clock_offset_ppm": (
            1
            - (last_rtc_clock_offset[2] - init_rtc_clock_offset[2])
            / (last_rtc_clock_offset[1] - init_rtc_clock_offset[1])
        )
        * 1000000,
    }
    res = {}
    print(win.dis_mean_label, type(win.dis_mean_label))
    if data["dis"] > set_data["dis"]:
        res["dis"] = data["dis"]
        if data["dis"][0] > set_data["dis"][0]:
            win.dis_mean_label.config(fg="red")
        if data["dis"][1] > set_data["dis"][1]:
            win.dis_std_label.config(fg="red")
    else:
        win.dis_mean_label.config(fg="black")
        win.dis_std_label.config(fg="black")

    if data["wakeup_time"] > set_data["wakeup_time"]:
        res["wakeup_time"] = data["wakeup_time"]
        if data["wakeup_time"][0] > set_data["wakeup_time"][0]:
            win.wakeup_time_mean_label.config(fg="red")
        if data["wakeup_time"][1] > set_data["wakeup_time"][1]:
            win.wakeup_time_std_label.config(fg="red")
    else:
        win.wakeup_time_mean_label.config(fg="black")
        win.wakeup_time_std_label.config(fg="black")

    if data["master2slave_plr"] > set_data["master2slave_plr"]:
        res["master2slave_plr"] = data["master2slave_plr"]
        win.master2slave_plr_label.config(fg="red")
    else:
        win.master2slave_plr_label.config(fg="black")

    if data["slave2master_plr"] > set_data["slave2master_plr"]:
        res["slave2master_plr"] = data["slave2master_plr"]
        win.slave2master_plr_label.config(fg="red")
    else:
        win.slave2master_plr_label.config(fg="black")

    if data["master2slave_rx_rssi"] > set_data["master2slave_rx_rssi"]:
        res["master2slave_rx_rssi"] = data["master2slave_rx_rssi"]
        if data["master2slave_rx_rssi"][0] > set_data["master2slave_rx_rssi"][0]:
            win.master2slave_rx_rssi_mean_label.config(fg="red")
        if data["master2slave_rx_rssi"][1] > set_data["master2slave_rx_rssi"][1]:
            win.master2slave_rx_rssi_std_label.config(fg="red")
    else:
        win.master2slave_rx_rssi_mean_label.config(fg="black")
        win.master2slave_rx_rssi_std_label.config(fg="black")

    if data["slave2master_rx_rssi"] > set_data["slave2master_rx_rssi"]:
        res["slave2master_rx_rssi"] = data["slave2master_rx_rssi"]
        if data["slave2master_rx_rssi"][0] > set_data["slave2master_rx_rssi"][0]:
            win.slave2master_rx_rssi_mean_label.config(fg="red")
        if data["slave2master_rx_rssi"][1] > set_data["slave2master_rx_rssi"][1]:
            win.slave2master_rx_rssi_std_label.config(fg="red")
    else:
        win.slave2master_rx_rssi_mean_label.config(fg="black")
        win.slave2master_rx_rssi_std_label.config(fg="black")

    if (
        data["master2slave_uwb_clock_offset_ppm"]
        > set_data["master2slave_uwb_clock_offset_ppm"]
    ):
        res["master2slave_uwb_clock_offset_ppm"] = data[
            "master2slave_uwb_clock_offset_ppm"
        ]
        if (
            data["master2slave_uwb_clock_offset_ppm"][0]
            > set_data["slave2master_rx_rssi"][0]
        ):
            win.master2slave_uwb_clock_offset_ppm_mean_label.config(fg="red")
        if (
            data["master2slave_uwb_clock_offset_ppm"][1]
            > set_data["slave2master_rx_rssi"][1]
        ):
            win.master2slave_uwb_clock_offset_ppm_std_label.config(fg="red")
    else:
        win.master2slave_uwb_clock_offset_ppm_mean_label.config(fg="black")
        win.master2slave_uwb_clock_offset_ppm_std_label.config(fg="black")

    if (
        abs(data["slave2master_rtc_clock_offset_ppm"])
        > set_data["abs_rtc_clock_offset_ppm"]
        or abs(data["master2slave_rtc_clock_offset_ppm"])
        > set_data["abs_rtc_clock_offset_ppm"]
    ):
        res["slave2master_rtc_clock_offset_ppm"] = data[
            "slave2master_rtc_clock_offset_ppm"
        ]
        res["master2slave_rtc_clock_offset_ppm"] = data[
            "master2slave_rtc_clock_offset_ppm"
        ]
        win.abs_rtc_clock_offset_ppm_label.config(fg="red")
    else:
        win.abs_rtc_clock_offset_ppm_label.config(fg="black")

    if (
        data["slave2master_rtc_clock_offset_ppm"]
        + data["master2slave_rtc_clock_offset_ppm"]
    ) > set_data["addtive_rtc_clock_offset_ppm"]:
        res["slave2master_rtc_clock_offset_ppm"] = data[
            "slave2master_rtc_clock_offset_ppm"
        ]
        res["master2slave_rtc_clock_offset_ppm"] = data[
            "master2slave_rtc_clock_offset_ppm"
        ]
        win.addtive_rtc_clock_offset_ppm_label.config(fg="red")
    else:
        win.addtive_rtc_clock_offset_ppm_label.config(fg="black")
    return data, res
