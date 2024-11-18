import numpy as np
import re
import pandas as pd

pattern = {
    "dis": r"twr distance: master_tx_cnt=(\d+), dis=(-?\d+\.\d+)",
    "wakeup_time": r"wakeup took (\d+) us",
    "plr": r"packet loss rate: master_tx_cnt=(\d+), master_rx_cnt=(\d+), slave_tx_cnt=(\d+), slave_rx_cnt=(\d+)",
    "signal": r"(\w+) signal rx info:.*clock_offset_ppm=(-?\d+\.\d+),.* rx_rssi=(-?\d+\.\d+)",
    "rtc_clock_offset": r"mcu_clock_offset: master_tx_cnt=(\d+), master_tx_time=(\d+), master_rx_time=(\d+), slave_tx_time=(\d+), slave_rx_time=(\d+)",
}


def filter_outliers_and_calculate_std(data):
    # 用于判定异常值的最小范围，当箱线图范围小于该值时，使用该值
    min_dis_range = 0.2

    # 创建 DataFrame
    df = pd.DataFrame(data, columns=["Dis"])

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
    filtered_data = [x for x in data if x not in outliers.values.reshape(-1)]
    # # 计算标准差
    std_filtered = np.std(filtered_data)

    return [
        median_value,
        std_filtered,
        [num_outliers / total_points, num_outliers, total_points],
    ]


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
            if eval(match[0][0]) > 200:
                continue
            dis.append(eval(match[0][1]))

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
                last_rtc_clock_offset = [eval(i) for i in match[0][1:]]
            else:
                if eval(match[0][0]) < 5:
                    init_rtc_clock_offset = [eval(i) for i in match[0][1:]]
    if not dis:
        return -1, -1
    wakeup_time = np.array(wakeup_time)

    init_rx_rssi = np.array(init_rx_rssi)
    resp_rx_rssi = np.array(resp_rx_rssi)
    init_clock_offset_ppm = np.array(init_clock_offset_ppm)
    resp_clock_offset_ppm = np.array(resp_clock_offset_ppm)
    data = {
        "dis": filter_outliers_and_calculate_std(dis),
        "rssi": {
            "init": [np.mean(init_rx_rssi), np.std(init_rx_rssi)],
            "resp": [np.mean(resp_rx_rssi), np.std(resp_rx_rssi)],
        },
        "wakeup_time": [
            np.median(wakeup_time),
            np.min(wakeup_time),
            np.std(wakeup_time),
        ],
        "plr": {
            "master2slave": 1 - last_slave_master_cnt[3] / last_slave_master_cnt[0],
            "slave2master": 1 - last_slave_master_cnt[1] / last_slave_master_cnt[2],
        },
        "uwb_clock_offset_ppm": {
            "init": [
                np.mean(init_clock_offset_ppm),
                np.std(init_clock_offset_ppm),
            ],
            "resp": [
                np.mean(resp_clock_offset_ppm),
                np.std(resp_clock_offset_ppm),
            ],
        },
        "rtc_clock_offset_ppm": {
            "master2slave": (
                1
                - (last_rtc_clock_offset[0] - init_rtc_clock_offset[0])
                / (last_rtc_clock_offset[3] - init_rtc_clock_offset[3])
            )
            * 1000000,
            "slave2master": (
                1
                - (last_rtc_clock_offset[2] - init_rtc_clock_offset[2])
                / (last_rtc_clock_offset[1] - init_rtc_clock_offset[1])
            )
            * 1000000,
        },
    }
    failed = 0
    # [1] dis
    if abs(data["dis"][0] - set_data["dis"]["truth"]) < set_data["dis"]["err_abs_max"]:
        win.dis_truth_label.config(fg="black")
        win.dis_err_abs_max_label.config(fg="black")
    else:
        failed += 1
        win.dis_truth_label.config(fg="red")
        win.dis_err_abs_max_label.config(fg="red")

    win.test_params_res_val["dis"]["truth"].set(round(data["dis"][0], 3))
    win.test_params_res_val["dis"]["err_abs_max"].set(
        round(abs(data["dis"][0] - set_data["dis"]["truth"]), 3)
    )

    if data["dis"][1] < set_data["dis"]["std_max"]:
        win.dis_std_max_label.config(fg="black")
    else:
        failed += 1
        win.dis_std_max_label.config(fg="red")
    win.test_params_res_val["dis"]["std_max"].set(round(data["dis"][1], 3))

    if data["dis"][2][0] < set_data["dis"]["abnormal_rate_max"]:

        win.dis_abnormal_rate_max_label.config(fg="black")
    else:
        failed += 1
        win.dis_abnormal_rate_max_label.config(fg="red")
    win.test_params_res_val["dis"]["abnormal_rate_max"].set(
        f"{data['dis'][2][0]:.3f} : {data['dis'][2][1]}/{data['dis'][2][2]}"
    )
    # [2] rssi

    if data["rssi"]["init"][0] > set_data["rssi"]["master2slave"]["mean"]:
        win.master2slave_mean_label.config(fg="black")
    else:
        failed += 1
        win.master2slave_mean_label.config(fg="red")
    win.test_params_res_val["rssi"]["master2slave"]["mean"].set(
        round(data["rssi"]["init"][0], 3)
    )

    if data["rssi"]["init"][1] < set_data["rssi"]["master2slave"]["std_max"]:
        win.master2slave_std_label.config(fg="black")
    else:
        failed += 1
        win.master2slave_std_label.config(fg="red")
    win.test_params_res_val["rssi"]["master2slave"]["std_max"].set(
        round(data["rssi"]["init"][1], 3)
    )

    if data["rssi"]["resp"][0] > set_data["rssi"]["slave2master"]["mean"]:
        win.slave2master_mean_label.config(fg="black")
    else:
        failed += 1
        win.slave2master_mean_label.config(fg="red")
    win.test_params_res_val["rssi"]["slave2master"]["mean"].set(
        round(data["rssi"]["resp"][0], 3)
    )

    if data["rssi"]["resp"][1] < set_data["rssi"]["slave2master"]["std_max"]:
        win.slave2master_std_label.config(fg="black")
    else:
        failed += 1
        win.slave2master_std_label.config(fg="red")
    win.test_params_res_val["rssi"]["slave2master"]["std_max"].set(
        round(data["rssi"]["resp"][1], 3)
    )

    # [3] wakeup_time
    if data["wakeup_time"][0] < set_data["wakeup_time"]["max"]:
        win.wakeup_time_max_label.config(fg="black")
    else:
        failed += 1
        win.wakeup_time_max_label.config(fg="red")
    win.test_params_res_val["wakeup_time"]["max"].set(round(data["wakeup_time"][0], 3))

    if data["wakeup_time"][1] > set_data["wakeup_time"]["min"]:
        win.wakeup_time_min_label.config(fg="black")
    else:
        failed += 1
        win.wakeup_time_min_label.config(fg="red")
    win.test_params_res_val["wakeup_time"]["min"].set(round(data["wakeup_time"][1], 3))

    if data["wakeup_time"][2] < set_data["wakeup_time"]["std_max"]:
        win.wakeup_time_std_max_label.config(fg="black")
    else:
        failed += 1
        win.wakeup_time_std_max_label.config(fg="red")
    win.test_params_res_val["wakeup_time"]["std_max"].set(
        round(data["wakeup_time"][2], 3)
    )

    # [4] plr
    if data["plr"]["master2slave"] < set_data["plr"]["master2slave"]:
        win.master2slave_plr_label.config(fg="black")
    else:
        failed += 1
        win.master2slave_plr_label.config(fg="red")
    win.test_params_res_val["plr"]["master2slave"].set(
        round(data["plr"]["master2slave"], 3)
    )

    if data["plr"]["slave2master"] < set_data["plr"]["slave2master"]:
        win.slave2master_plr_label.config(fg="black")
    else:
        failed += 1
        win.slave2master_plr_label.config(fg="red")
    win.test_params_res_val["plr"]["slave2master"].set(
        round(data["plr"]["slave2master"], 3)
    )

    # [5] uwb_clock_offset_ppm
    if (
        abs(data["uwb_clock_offset_ppm"]["init"][0])
        < set_data["uwb_clock_offset_ppm"]["master2slave"]["abs_mean_max"]
    ):
        win.master2slave_clock_offset_ppm_abs_mean_label.config(fg="black")
    else:
        failed += 1
        win.master2slave_clock_offset_ppm_abs_mean_label.config(fg="red")
    win.test_params_res_val["uwb_clock_offset_ppm"]["master2slave"]["abs_mean_max"].set(
        round(abs(data["uwb_clock_offset_ppm"]["init"][0]), 3)
    )
    if (
        data["uwb_clock_offset_ppm"]["init"][1]
        < set_data["uwb_clock_offset_ppm"]["master2slave"]["std_max"]
    ):
        win.master2slave_clock_offset_ppm_std_max_label.config(fg="black")
    else:
        failed += 1
        win.master2slave_clock_offset_ppm_std_max_label.config(fg="red")
    win.test_params_res_val["uwb_clock_offset_ppm"]["master2slave"]["std_max"].set(
        round(data["uwb_clock_offset_ppm"]["init"][1], 3)
    )

    if (
        abs(data["uwb_clock_offset_ppm"]["resp"][0])
        < set_data["uwb_clock_offset_ppm"]["slave2master"]["abs_mean_max"]
    ):
        win.slave2master_clock_offset_ppm_abs_mean_label.config(fg="black")
    else:
        failed += 1
        win.slave2master_clock_offset_ppm_abs_mean_label.config(fg="red")
    win.test_params_res_val["uwb_clock_offset_ppm"]["slave2master"]["abs_mean_max"].set(
        round(data["uwb_clock_offset_ppm"]["resp"][0], 3)
    )
    if (
        data["uwb_clock_offset_ppm"]["resp"][1]
        < set_data["uwb_clock_offset_ppm"]["slave2master"]["std_max"]
    ):
        win.slave2master_clock_offset_ppm_std_max_label.config(fg="black")
    else:
        failed += 1
        win.slave2master_clock_offset_ppm_std_max_label.config(fg="red")
    win.test_params_res_val["uwb_clock_offset_ppm"]["slave2master"]["std_max"].set(
        round(data["uwb_clock_offset_ppm"]["resp"][1], 3)
    )
    #  [6] rtc_clock_offset
    if (
        abs(data["rtc_clock_offset_ppm"]["master2slave"])
        < set_data["rtc_clock_offset_ppm"]["master2slave_abs"]
    ):
        win.master2slave_rtc_clock_offset_abs_maxlabel.config(fg="black")
    else:
        failed += 1
        win.master2slave_rtc_clock_offset_abs_maxlabel.config(fg="red")
    win.test_params_res_val["rtc_clock_offset_ppm"]["master2slave_abs"].set(
        round(data["rtc_clock_offset_ppm"]["master2slave"], 3)
    )
    if (
        abs(data["rtc_clock_offset_ppm"]["slave2master"])
        < set_data["rtc_clock_offset_ppm"]["slave2master_abs"]
    ):
        win.slave2master_rtc_clock_offset_abs_maxlabel.config(fg="black")
    else:
        failed += 1
        win.slave2master_rtc_clock_offset_abs_maxlabel.config(fg="red")
    win.test_params_res_val["rtc_clock_offset_ppm"]["slave2master_abs"].set(
        round(data["rtc_clock_offset_ppm"]["slave2master"], 3)
    )
    if (
        data["rtc_clock_offset_ppm"]["slave2master"]
        + data["rtc_clock_offset_ppm"]["master2slave"]
        < set_data["rtc_clock_offset_ppm"]["add"]
    ):
        win.rtc_clock_offset_add.config(fg="black")
    else:
        failed += 1
        win.rtc_clock_offset_add.config(fg="red")
    win.test_params_res_val["rtc_clock_offset_ppm"]["add"].set(
        round(
            data["rtc_clock_offset_ppm"]["slave2master"]
            + data["rtc_clock_offset_ppm"]["master2slave"],
            3,
        )
    )
    return failed, wakeup_time
