import tkinter as tk
from tkinter import scrolledtext, filedialog
import os
from env import config_data
import datetime
_title = "ipsc_uid_print_tool"
_padx = 5
_pady = 5
_width = 10
_sticky = "we"


class Window(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(_title)
        self.init_val()
        self.set_first_Frame()
        self.set_second_Frame()
        self.set_third_Frame()

    def init_val(self):
        self.var1 = tk.IntVar()
        self.var2 = tk.IntVar()
        self.var3 = tk.IntVar()
        self.Lvar = tk.DoubleVar(value=config_data["LVar"])
        self.Hvar = tk.DoubleVar(value=config_data["HVar"])
        self.test_time_val = tk.IntVar(value=config_data["test_time_val"])
        self.gateway_filepath_val = tk.StringVar(
            value=config_data["gateway_firmware_path"]
        )
        self.anchor_filepath_val = tk.StringVar(
            value=config_data["anchor_firmware_path"]
        )
        self.tag_filepath_val = tk.StringVar(value=config_data["tag_firmware_path"])
        self.flash_res_val = tk.StringVar()
        self.analysis_res_val = tk.StringVar()
        self.test_res_val = tk.StringVar()
        self.print_res_val = tk.StringVar()
        self.auto_res_val = tk.StringVar()
        self.test_params_val={  "dis": [
            tk.DoubleVar(value=config_data["set_value"]["dis"][0]),
            tk.DoubleVar(value=config_data["set_value"]["dis"][1])
        ],
        "wakeup_time": [
            tk.DoubleVar(value=config_data["set_value"]["wakeup_time"][0]),
            tk.DoubleVar(value=config_data["set_value"]["wakeup_time"][1])
        ],
        "master2slave_plr": tk.DoubleVar(value=config_data["set_value"]["master2slave_plr"]),
        "slave2master_plr": tk.DoubleVar(value=config_data["set_value"]["slave2master_plr"]),
        "master2slave_rx_rssi": [
            tk.DoubleVar(value=config_data["set_value"]["master2slave_rx_rssi"][0]),
            tk.DoubleVar(value=config_data["set_value"]["master2slave_rx_rssi"][1])
        ],
        "slave2master_rx_rssi": [
            tk.DoubleVar(value=config_data["set_value"]["slave2master_rx_rssi"][0]),
            tk.DoubleVar(value=config_data["set_value"]["slave2master_rx_rssi"][1])
        ],
        "master2slave_uwb_clock_offset_ppm": [
            tk.DoubleVar(value=config_data["set_value"]["master2slave_uwb_clock_offset_ppm"][0]),
            tk.DoubleVar(value=config_data["set_value"]["master2slave_uwb_clock_offset_ppm"][1])
        ],
        "slave2master_uwb_clock_offset_ppm": [
            tk.DoubleVar(value=config_data["set_value"]["slave2master_uwb_clock_offset_ppm"][0]),
            tk.DoubleVar(value=config_data["set_value"]["slave2master_uwb_clock_offset_ppm"][1])
        ],
        "addtive_rtc_clock_offset_ppm":tk.DoubleVar(value=config_data["set_value"]["addtive_rtc_clock_offset_ppm"]),
        "abs_rtc_clock_offset_ppm": tk.DoubleVar(value=config_data["set_value"]["abs_rtc_clock_offset_ppm"])}

    def set_first_Frame(self):
        self.first_Frame = tk.Frame(self)

        for i in range(4):
            self.first_Frame.grid_rowconfigure(i, weight=1)
            self.first_Frame.grid_rowconfigure(i, weight=1)


        self.gateway_check = tk.Checkbutton(
            self.first_Frame,
            text="gateway",
            variable=self.var1,
            command=lambda: self.check(1),
        )
        self.gateway_check.grid(row=0, column=0, sticky=_sticky)
        self.gateway_firmware_btn = tk.Button(
            self.first_Frame,
            text="上传固件",
            command=lambda: self.upload_file(1),
        )
        self.gateway_firmware_btn.grid(row=0, column=2, sticky=_sticky)
        self.gateway_filepath = tk.Label(
            self.first_Frame, textvariable=self.gateway_filepath_val
        )
        self.gateway_filepath.grid(row=0, column=3, sticky=_sticky)

        self.anchor_check = tk.Checkbutton(
            self.first_Frame,
            text="anchor",
            variable=self.var2,
            command=lambda: self.check(2),
        )
        self.anchor_check.grid(row=1, column=0, sticky=_sticky, pady=_pady, padx=_padx)
        self.anchor_firmware_btn = tk.Button(
            self.first_Frame,
            text="上传固件",
            command=lambda: self.upload_file(2),
        )
        self.anchor_firmware_btn.grid(
            row=1, column=2, sticky=_sticky, pady=_pady, padx=_padx
        )
        self.anchor_filepath = tk.Label(
            self.first_Frame, textvariable=self.anchor_filepath_val
        )
        self.anchor_filepath.grid(
            row=1, column=3, sticky=_sticky, pady=_pady, padx=_padx
        )

        self.tag_check = tk.Checkbutton(
            self.first_Frame,
            text="tag",
            variable=self.var3,
            command=lambda: self.check(3),
        )

        self.tag_check.grid(row=2, column=0, sticky=_sticky, pady=_pady, padx=_padx)
        self.anchor_firmware_btn = tk.Button(
            self.first_Frame,
            text="上传固件",
            command=lambda: self.upload_file(3),
        )
        self.anchor_firmware_btn.grid(
            row=2, column=2, sticky=_sticky, pady=_pady, padx=_padx
        )
        self.tag_filepath = tk.Label(
            self.first_Frame, textvariable=self.tag_filepath_val
        )
        self.tag_filepath.grid(row=2, column=3, sticky=_sticky, pady=_pady, padx=_padx)
        self.first_Frame.pack(expand=True, fill="both")

    def set_second_Frame(self):
        self.second_Frame = tk.Frame(self)
        for i in range(6):
            self.second_Frame.grid_rowconfigure(i, weight=1)
            self.second_Frame.grid_rowconfigure(i, weight=1)
        self.flash_btn = tk.Button(self.second_Frame, text="烧录")
        self.flash_btn.grid(row=0, column=0, sticky=_sticky, pady=_pady, padx=_padx)
        tk.Label(self.second_Frame, textvariable=self.flash_res_val).grid(
            row=0, column=1, sticky=_sticky, pady=_pady, padx=_padx
        )

        self.test_btn = tk.Button(self.second_Frame, text="测试")
        self.test_btn.grid(row=1, column=0, sticky=_sticky, pady=_pady, padx=_padx)

        tk.Label(self.second_Frame, text="测试时间：").grid(
            row=1, column=2, sticky=_sticky, pady=_pady, padx=_padx
        )
        self.test_time = tk.Entry(self.second_Frame, textvariable=self.test_time_val,width=10)
        self.test_time.grid(row=1, column=3, sticky=_sticky, pady=_pady, padx=_padx)
        tk.Label(self.second_Frame, textvariable=self.test_res_val).grid(
            row=1, column=4, sticky=_sticky, pady=_pady, padx=_padx
        )

        self.analysis_btn = tk.Button(self.second_Frame, text="分析")
        self.analysis_btn.grid(row=2, column=0, sticky=_sticky, pady=_pady, padx=_padx)

        self.select_analysis_btn = tk.Button(
            self.second_Frame,
            text="选择文件",
            command=lambda: self.upload_file(4),
        )
        self.select_analysis_btn.grid(
            row=2, column=2, sticky=_sticky, pady=_pady, padx=_padx
        )
        tk.Label(self.second_Frame, textvariable=self.analysis_res_val).grid(
            row=2, column=3, sticky=_sticky, pady=_pady, padx=_padx
        )
      
        self.set_test_params()


        self.print_uid_btn = tk.Button(self.second_Frame, text="打印uid")
        self.print_uid_btn.grid(row=4, column=0, sticky=_sticky, pady=_pady, padx=_padx)
        tk.Label(self.second_Frame,text="L:").grid(row=4, column=1)
        tk.Entry(self.second_Frame,width=10,textvariable=self.Lvar).grid(row=4, column=2)
        tk.Label(self.second_Frame,text="R:").grid(row=4, column=3)
        tk.Entry(self.second_Frame,width=10,textvariable=self.Hvar).grid(row=4, column=4)
        tk.Label(self.second_Frame, textvariable=self.print_res_val).grid(
            row=4, column=5, sticky=_sticky, pady=_pady, padx=_padx
        )


        self.auto_btn = tk.Button(self.second_Frame, text="自动执行")
        self.auto_btn.grid(
            row=5, column=0, columnspan=1, sticky=_sticky, pady=_pady, padx=_padx
        )
        tk.Label(self.second_Frame, textvariable=self.auto_res_val).grid(
            row=5, column=1, sticky=_sticky, pady=_pady, padx=_padx
        )

        self.second_Frame.pack(expand=True, fill="both")

    def set_third_Frame(self):
        self.third_Frame = tk.Frame(self)
        self.log_text = scrolledtext.ScrolledText(
            self.third_Frame,
            wrap=tk.WORD,
            font=("Times New Roman", 10),
            width=200
        )
        self.log_text.pack(padx=5, pady=5)
        self.third_Frame.pack(expand=True, fill="both")

    def set_test_params(self):
        self.test_params = tk.Frame(self.second_Frame, bd=1, relief="sunken")

        self.dis_mean_label=tk.Label(self.test_params, text="dis_mean")
        self.dis_mean_label.grid(row=1, column=0)
        tk.Entry(self.test_params, width=10,textvariable=self.test_params_val["dis"][0]).grid(row=1, column=1)
        self.dis_std_label=tk.Label(self.test_params, text="dis_std")
        self.dis_std_label.grid(row=1, column=2)
        tk.Entry(self.test_params, width=10,textvariable=self.test_params_val["dis"][1]).grid(row=1, column=3)

        self.wakeup_time_mean_label=tk.Label(self.test_params, text="wakeup_time_mean")
        self.wakeup_time_mean_label.grid(row=1, column=4)
        tk.Entry(self.test_params, width=10,textvariable=self.test_params_val["wakeup_time"][0]).grid(row=1, column=5)
        self.wakeup_time_std_label=tk.Label(self.test_params, text="wakeup_time_std")
        self.wakeup_time_std_label.grid(row=1, column=6)
        tk.Entry(self.test_params, width=10,textvariable=self.test_params_val["wakeup_time"][1]).grid(row=1, column=7)

        self.master2slave_plr_label=tk.Label(self.test_params, text="master2slave_plr")
        self.master2slave_plr_label.grid(row=2, column=0)
        tk.Entry(self.test_params, width=10,textvariable=self.test_params_val["master2slave_plr"]).grid(row=2, column=1)

        self.slave2master_plr_label=tk.Label(self.test_params, text="slave2master_plr")
        self.slave2master_plr_label.grid(row=2, column=2)
        tk.Entry(self.test_params, width=10,textvariable=self.test_params_val["slave2master_plr"]).grid(row=2, column=3)

        self.master2slave_rx_rssi_mean_label=tk.Label(self.test_params, text="master2slave_rx_rssi_mean")
        self.master2slave_rx_rssi_mean_label.grid(
            row=2, column=4
        )
        tk.Entry(self.test_params, width=10,textvariable=self.test_params_val["master2slave_rx_rssi"][0]).grid(row=2, column=5)
        self.master2slave_rx_rssi_std_label=tk.Label(self.test_params, text="master2slave_rx_rssi_std")
        self.master2slave_rx_rssi_std_label.grid(
            row=2, column=6
        )
        tk.Entry(self.test_params, width=10,textvariable=self.test_params_val["master2slave_rx_rssi"][1]).grid(row=2, column=7)

        self.slave2master_rx_rssi_mean_label=tk.Label(self.test_params, text="slave2master_rx_rssi_mean")
        self.slave2master_rx_rssi_mean_label.grid(
            row=3, column=0
        )
        tk.Entry(self.test_params, width=10,textvariable=self.test_params_val["slave2master_rx_rssi"][0]).grid(row=3, column=1)
        self.slave2master_rx_rssi_std_label=tk.Label(self.test_params, text="slave2master_rx_rssi_std")
        self.slave2master_rx_rssi_std_label.grid(
            row=3, column=2
        )
        tk.Entry(self.test_params, width=10,textvariable=self.test_params_val["slave2master_rx_rssi"][1]).grid(row=3, column=3)


        self.master2slave_uwb_clock_offset_ppm_mean_label=tk.Label(self.test_params, text="master2slave_uwb_clock_offset_ppm_mean")
        self.master2slave_uwb_clock_offset_ppm_mean_label.grid(
            row=3, column=4
        )
        tk.Entry(self.test_params, width=10,textvariable=self.test_params_val["master2slave_uwb_clock_offset_ppm"][0]).grid(row=3, column=5)

        self.master2slave_uwb_clock_offset_ppm_std_label=tk.Label(self.test_params, text="master2slave_uwb_clock_offset_ppm_std")
        self.master2slave_uwb_clock_offset_ppm_std_label.grid(
            row=3, column=6
        )
        tk.Entry(self.test_params, width=10,textvariable=self.test_params_val["master2slave_uwb_clock_offset_ppm"][1]).grid(row=3, column=7)



        self.slave2master_uwb_clock_offset_ppm_mean_label=tk.Label(self.test_params, text="slave2master_uwb_clock_offset_ppm_mean")
        self.slave2master_uwb_clock_offset_ppm_mean_label.grid(
            row=4, column=0
        )
        tk.Entry(self.test_params, width=10,textvariable=self.test_params_val["slave2master_uwb_clock_offset_ppm"][0]).grid(row=4, column=1)

        self.slave2master_uwb_clock_offset_ppm_std_label=tk.Label(self.test_params, text="slave2master_uwb_clock_offset_ppm_std")
        self.slave2master_uwb_clock_offset_ppm_std_label.grid(
            row=4, column=2
        )
        tk.Entry(self.test_params, width=10,textvariable=self.test_params_val["slave2master_uwb_clock_offset_ppm"][1]).grid(row=4, column=3)


        self.addtive_rtc_clock_offset_ppm_label=tk.Label(self.test_params, text="addtive_rtc_clock_offset_ppm")
        self.addtive_rtc_clock_offset_ppm_label.grid(
            row=4, column=4
        )
        tk.Entry(self.test_params, width=10,textvariable=self.test_params_val["addtive_rtc_clock_offset_ppm"]).grid(row=4, column=5)

        self.abs_rtc_clock_offset_ppm_label=tk.Label(self.test_params, text="abs_rtc_clock_offset_ppm")
        self.abs_rtc_clock_offset_ppm_label.grid(
            row=4, column=6
        )
        tk.Entry(self.test_params, width=10,textvariable=self.test_params_val["abs_rtc_clock_offset_ppm"]).grid(row=4, column=7)

        self.test_params.grid(row=3, column=0, columnspan=10)

    def add_log(self, log_message):
        self.log_text.insert(tk.END, f"{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} : {log_message}\n")
        self.log_text.yview(tk.END)

    def upload_file(self, event):
        file_path = tk.filedialog.askopenfilename(initialdir=os.getcwd())
        match event:
            case 1:
                self.gateway_filepath_val.set(file_path)
                config_data["gateway_firmware_path"] = file_path
            case 2:
                self.anchor_filepath_val.set(file_path)
                config_data["anchor_firmware_path"] = file_path
            case 3:
                self.tag_filepath_val.set(file_path)
                config_data["tag_firmware_path"] = file_path

            case 4:
                self.analysis_res_val.set(file_path)
            case _:
                pass

    def check(self, event):
        match event:
            case 1:
                self.var2.set(0)
                self.var3.set(0)
            case 2:
                self.var3.set(0)
                self.var1.set(0)

            case 3:
                self.var2.set(0)
                self.var1.set(0)

            case _:
                pass

    def get_test_params(self):
        data= {
            "dis": [
                self.test_params_val["dis"][0].get(),
                self.test_params_val["dis"][1].get(),
            ],
            "wakeup_time": [
                self.test_params_val["wakeup_time"][0].get(),
                self.test_params_val["wakeup_time"][1].get(),
            ],
            "master2slave_plr": self.test_params_val["master2slave_plr"].get(),
            "slave2master_plr": self.test_params_val["slave2master_plr"].get(),
            "master2slave_rx_rssi": [
                self.test_params_val["master2slave_rx_rssi"][0].get(),
                self.test_params_val["master2slave_rx_rssi"][1].get(),
            ],
            "slave2master_rx_rssi": [
                self.test_params_val["slave2master_rx_rssi"][0].get(),
                self.test_params_val["slave2master_rx_rssi"][1].get(),
            ],
            "master2slave_uwb_clock_offset_ppm": [
                self.test_params_val["master2slave_uwb_clock_offset_ppm"][
                    0
                ].get(),
                self.test_params_val["master2slave_uwb_clock_offset_ppm"][
                    1
                ].get(),
            ],
            "slave2master_uwb_clock_offset_ppm": [
                self.test_params_val["slave2master_uwb_clock_offset_ppm"][
                    0
                ].get(),
                self.test_params_val["slave2master_uwb_clock_offset_ppm"][
                    1
                ].get(),
            ],
            "addtive_rtc_clock_offset_ppm": self.test_params_val[
                "addtive_rtc_clock_offset_ppm"
            ].get(),
            "abs_rtc_clock_offset_ppm": self.test_params_val[
                "abs_rtc_clock_offset_ppm"
            ].get()
    }
        return data
