import tkinter as tk
from tkinter import font as tkFont
from tkinter import scrolledtext, filedialog, ttk
import os
from env import config_data, hardware_info_data
import datetime
import requests
from env import config_data, cert, ca_cert

_title = "ipsc_uid_print_tool"
_padx = 5
_pady = 5
_sticky = "we"


class Window(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(_title)
        self.init_val()
        self.set_first_Frame()
        self.set_third_Frame()
        self.set_second_Frame()

        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)
        self.bind("<Configure>", self.on_resize)

    def init_val(self):
        self.custom_font = tkFont.Font(family="Helvetica", size=8)
        version_batch = config_data["manufacture_device"]["version-batch"].split("-")
        self.version_batch = {
            "hardwareVersion": version_batch[0],
            "hardwareBatch": version_batch[1],
        }
        self.short_id_val = tk.StringVar()
        self.var1 = tk.IntVar()
        self.var2 = tk.IntVar()
        self.var3 = tk.IntVar()
        self.pval = tk.IntVar(value=config_data["P"])
        self.logoval = tk.IntVar(value=config_data["logo"])
        self.p1_check = tk.IntVar()
        self.io_test_val = tk.IntVar(value=config_data["io_test_val"])
        self.product_test_master_val = tk.IntVar(
            value=config_data["product_test_master"]["val"]
        )

        self.Lvar = tk.DoubleVar(value=config_data["LVar"])
        self.Hvar = tk.DoubleVar(value=config_data["HVar"])
        self.test_time_val = tk.IntVar(
            value=config_data["product_test_master"]["test_time"]
        )
        self.gateway_filepath_val = tk.StringVar(
            value=config_data["gateway_firmware_path"]
        )
        self.anchor_filepath_val = tk.StringVar(
            value=config_data["anchor_firmware_path"]
        )
        self.tag_filepath_val = tk.StringVar(value=config_data["tag_firmware_path"])
        self.analysis_res_val = tk.StringVar()
        self.test_res_val = tk.StringVar()
        self.print_res_val = tk.StringVar()
        self.auto_res_val = tk.StringVar()
        self.test_params_val = {
            "dis": {
                "truth": tk.DoubleVar(value=config_data["set_value"]["dis"]["truth"]),
                "err_abs_max": tk.DoubleVar(
                    value=config_data["set_value"]["dis"]["err_abs_max"]
                ),
                "std_max": tk.DoubleVar(
                    value=config_data["set_value"]["dis"]["std_max"]
                ),
                "abnormal_rate_max": tk.DoubleVar(
                    value=config_data["set_value"]["dis"]["abnormal_rate_max"]
                ),
            },
            "rssi": {
                "master2slave": {
                    "mean": tk.DoubleVar(
                        value=config_data["set_value"]["rssi"]["master2slave"]["mean"]
                    ),
                    "std_max": tk.DoubleVar(
                        value=config_data["set_value"]["rssi"]["master2slave"][
                            "std_max"
                        ]
                    ),
                },
                "slave2master": {
                    "mean": tk.DoubleVar(
                        value=config_data["set_value"]["rssi"]["slave2master"]["mean"]
                    ),
                    "std_max": tk.DoubleVar(
                        value=config_data["set_value"]["rssi"]["slave2master"][
                            "std_max"
                        ]
                    ),
                },
            },
            "wakeup_time": {
                "max": tk.DoubleVar(
                    value=config_data["set_value"]["wakeup_time"]["max"]
                ),
                "min": tk.DoubleVar(
                    value=config_data["set_value"]["wakeup_time"]["min"]
                ),
                "std_max": tk.DoubleVar(
                    value=config_data["set_value"]["wakeup_time"]["std_max"]
                ),
            },
            "plr": {
                "master2slave": tk.DoubleVar(
                    value=config_data["set_value"]["plr"]["master2slave"]
                ),
                "slave2master": tk.DoubleVar(
                    value=config_data["set_value"]["plr"]["slave2master"]
                ),
            },
            "uwb_clock_offset_ppm": {
                "master2slave": {
                    "abs_mean_max": tk.DoubleVar(
                        value=config_data["set_value"]["uwb_clock_offset_ppm"][
                            "master2slave"
                        ]["abs_mean_max"]
                    ),
                    "std_max": tk.DoubleVar(
                        value=config_data["set_value"]["uwb_clock_offset_ppm"][
                            "master2slave"
                        ]["std_max"]
                    ),
                },
                "slave2master": {
                    "abs_mean_max": tk.DoubleVar(
                        value=config_data["set_value"]["uwb_clock_offset_ppm"][
                            "slave2master"
                        ]["abs_mean_max"]
                    ),
                    "std_max": tk.DoubleVar(
                        value=config_data["set_value"]["uwb_clock_offset_ppm"][
                            "slave2master"
                        ]["std_max"]
                    ),
                },
            },
            "rtc_clock_offset_ppm": {
                "master2slave_abs": tk.DoubleVar(
                    value=config_data["set_value"]["rtc_clock_offset_ppm"][
                        "master2slave_abs"
                    ]
                ),
                "slave2master_abs": tk.DoubleVar(
                    value=config_data["set_value"]["rtc_clock_offset_ppm"][
                        "slave2master_abs"
                    ]
                ),
                "add": tk.DoubleVar(
                    value=config_data["set_value"]["rtc_clock_offset_ppm"]["add"]
                ),
            },
        }

        self.test_params_res_val = {
            "dis": {
                "truth": tk.DoubleVar(),
                "err_abs_max": tk.DoubleVar(),
                "std_max": tk.DoubleVar(),
                "abnormal_rate_max": tk.StringVar(),
            },
            "rssi": {
                "master2slave": {
                    "mean": tk.DoubleVar(),
                    "std_max": tk.DoubleVar(),
                },
                "slave2master": {
                    "mean": tk.DoubleVar(),
                    "std_max": tk.DoubleVar(),
                },
            },
            "wakeup_time": {
                "max": tk.DoubleVar(),
                "min": tk.DoubleVar(),
                "std_max": tk.DoubleVar(),
            },
            "plr": {
                "master2slave": tk.DoubleVar(),
                "slave2master": tk.DoubleVar(),
            },
            "uwb_clock_offset_ppm": {
                "master2slave": {
                    "abs_mean_max": tk.DoubleVar(),
                    "std_max": tk.DoubleVar(),
                },
                "slave2master": {
                    "abs_mean_max": tk.DoubleVar(),
                    "std_max": tk.DoubleVar(),
                },
            },
            "rtc_clock_offset_ppm": {
                "master2slave_abs": tk.DoubleVar(),
                "slave2master_abs": tk.DoubleVar(),
                "add": tk.DoubleVar(),
            },
        }

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
        self.gateway_check.grid(row=0, column=0)
        tk.Label(self.first_Frame, text="model").grid(
            row=0,
            column=1,
        )
        self.gateway_model_dropdown = ttk.Combobox(
            self.first_Frame,
            state="readonly",
            values=list(hardware_info_data["gateway"].keys()),
            width=10,
        )

        self.gateway_model_dropdown.bind(
            "<<ComboboxSelected>>", self.on_gateway_model_select
        )
        self.gateway_model_dropdown.grid(row=0, column=2)

        tk.Label(self.first_Frame, text="version").grid(
            row=0,
            column=3,
        )
        self.gateway_version_dropdown = ttk.Combobox(
            self.first_Frame,
            state="readonly",
            width=10,
        )

        self.gateway_version_dropdown.bind(
            "<<ComboboxSelected>>", self.on_gateway_version_select
        )
        self.gateway_version_dropdown.grid(row=0, column=4)
        tk.Label(self.first_Frame, text="batch").grid(
            row=0,
            column=5,
        )
        self.gateway_batch_dropdown = ttk.Combobox(
            self.first_Frame,
            state="readonly",
            width=10,
        )

        self.gateway_batch_dropdown.bind(
            "<<ComboboxSelected>>", self.on_gateway_batch_select
        )
        self.gateway_batch_dropdown.grid(row=0, column=6)
        self.gateway_firmware_btn = tk.Button(
            self.first_Frame,
            text="上传固件",
            command=lambda: self.upload_file(1),
        )
        self.gateway_firmware_btn.grid(row=0, column=7, sticky=_sticky)
        self.gateway_filepath = tk.Label(
            self.first_Frame,
            textvariable=self.gateway_filepath_val,
            font=self.custom_font,
            anchor="w",
        )
        self.gateway_filepath.grid(row=0, column=8, sticky=_sticky)

        self.anchor_check = tk.Checkbutton(
            self.first_Frame,
            text="anchor",
            variable=self.var2,
            command=lambda: self.check(2),
        )
        self.anchor_check.grid(
            row=1,
            column=0,
        )
        tk.Label(self.first_Frame, text="model").grid(
            row=1,
            column=1,
        )
        self.anchor_model_dropdown = ttk.Combobox(
            self.first_Frame,
            state="readonly",
            values=list(hardware_info_data["anchor"].keys()),
            width=10,
        )
        self.anchor_model_dropdown.bind(
            "<<ComboboxSelected>>", self.on_anchor_model_select
        )
        self.anchor_model_dropdown.grid(row=1, column=2)

        tk.Label(self.first_Frame, text="version").grid(
            row=1,
            column=3,
        )
        self.anchor_version_dropdown = ttk.Combobox(
            self.first_Frame,
            state="readonly",
            width=10,
        )

        self.anchor_version_dropdown.bind(
            "<<ComboboxSelected>>", self.on_anchor_version_select
        )
        self.anchor_version_dropdown.grid(row=1, column=4)

        tk.Label(self.first_Frame, text="batch").grid(
            row=1,
            column=5,
        )
        self.anchor_batch_dropdown = ttk.Combobox(
            self.first_Frame,
            state="readonly",
            width=10,
        )

        self.anchor_batch_dropdown.bind(
            "<<ComboboxSelected>>", self.on_anchor_batch_select
        )
        self.anchor_batch_dropdown.grid(row=1, column=6)
        self.anchor_firmware_btn = tk.Button(
            self.first_Frame,
            text="上传固件",
            command=lambda: self.upload_file(2),
        )
        self.anchor_firmware_btn.grid(
            row=1, column=7, sticky=_sticky, pady=_pady, padx=_padx
        )
        self.anchor_filepath = tk.Label(
            self.first_Frame,
            textvariable=self.anchor_filepath_val,
            font=self.custom_font,
            anchor="w",
        )
        self.anchor_filepath.grid(
            row=1, column=8, sticky=_sticky, pady=_pady, padx=_padx
        )

        self.tag_check = tk.Checkbutton(
            self.first_Frame,
            text="tag",
            variable=self.var3,
            command=lambda: self.check(3),
        )
        self.tag_check.grid(
            row=2,
            column=0,
        )
        tk.Label(self.first_Frame, text="model").grid(
            row=2,
            column=1,
        )
        self.tag_model_dropdown = ttk.Combobox(
            self.first_Frame,
            state="readonly",
            values=list(hardware_info_data["tag"].keys()),
            width=10,
        )
        self.tag_model_dropdown.bind("<<ComboboxSelected>>", self.on_tag_model_select)
        self.tag_model_dropdown.grid(row=2, column=2)

        tk.Label(self.first_Frame, text="version").grid(
            row=2,
            column=3,
        )
        self.tag_version_dropdown = ttk.Combobox(
            self.first_Frame,
            state="readonly",
            width=10,
        )

        self.tag_version_dropdown.bind(
            "<<ComboboxSelected>>", self.on_tag_version_select
        )
        self.tag_version_dropdown.grid(row=2, column=4)

        tk.Label(self.first_Frame, text="batch").grid(
            row=2,
            column=5,
        )
        self.tag_batch_dropdown = ttk.Combobox(
            self.first_Frame,
            state="readonly",
            width=10,
        )
        self.tag_batch_dropdown.bind("<<ComboboxSelected>>", self.on_tag_batch_select)
        self.tag_batch_dropdown.grid(row=2, column=6)
        self.tag_firmware_btn = tk.Button(
            self.first_Frame,
            text="上传固件",
            command=lambda: self.upload_file(3),
        )
        self.tag_firmware_btn.grid(
            row=2, column=7, sticky=_sticky, pady=_pady, padx=_padx
        )

        self.tag_filepath = tk.Label(
            self.first_Frame,
            textvariable=self.tag_filepath_val,
            font=self.custom_font,
            anchor="w",
        )
        self.tag_filepath.grid(row=2, column=8, sticky=_sticky, pady=_pady, padx=_padx)

        options = config_data["slave_addr"]
        tk.Label(self.first_Frame, text="slave:").grid(row=3, column=0)

        self.slave_dropdown = ttk.Combobox(
            self.first_Frame,
            state="readonly",
            values=options,
            width=10,
        )
        self.slave_dropdown.set(config_data["default_slave_addr"])
        self.slave_anchor = self.slave_dropdown.get()
        self.slave_dropdown.bind("<<ComboboxSelected>>", self.on_slave_select)
        self.slave_dropdown.grid(row=3, column=1)
        self.first_Frame.grid(row=0, column=0)
        self.set_default_hardware_info()

    def on_manufacture_batch_select(self, e):
        data = self.manufacture_batch_dropdown.get().split("-")
        self.version_batch["hardwareVersion"] = eval(data[0])
        self.version_batch["hardwareBatch"] = eval(data[1])
        config_data["manufacture_device"][
            "version-batch"
        ] = self.manufacture_batch_dropdown.get()

    def get_manufacture_batch(self):
        data = {"hardwareVersion": 0}
        response = requests.get(
            config_data["manufacture_device"]["batch_url"],
            json=data,
            cert=cert,
            verify=ca_cert,
        )
        option = []
        if response.status_code == 200:
            self.add_log("GET 请求成功！")
            self.add_log(f"响应内容：, {response.json()}")

            for data in response.json()["data"]["records"]:
                option.append(f"{data['hardwareVersion']}-{data['hardwareBatch']}")

        else:
            self.add_log("GET 请求失败，状态码：", response.status_code)
        return option

    def set_default_hardware_info(self):
        if (
            config_data["manufacture_device"]["gateway"]["model"]
            in hardware_info_data["gateway"].keys()
        ):
            self.gateway_model_dropdown.set(
                config_data["manufacture_device"]["gateway"]["model"]
            )
            self.gateway_version_dropdown.set(
                config_data["manufacture_device"]["gateway"]["version"]
            )
            self.gateway_batch_dropdown.set(
                config_data["manufacture_device"]["gateway"]["batch"]
            )
        if (
            config_data["manufacture_device"]["anchor"]["model"]
            in hardware_info_data["anchor"].keys()
        ):
            self.anchor_model_dropdown.set(
                config_data["manufacture_device"]["anchor"]["model"]
            )
            self.anchor_version_dropdown.set(
                config_data["manufacture_device"]["anchor"]["version"]
            )
            self.anchor_batch_dropdown.set(
                config_data["manufacture_device"]["anchor"]["batch"]
            )
        if (
            config_data["manufacture_device"]["tag"]["model"]
            in hardware_info_data["tag"].keys()
        ):
            self.tag_model_dropdown.set(
                config_data["manufacture_device"]["tag"]["model"]
            )
            self.tag_version_dropdown.set(
                config_data["manufacture_device"]["tag"]["version"]
            )
            self.tag_batch_dropdown.set(
                config_data["manufacture_device"]["tag"]["batch"]
            )

    def on_gateway_model_select(self, e):
        gateway_model_dropdown = self.gateway_model_dropdown.get()
        config_data["manufacture_device"]["gateway"]["model"] = gateway_model_dropdown
        self.gateway_version_dropdown.config(
            values=list(
                hardware_info_data["gateway"][self.gateway_model_dropdown.get()]
            )
        )

    def on_gateway_version_select(self, e):
        gateway_version_dropdown = self.gateway_version_dropdown.get()
        config_data["manufacture_device"]["gateway"][
            "version"
        ] = gateway_version_dropdown
        self.gateway_batch_dropdown.config(
            values=list(
                hardware_info_data["gateway"][self.gateway_model_dropdown.get()][
                    self.gateway_version_dropdown.get()
                ]
            )
        )

    def on_gateway_batch_select(self, e):
        gateway_batch_dropdown = self.gateway_batch_dropdown.get()
        config_data["manufacture_device"]["gateway"]["batch"] = gateway_batch_dropdown

    def on_anchor_model_select(self, e):
        anchor_model_dropdown = self.anchor_model_dropdown.get()
        config_data["manufacture_device"]["anchor"]["model"] = anchor_model_dropdown
        self.anchor_version_dropdown.config(
            values=list(hardware_info_data["anchor"][anchor_model_dropdown])
        )

    def on_anchor_version_select(self, e):
        anchor_version_dropdown = self.anchor_version_dropdown.get()
        config_data["manufacture_device"]["anchor"]["version"] = anchor_version_dropdown
        self.anchor_batch_dropdown.config(
            values=list(
                hardware_info_data["anchor"][self.anchor_model_dropdown.get()][
                    anchor_version_dropdown
                ]
            )
        )

    def on_anchor_batch_select(self, e):
        anchor_batch_dropdown = self.anchor_batch_dropdown.get()
        config_data["manufacture_device"]["anchor"]["batch"] = anchor_batch_dropdown

    def on_tag_model_select(self, e):
        tag_model_dropdown = self.tag_model_dropdown.get()
        config_data["manufacture_device"]["tag"]["model"] = tag_model_dropdown
        self.tag_version_dropdown.config(
            values=list(hardware_info_data["tag"][tag_model_dropdown])
        )

    def on_tag_version_select(self, e):
        tag_version_dropdown = self.tag_version_dropdown.get()
        config_data["manufacture_device"]["tag"]["version"] = tag_version_dropdown
        self.tag_batch_dropdown.config(
            values=list(
                hardware_info_data["tag"][self.tag_model_dropdown.get()][
                    tag_version_dropdown
                ]
            )
        )

    def on_tag_batch_select(self, e):
        tag_batch_dropdown = self.tag_batch_dropdown.get()
        config_data["manufacture_device"]["tag"]["batch"] = tag_batch_dropdown

    def on_slave_select(self, e):
        self.slave_anchor = self.slave_dropdown.get()
        config_data["default_slave_addr"] = self.slave_dropdown.get()

    def set_second_Frame(self):
        self.second_Frame = tk.Frame(self)
        for i in range(2):
            self.second_Frame.grid_rowconfigure(i, weight=1)
        for i in range(4, 6):
            self.second_Frame.grid_rowconfigure(i, weight=1)
        self.second_Frame.grid_rowconfigure(3, weight=3)
        self.flash_btn = tk.Button(
            self.second_Frame, font=self.custom_font, text="烧录"
        )
        self.flash_btn.grid(row=0, column=0, sticky=_sticky, pady=_pady, padx=_padx)
        self.p1_flash_check = tk.Checkbutton(
            self.second_Frame,
            font=self.custom_font,
            text="P1芯片",
            variable=self.p1_check,
        )
        self.p1_flash_check.grid(
            row=0, column=1, sticky=_sticky, pady=_pady, padx=_padx
        )
        self.set_btn = tk.Button(self.second_Frame, font=self.custom_font, text="配置")
        self.set_btn.grid(row=1, column=0, sticky=_sticky, pady=_pady, padx=_padx)
        tk.Label(self.second_Frame, text="硬件版本-批次").grid(row=1, column=1)
        self.manufacture_batch_dropdown = ttk.Combobox(
            self.second_Frame, state="readonly", values=self.get_manufacture_batch()
        )
        self.manufacture_batch_dropdown.set(
            config_data["manufacture_device"]["version-batch"]
        )
        self.manufacture_batch_dropdown.bind(
            "<<ComboboxSelected>>", self.on_manufacture_batch_select
        )
        self.manufacture_batch_dropdown.grid(row=1, column=2)
        self.test_btn = tk.Button(self.second_Frame, font=self.custom_font, text="测试")
        self.test_btn.grid(row=2, column=0, sticky=_sticky, pady=_pady, padx=_padx)

        self.io_test_check = tk.Checkbutton(
            self.second_Frame,
            text="product_test_io",
            variable=self.io_test_val,
            command=lambda: self.check(4),
        )
        self.io_test_check.grid(row=2, column=1, sticky=_sticky, pady=_pady, padx=_padx)

        self.product_test_master_check = tk.Checkbutton(
            self.second_Frame,
            text="product_test_master",
            variable=self.product_test_master_val,
            command=lambda: self.check(6),
        )
        self.product_test_master_check.grid(
            row=2, column=2, sticky=_sticky, pady=_pady, padx=_padx
        )
        tk.Label(
            self.second_Frame, text="测试时间：", font=self.custom_font, anchor="w"
        ).grid(row=2, column=3, sticky=_sticky, pady=_pady, padx=_padx)
        self.test_time = tk.Entry(
            self.second_Frame, textvariable=self.test_time_val, width=10
        )
        self.test_time.grid(row=2, column=4, sticky=_sticky, pady=_pady, padx=_padx)
        tk.Label(
            self.second_Frame,
            textvariable=self.test_res_val,
            font=self.custom_font,
            anchor="w",
        ).grid(row=2, column=5, sticky=_sticky, pady=_pady, padx=_padx)

        self.power_consumption_test_btn = tk.Button(
            self.second_Frame,
            text="功耗测试",
        )
        self.power_consumption_test_btn.grid(
            row=2, column=6, sticky=_sticky, pady=_pady, padx=_padx
        )

        self.test_end_btn = tk.Button(
            self.second_Frame,
            text="完成",
        )
        self.test_end_btn.grid(row=2, column=7, sticky=_sticky, pady=_pady, padx=_padx)
        self.analysis_btn = tk.Button(
            self.second_Frame, font=self.custom_font, text="分析"
        )
        self.analysis_btn.grid(row=3, column=0, sticky=_sticky, pady=_pady, padx=_padx)

        self.select_analysis_btn = tk.Button(
            self.second_Frame,
            text="选择文件",
            command=lambda: self.upload_file(4),
        )
        self.select_analysis_btn.grid(
            row=3, column=2, sticky=_sticky, pady=_pady, padx=_padx
        )
        tk.Label(
            self.second_Frame,
            textvariable=self.analysis_res_val,
            font=self.custom_font,
            anchor="w",
        ).grid(row=3, column=3, columnspan=3, sticky=_sticky, pady=_pady, padx=_padx)

        self.set_test_params()

        self.print_uid_btn = tk.Button(
            self.second_Frame, font=self.custom_font, text="打印uid"
        )
        self.print_uid_btn.grid(row=6, column=0, sticky=_sticky, pady=_pady, padx=_padx)
        self.Pcheck = tk.Checkbutton(
            self.second_Frame,
            text="P",
            variable=self.pval,
            command=lambda: self.check(7),
        )
        self.Pcheck.grid(row=6, column=1)
        self.logocheck = tk.Checkbutton(
            self.second_Frame,
            text="logo",
            variable=self.logoval,
            command=lambda: self.check(5),
        )
        self.logocheck.grid(row=6, column=2)
        tk.Label(self.second_Frame, text="L:", font=self.custom_font, anchor="w").grid(
            row=6, column=3
        )
        tk.Entry(self.second_Frame, width=10, textvariable=self.Lvar).grid(
            row=6, column=4
        )
        tk.Label(self.second_Frame, text="H:", font=self.custom_font, anchor="w").grid(
            row=6, column=5
        )
        tk.Entry(self.second_Frame, width=10, textvariable=self.Hvar).grid(
            row=6, column=6
        )

        tk.Label(
            self.second_Frame,
            textvariable=self.print_res_val,
            font=self.custom_font,
            anchor="w",
        ).grid(row=6, column=7, sticky=_sticky, pady=_pady, padx=_padx)

        self.auto_btn = tk.Button(
            self.second_Frame, font=self.custom_font, text="自动执行"
        )
        self.auto_btn.grid(row=6, column=0, sticky=_sticky, pady=_pady, padx=_padx)
        tk.Label(
            self.second_Frame,
            textvariable=self.auto_res_val,
            font=self.custom_font,
            anchor="w",
        ).grid(row=7, column=1, sticky=_sticky, pady=_pady, padx=_padx)

        tk.Label(
            self.second_Frame,
            text="short_id:",
            anchor="w",
        ).grid(row=8, column=0, sticky=_sticky, pady=_pady, padx=_padx)
        tk.Entry(self.second_Frame, textvariable=self.short_id_val, width=30).grid(
            row=8, column=1, sticky=_sticky, pady=_pady, padx=_padx
        )
        self.second_Frame.grid(row=1, column=0)

    def set_third_Frame(self):
        self.third_Frame = tk.Frame(self)
        self.log_text = scrolledtext.ScrolledText(
            self.third_Frame,
            wrap=tk.WORD,
            font=("Times New Roman", 10),
            width=100,
            height=10,
        )
        self.log_text.pack(padx=5, pady=5)
        self.third_Frame.grid(row=3, column=0)

    def set_test_params(self):
        self.canvas = tk.Canvas(self.second_Frame, height=150)
        self.second_Frame.grid_columnconfigure(5, weight=10)
        self.canvas.grid(row=4, column=0, columnspan=10, sticky="nsew")

        self.y_scrollbar = tk.Scrollbar(
            self.second_Frame, orient="vertical", command=self.canvas.yview
        )
        self.y_scrollbar.grid(row=4, column=10, sticky="ns")

        self.x_scrollbar = tk.Scrollbar(
            self.second_Frame, orient="horizontal", command=self.canvas.xview
        )
        self.x_scrollbar.grid(row=5, column=0, columnspan=10, sticky="ew")

        self.canvas.configure(
            xscrollcommand=self.x_scrollbar.set, yscrollcommand=self.y_scrollbar.set
        )
        self.test_params = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.test_params, anchor="nw")

        for i in range(7):
            self.test_params.grid_rowconfigure(i, weight=1)
            self.test_params.grid_columnconfigure(i, weight=1)

        # [1] dis
        self.dis_truth_label = tk.Label(
            self.test_params, text="实际距离", font=self.custom_font, anchor="w"
        )
        self.dis_truth_label.grid(sticky=_sticky, row=0, column=0, padx=_padx)
        tk.Entry(
            self.test_params, width=6, textvariable=self.test_params_val["dis"]["truth"]
        ).grid(sticky=_sticky, row=0, column=1, padx=_padx)
        tk.Label(
            self.test_params, textvariable=self.test_params_res_val["dis"]["truth"]
        ).grid(sticky=_sticky, row=0, column=2, padx=_padx)

        self.dis_err_abs_max_label = tk.Label(
            self.test_params,
            text="|与实际距离差值|",
            font=self.custom_font,
            anchor="w",
            padx=_padx,
        )
        self.dis_err_abs_max_label.grid(sticky=_sticky, row=0, column=3, padx=_padx)
        tk.Entry(
            self.test_params,
            width=6,
            textvariable=self.test_params_val["dis"]["err_abs_max"],
        ).grid(sticky=_sticky, row=0, column=4, padx=_padx)
        tk.Label(
            self.test_params,
            textvariable=self.test_params_res_val["dis"]["err_abs_max"],
        ).grid(sticky=_sticky, row=0, column=5, padx=_padx)

        self.dis_std_max_label = tk.Label(
            self.test_params,
            text="滤除异常值后距离标准差",
            font=self.custom_font,
            anchor="w",
            padx=_padx,
        )
        self.dis_std_max_label.grid(sticky=_sticky, row=0, column=6, padx=_padx)
        tk.Entry(
            self.test_params,
            width=6,
            textvariable=self.test_params_val["dis"]["std_max"],
        ).grid(sticky=_sticky, row=0, column=7, padx=_padx)
        tk.Label(
            self.test_params, textvariable=self.test_params_res_val["dis"]["std_max"]
        ).grid(sticky=_sticky, row=0, column=8, padx=_padx)

        self.dis_abnormal_rate_max_label = tk.Label(
            self.test_params,
            text="异常距离数量占比",
            font=self.custom_font,
            anchor="w",
            padx=_padx,
        )
        self.dis_abnormal_rate_max_label.grid(
            sticky=_sticky, row=0, column=9, padx=_padx
        )
        tk.Entry(
            self.test_params,
            width=6,
            textvariable=self.test_params_val["dis"]["abnormal_rate_max"],
        ).grid(sticky=_sticky, row=0, column=10, padx=_padx)
        tk.Label(
            self.test_params,
            textvariable=self.test_params_res_val["dis"]["abnormal_rate_max"],
        ).grid(sticky=_sticky, row=0, column=11, padx=_padx)

        # [2] rssi
        self.master2slave_mean_label = tk.Label(
            self.test_params,
            text="master2slave信号强度均值",
            font=self.custom_font,
            anchor="w",
        )
        self.master2slave_mean_label.grid(sticky=_sticky, row=1, column=0, padx=_padx)
        tk.Entry(
            self.test_params,
            width=6,
            textvariable=self.test_params_val["rssi"]["master2slave"]["mean"],
        ).grid(sticky=_sticky, row=1, column=1, padx=_padx)
        tk.Label(
            self.test_params,
            textvariable=self.test_params_res_val["rssi"]["master2slave"]["mean"],
        ).grid(sticky=_sticky, row=1, column=2, padx=_padx)

        self.master2slave_std_label = tk.Label(
            self.test_params,
            text="master2slave信号强度标准差",
            font=self.custom_font,
            anchor="w",
        )
        self.master2slave_std_label.grid(sticky=_sticky, row=1, column=3, padx=_padx)
        tk.Entry(
            self.test_params,
            width=6,
            textvariable=self.test_params_val["rssi"]["master2slave"]["std_max"],
        ).grid(sticky=_sticky, row=1, column=4, padx=_padx)
        tk.Label(
            self.test_params,
            textvariable=self.test_params_res_val["rssi"]["master2slave"]["std_max"],
        ).grid(sticky=_sticky, row=1, column=5, padx=_padx)

        self.slave2master_mean_label = tk.Label(
            self.test_params,
            text="slave2master信号强度均值",
            font=self.custom_font,
            anchor="w",
        )
        self.slave2master_mean_label.grid(sticky=_sticky, row=1, column=6, padx=_padx)
        tk.Entry(
            self.test_params,
            width=6,
            textvariable=self.test_params_val["rssi"]["slave2master"]["mean"],
        ).grid(sticky=_sticky, row=1, column=7, padx=_padx)
        tk.Label(
            self.test_params,
            textvariable=self.test_params_res_val["rssi"]["slave2master"]["mean"],
        ).grid(sticky=_sticky, row=1, column=8, padx=_padx)

        self.slave2master_std_label = tk.Label(
            self.test_params,
            text="slave2master信号强度标准差",
            font=self.custom_font,
            anchor="w",
        )
        self.slave2master_std_label.grid(sticky=_sticky, row=1, column=9, padx=_padx)
        tk.Entry(
            self.test_params,
            width=6,
            textvariable=self.test_params_val["rssi"]["slave2master"]["std_max"],
        ).grid(sticky=_sticky, row=1, column=10, padx=_padx)
        tk.Label(
            self.test_params,
            textvariable=self.test_params_res_val["rssi"]["slave2master"]["std_max"],
        ).grid(sticky=_sticky, row=1, column=11, padx=_padx)

        # [3] wakeup_time

        self.wakeup_time_max_label = tk.Label(
            self.test_params, text="唤醒时间最大", font=self.custom_font, anchor="w"
        )
        self.wakeup_time_max_label.grid(sticky=_sticky, row=2, column=0, padx=_padx)
        tk.Entry(
            self.test_params,
            width=6,
            textvariable=self.test_params_val["wakeup_time"]["max"],
        ).grid(sticky=_sticky, row=2, column=1, padx=_padx)
        tk.Label(
            self.test_params,
            textvariable=self.test_params_res_val["wakeup_time"]["max"],
        ).grid(sticky=_sticky, row=2, column=2, padx=_padx)

        self.wakeup_time_min_label = tk.Label(
            self.test_params, text="唤醒时间最小", font=self.custom_font, anchor="w"
        )
        self.wakeup_time_min_label.grid(sticky=_sticky, row=2, column=3, padx=_padx)
        tk.Entry(
            self.test_params,
            width=6,
            textvariable=self.test_params_val["wakeup_time"]["min"],
        ).grid(sticky=_sticky, row=2, column=4, padx=_padx)
        tk.Label(
            self.test_params,
            textvariable=self.test_params_res_val["wakeup_time"]["min"],
        ).grid(sticky=_sticky, row=2, column=5, padx=_padx)

        self.wakeup_time_std_max_label = tk.Label(
            self.test_params,
            text="唤醒时间标准差",
            font=self.custom_font,
            anchor="w",
        )
        self.wakeup_time_std_max_label.grid(sticky=_sticky, row=2, column=6, padx=_padx)
        tk.Entry(
            self.test_params,
            width=6,
            textvariable=self.test_params_val["wakeup_time"]["std_max"],
        ).grid(sticky=_sticky, row=2, column=7, padx=_padx)
        tk.Label(
            self.test_params,
            textvariable=self.test_params_res_val["wakeup_time"]["std_max"],
        ).grid(sticky=_sticky, row=2, column=8, padx=_padx)

        # [4] plr

        self.master2slave_plr_label = tk.Label(
            self.test_params,
            text="发送信号丢包率",
            font=self.custom_font,
            anchor="w",
        )
        self.master2slave_plr_label.grid(sticky=_sticky, row=3, column=0, padx=_padx)
        tk.Entry(
            self.test_params,
            width=6,
            textvariable=self.test_params_val["plr"]["master2slave"],
        ).grid(sticky=_sticky, row=3, column=1, padx=_padx)
        tk.Label(
            self.test_params,
            textvariable=self.test_params_res_val["plr"]["master2slave"],
        ).grid(sticky=_sticky, row=3, column=2, padx=_padx)

        self.slave2master_plr_label = tk.Label(
            self.test_params,
            text="接收信号丢包率",
            font=self.custom_font,
            anchor="w",
        )
        self.slave2master_plr_label.grid(sticky=_sticky, row=3, column=3, padx=_padx)
        tk.Entry(
            self.test_params,
            width=6,
            textvariable=self.test_params_val["plr"]["slave2master"],
        ).grid(sticky=_sticky, row=3, column=4, padx=_padx)
        tk.Label(
            self.test_params,
            textvariable=self.test_params_res_val["plr"]["slave2master"],
        ).grid(sticky=_sticky, row=3, column=5, padx=_padx)

        # [5] uwb_clock_offset_ppm
        self.master2slave_clock_offset_ppm_abs_mean_label = tk.Label(
            self.test_params,
            text="发送方向uwb频偏",
            font=self.custom_font,
            anchor="w",
        )
        self.master2slave_clock_offset_ppm_abs_mean_label.grid(
            sticky=_sticky, row=4, column=0, padx=_padx
        )
        tk.Entry(
            self.test_params,
            width=6,
            textvariable=self.test_params_val["uwb_clock_offset_ppm"]["master2slave"][
                "abs_mean_max"
            ],
        ).grid(sticky=_sticky, row=4, column=1, padx=_padx)
        tk.Label(
            self.test_params,
            textvariable=self.test_params_res_val["uwb_clock_offset_ppm"][
                "master2slave"
            ]["abs_mean_max"],
        ).grid(sticky=_sticky, row=4, column=2, padx=_padx)

        self.master2slave_clock_offset_ppm_std_max_label = tk.Label(
            self.test_params,
            text="发送方向uwb频偏标准差",
            font=self.custom_font,
            anchor="w",
        )
        self.master2slave_clock_offset_ppm_std_max_label.grid(
            sticky=_sticky, row=4, column=3, padx=_padx
        )
        tk.Entry(
            self.test_params,
            width=6,
            textvariable=self.test_params_val["uwb_clock_offset_ppm"]["master2slave"][
                "std_max"
            ],
        ).grid(sticky=_sticky, row=4, column=4, padx=_padx)
        tk.Label(
            self.test_params,
            textvariable=self.test_params_res_val["uwb_clock_offset_ppm"][
                "master2slave"
            ]["std_max"],
        ).grid(sticky=_sticky, row=4, column=5, padx=_padx)

        self.slave2master_clock_offset_ppm_abs_mean_label = tk.Label(
            self.test_params,
            text="接收方向uwb频偏",
            font=self.custom_font,
            anchor="w",
        )
        self.slave2master_clock_offset_ppm_abs_mean_label.grid(
            sticky=_sticky, row=4, column=6, padx=_padx
        )
        tk.Entry(
            self.test_params,
            width=6,
            textvariable=self.test_params_val["uwb_clock_offset_ppm"]["slave2master"][
                "abs_mean_max"
            ],
        ).grid(sticky=_sticky, row=4, column=7, padx=_padx)
        tk.Label(
            self.test_params,
            textvariable=self.test_params_res_val["uwb_clock_offset_ppm"][
                "slave2master"
            ]["abs_mean_max"],
        ).grid(sticky=_sticky, row=4, column=8, padx=_padx)

        self.slave2master_clock_offset_ppm_std_max_label = tk.Label(
            self.test_params,
            text="接收方向uwb频偏标准差",
            font=self.custom_font,
            anchor="w",
        )
        self.slave2master_clock_offset_ppm_std_max_label.grid(
            sticky=_sticky, row=4, column=9, padx=_padx
        )
        tk.Entry(
            self.test_params,
            width=6,
            textvariable=self.test_params_val["uwb_clock_offset_ppm"]["slave2master"][
                "std_max"
            ],
        ).grid(sticky=_sticky, row=4, column=10, padx=_padx)
        tk.Label(
            self.test_params,
            textvariable=self.test_params_res_val["uwb_clock_offset_ppm"][
                "slave2master"
            ]["std_max"],
        ).grid(sticky=_sticky, row=4, column=11, padx=_padx)

        # [6] rtc_clock_offset
        self.master2slave_rtc_clock_offset_abs_maxlabel = tk.Label(
            self.test_params,
            text="发送方向rtc频偏",
            font=self.custom_font,
            anchor="w",
        )
        self.master2slave_rtc_clock_offset_abs_maxlabel.grid(
            sticky=_sticky, row=5, column=0, padx=_padx
        )
        tk.Entry(
            self.test_params,
            width=6,
            textvariable=self.test_params_val["rtc_clock_offset_ppm"][
                "master2slave_abs"
            ],
        ).grid(sticky=_sticky, row=5, column=1, padx=_padx)
        tk.Label(
            self.test_params,
            textvariable=self.test_params_res_val["rtc_clock_offset_ppm"][
                "master2slave_abs"
            ],
        ).grid(sticky=_sticky, row=5, column=2, padx=_padx)

        self.slave2master_rtc_clock_offset_abs_maxlabel = tk.Label(
            self.test_params,
            text="接收方向rtc频偏",
            font=self.custom_font,
            anchor="w",
        )
        self.slave2master_rtc_clock_offset_abs_maxlabel.grid(
            sticky=_sticky, row=5, column=3, padx=_padx
        )
        tk.Entry(
            self.test_params,
            width=6,
            textvariable=self.test_params_val["rtc_clock_offset_ppm"][
                "slave2master_abs"
            ],
        ).grid(sticky=_sticky, row=5, column=4, padx=_padx)
        tk.Label(
            self.test_params,
            textvariable=self.test_params_res_val["rtc_clock_offset_ppm"][
                "slave2master_abs"
            ],
        ).grid(sticky=_sticky, row=5, column=5, padx=_padx)

        self.rtc_clock_offset_add = tk.Label(
            self.test_params,
            text="双向rtc频偏相加",
            font=self.custom_font,
            anchor="w",
        )
        self.rtc_clock_offset_add.grid(sticky=_sticky, row=5, column=6, padx=_padx)
        tk.Entry(
            self.test_params,
            width=6,
            textvariable=self.test_params_val["rtc_clock_offset_ppm"]["add"],
        ).grid(sticky=_sticky, row=5, column=7, padx=_padx)
        tk.Label(
            self.test_params,
            textvariable=self.test_params_res_val["rtc_clock_offset_ppm"]["add"],
        ).grid(sticky=_sticky, row=5, column=8, padx=_padx)

        self.test_params.bind("<Configure>", self.on_frame_configure)

    def set_rtt_frame(self):
        self.rtt_frame = tk.Frame(self)
        self.rtt_log_text = scrolledtext.ScrolledText(
            self.rtt_frame, wrap=tk.WORD, width=50, height=60
        )
        self.rtt_log_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.max_lines = 1000
        self.rtt_frame.grid(row=0, column=2, rowspan=4, sticky="nw")

    def append_rtt_log(self, log_entry):
        self.rtt_log_text.after(0, self.rtt_log_text.insert, "end", log_entry)

        def check_and_delete_lines():
            if int(self.rtt_log_text.index("end-1c").split(".")[0]) > self.max_lines:
                self.rtt_log_text.delete("1.0", "2.0")

        self.rtt_log_text.after(0, check_and_delete_lines)

    def add_log(self, log_message):
        self.log_text.insert(
            tk.END,
            f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} : {log_message}\n",
        )
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
            case 4:
                config_data["io_test_val"] = self.io_test_val.get()
            case 5:
                config_data["logo"] = self.logoval.get()
            case 6:
                config_data["product_test_master"][
                    "val"
                ] = self.product_test_master_val.get()
                config_data["product_test_master"][
                    "test_time"
                ] = self.test_time_val.get()
            case 7:
                config_data["P"] = self.pval.get()

            case _:
                pass

    def get_test_params(self):
        data = {
            "dis": {
                "truth": self.test_params_val["dis"]["truth"].get(),
                "err_abs_max": self.test_params_val["dis"]["err_abs_max"].get(),
                "std_max": self.test_params_val["dis"]["std_max"].get(),
                "abnormal_rate_max": self.test_params_val["dis"][
                    "abnormal_rate_max"
                ].get(),
            },
            "rssi": {
                "master2slave": {
                    "mean": self.test_params_val["rssi"]["master2slave"]["mean"].get(),
                    "std_max": self.test_params_val["rssi"]["master2slave"][
                        "std_max"
                    ].get(),
                },
                "slave2master": {
                    "mean": self.test_params_val["rssi"]["slave2master"]["mean"].get(),
                    "std_max": self.test_params_val["rssi"]["slave2master"][
                        "std_max"
                    ].get(),
                },
            },
            "wakeup_time": {
                "max": self.test_params_val["wakeup_time"]["max"].get(),
                "min": self.test_params_val["wakeup_time"]["min"].get(),
                "std_max": self.test_params_val["wakeup_time"]["std_max"].get(),
            },
            "plr": {
                "master2slave": self.test_params_val["plr"]["master2slave"].get(),
                "slave2master": self.test_params_val["plr"]["slave2master"].get(),
            },
            "uwb_clock_offset_ppm": {
                "master2slave": {
                    "abs_mean_max": self.test_params_val["uwb_clock_offset_ppm"][
                        "master2slave"
                    ]["abs_mean_max"].get(),
                    "std_max": self.test_params_val["uwb_clock_offset_ppm"][
                        "master2slave"
                    ]["std_max"].get(),
                },
                "slave2master": {
                    "abs_mean_max": self.test_params_val["uwb_clock_offset_ppm"][
                        "slave2master"
                    ]["abs_mean_max"].get(),
                    "std_max": self.test_params_val["uwb_clock_offset_ppm"][
                        "slave2master"
                    ]["std_max"].get(),
                },
            },
            "rtc_clock_offset_ppm": {
                "master2slave_abs": self.test_params_val["rtc_clock_offset_ppm"][
                    "master2slave_abs"
                ].get(),
                "slave2master_abs": self.test_params_val["rtc_clock_offset_ppm"][
                    "slave2master_abs"
                ].get(),
                "add": self.test_params_val["rtc_clock_offset_ppm"]["add"].get(),
            },
        }
        return data

    def on_resize(self, event):
        if event.widget == self:
            new_width = event.width
            new_height = event.height
            new_size = min(new_width // 50, new_height // 50, 8)
            new_size = max(6, new_size)
            self.custom_font.configure(size=new_size)

        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
