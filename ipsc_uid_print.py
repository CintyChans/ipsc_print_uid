import pylink
import log_wrapper
import time
import re
import threading
import win32print
import pywintypes
import dl_data
import ui
import json
from env import config_data

ipsc_uid_print_win = ui.Window()


class jlink:
    def __init__(self):
        self.uid = ""
        self.jlink = pylink.JLink()

    def connect_target(self, chip_name="nRF52840_xxAA"):
        try:
            self.jlink.open()

        except Exception as e:
            ipsc_uid_print_win.add_log(e)
        if self.jlink.opened():
            self.jlink.set_tif(pylink.enums.JLinkInterfaces.SWD)
            self.jlink.connect(chip_name=chip_name, verbose=True)
            ipsc_uid_print_win.add_log(f"connect")
        else:
            ipsc_uid_print_win.add_log(f"未检测到jlink")

    def flash_firmware(self, addr=0x0000000):
        if ipsc_uid_print_win.var1.get():
            file = ipsc_uid_print_win.gateway_filepath_val.get()
        elif ipsc_uid_print_win.var2.get():
            file = ipsc_uid_print_win.anchor_filepath_val.get()
        elif ipsc_uid_print_win.var3.get():
            file = ipsc_uid_print_win.tag_filepath_val.get()
        else:
            file = ""
            ipsc_uid_print_win.add_log(f"未选择固件")
        self.connect_target()
        if self.jlink.target_connected() and file:
            try:
                ipsc_uid_print_win.add_log("连接成功")
                ipsc_uid_print_win.add_log(f"固件: {file}")
                self.jlink.flash_file(file, addr)
                ipsc_uid_print_win.add_log("烧录成功")
                self.jlink.reset()
                self.jlink.restart()
                ipsc_uid_print_win.add_log("重启成功")
            except:
                return False
        else:
            ipsc_uid_print_win.add_log("连接失败")

    def start_rtt(self):

        if not self.jlink.rtt_get_status().IsRunning:
            self.jlink.rtt_start()
            time.sleep(1)

    def get_uid(self):
        self.start_rtt()
        running = 1
        while running:
            bytes = list(bytearray("arg_list", "utf-8") + b"\x0A\x00")
            bytes_written = self.jlink.rtt_write(0, bytes)

            if bytes_written:
                while 1:
                    terminal_bytes = self.jlink.rtt_read(0, 1024)
                    if terminal_bytes:
                        data = "".join(map(chr, terminal_bytes))
                        if "uid" in data:
                            match = re.findall(r"uid=([a-fA-F0-9]+)", data)
                            if match:
                                self.uid = match[0]
                                ipsc_uid_print_win.add_log(f"uid={self.uid}")
                                running = 0
                                break

    def print_uid(self):
        if not self.jlink.target_connected():
            self.connect_target()
        if self.jlink.target_connected():
            self.uid = ""
            self.get_uid()
            ipsc_uid_print_win.print_res_val.set(f"{self.uid}")
            if ipsc_uid_print_win.var1.get():
                print_zpl_label(uid=self.uid, hardware=1)
            elif ipsc_uid_print_win.var2.get():
                print_zpl_label(uid=self.uid, hardware=2)
            elif ipsc_uid_print_win.var3.get():
                print_zpl_label(uid=self.uid, hardware=3)

    def product_test_master(self, slave_addr=config_data["slave_addr"]):
        if not self.jlink.target_connected():
            self.connect_target()
        if self.jlink.target_connected():
            self.get_uid()
            bytes = list(bytearray(f"arg_config", "utf-8") + b"\x0A\x00")
            bytes_written = self.jlink.rtt_write(0, bytes)
            time.sleep(0.5)
            test_time = ipsc_uid_print_win.test_time_val.get()
            config_data["test_time_val"] = test_time
            bytes = list(
                bytearray(
                    f"product_test_master 5 {slave_addr} 10 {test_time*10}",
                    "utf-8",
                )
                + b"\x0A\x00"
            )
            bytes_written = self.jlink.rtt_write(0, bytes)

            if bytes_written:
                t = threading.Thread(target=self.logging_data, daemon=True)
                t.start()

    def logging_data(self):
        duration = 13
        start_time = time.time()
        self.filename, logger = log_wrapper.init(self.uid)
        ipsc_uid_print_win.add_log("Recording...")
        running = 1
        while running:
            terminal_bytes = self.jlink.rtt_read(0, 1024)
            data = "".join(map(chr, terminal_bytes))
            if data:
                logger.info(data)
                if "test finished" in data or time.time() - start_time > duration:
                    running = 0
        ipsc_uid_print_win.add_log("recorded end")
        ipsc_uid_print_win.test_res_val.set(self.filename)
        ipsc_uid_print_win.analysis_res_val.set(self.filename)
        self.cal_data_file()

    def cal_data_file(self):
        filename = ipsc_uid_print_win.analysis_res_val.get()
        ipsc_uid_print_win.add_log(f"test_res_val:{filename}")
        if filename:
            try:
                data, res = dl_data.cal(
                    filename, ipsc_uid_print_win.get_test_params(), ipsc_uid_print_win
                )
                ipsc_uid_print_win.add_log(f"res {res}")
                if res == {}:
                    ipsc_uid_print_win.add_log(f"cal pass")
                    self.print_uid()

            except Exception as e:
                ipsc_uid_print_win.add_log(e)

    def encrypt_firmware(self):
        if self.jlink.target_connected():
            self.start_rtt()
            bytes = list(bytearray("encrypt_firmware", "utf-8") + b"\x0A\x00")
            bytes_written = self.jlink.rtt_write(0, bytes)
            if bytes_written:
                ipsc_uid_print_win.add_log("encrypt firmware successfully")
                self.jlink.rtt_stop()
                self.jlink.close()
                ipsc_uid_print_win.add_log("jlink close")

    def auto(self):
        try:
            self.flash_firmware()
            self.product_test_master()

        except Exception as e:
            ipsc_uid_print_win.add_log(e)


def print_zpl_label(printer_name="ZDesigner 110Xi4 600 dpi", uid="", hardware=0):
    lvar = ipsc_uid_print_win.Lvar.get() * 23.6
    hvar = ipsc_uid_print_win.Hvar.get() * 23.6
    match hardware:
        case 1:
            dll = 17 * 23.6
            zpl_data = f"""^XA
        ^MCY^PMN
        ^PW1957
        ~JSN
        ^JZY
        ^LH{lvar+0,hvar+0}^LRN
        ^XZ
        ~DGR:SSGFX000.GRF,2160,30,:Z64:eJx9lbFyGjEQhvcsg1wwVpokLpi7PpVLCuYOF+n
        = tGbtN/AbBFRQElEmRdLyByZPYSmNK8gAZ+yYUlBZxYXmskbLSYYgxui2Yhe/+ZVe7twJgV
        = sK7HxAwinTQClFmFWR5WKshk2FqSmjVGIiDlFjLM1VCRRKg9snyTbTT6Vh7P7Cd1ibacJE
        = V05sj70FkrS6lhpnNtAZgjKkGtLs+7WFAW/V0HKDE05kN0gEWHKK8OC6+kUbCaS1qW7D9E
        = ucF5ejsvKQt6GPBhoPAU92gzbyW5bBs4ypIu6CC5rAckL0lbSwok5Fc/bZ6LsHDeE7bS1p
        = H7S3+b6JI/lTlagZrqJ1jvYmKCnpSOSro6/eH2KSCZopMrR1ZY4eP6AytGQwVNik2so8jr
        = beujImN7sdy6eBB44uUGUg1nVibWW0Gj5jHJTo45ZF7zRINvR4d39wkN0p9vPeO1oOFlin
        = o9dmQpyk8SDIb8jiFrsLcI4EvIZVIaQL1HpzJaPYN4qZzMPecWU0UqJSdQ6rgMSe3GKTng
        = mCJp6jFp1SWxNDswjwnEx9kLrH3jhrslMpGKTRUNEV64YLc5U67XzUauyzjuA5dCX9E9Rq
        = DtOFvvoXaBkEtRCq5aIJSZCbYuU94mlOk9YLK5LdPeCzoeRODOAdpjbiZIzkzXZ8wZxjEV
        = S0YB9iOPBVUt2Eu6BhYE4PkZMwpNmrXLQ6n1S5POuSsqHrCnZZ6LUWtjKaCjiDptSMMMoE
        = EteSL01JBlCRTwUaQFgnjYfshcNNcFVtSwtWvN/Fxz1XtnA9uirjTMk4e7OUEm2q1ssOZc
        = WPipAInEscr+qkHdK4TK/GDSnT89OduWe0A+aoMm6rM5ndPjqOnA9S+gig6Oq5UDj+fHJw
        = dHlcODrOTlp/tZ4sO9wv3Tlp833fapfXWnMYzqtacet/wFW2vObXs/63xfc3ZzgIbx1u1l
        = NIksOm8kcsyGo0CG3ZBgzeKs+vgbeTstlT7qVQbvkGdvRWl2lKa8DLKSmm1DLo7qcQ23Ac
        = L+wfbpuq9:FCA9
        ^XA
        ^FO{lvar+49.56+dll*0},{hvar+70.8}
        ^XGR:SSGFX000.GRF,1,1^FS
        ^PQ3,0,3,Y
        ^XZ
        ^XA
        ^IDR:SSGFX000.GRF
        ^FO{lvar+224.2+dll*1},{hvar+224.2} 
        ^BQN,2,6,3
        ^FDMM,A{uid}^FS 
        ^FO{lvar+165.2+dll*1},{hvar+188.8}^A@N,38,38,E::TIMESNEW.FNT^FDU1^FS
        ^FO{lvar+49.56+dll*1},{hvar+304.44}^A@N,30,25,E::TIMESNEW.FNT^FDSN:{uid}^FS

        ^MCY^PMN
        ^PW1957
        ~JSN
        ^JZY
        ^LH{lvar+0,hvar+0}^LRN
        ^XZ
        ~DGR:SSGFX000.GRF,2160,30,:Z64:eJx9lbFyGjEQhvcsg1wwVpokLpi7PpVLCuYOF+n
        = tGbtN/AbBFRQElEmRdLyByZPYSmNK8gAZ+yYUlBZxYXmskbLSYYgxui2Yhe/+ZVe7twJgV
        = sK7HxAwinTQClFmFWR5WKshk2FqSmjVGIiDlFjLM1VCRRKg9snyTbTT6Vh7P7Cd1ibacJE
        = V05sj70FkrS6lhpnNtAZgjKkGtLs+7WFAW/V0HKDE05kN0gEWHKK8OC6+kUbCaS1qW7D9E
        = ucF5ejsvKQt6GPBhoPAU92gzbyW5bBs4ypIu6CC5rAckL0lbSwok5Fc/bZ6LsHDeE7bS1p
        = H7S3+b6JI/lTlagZrqJ1jvYmKCnpSOSro6/eH2KSCZopMrR1ZY4eP6AytGQwVNik2so8jr
        = beujImN7sdy6eBB44uUGUg1nVibWW0Gj5jHJTo45ZF7zRINvR4d39wkN0p9vPeO1oOFlin
        = o9dmQpyk8SDIb8jiFrsLcI4EvIZVIaQL1HpzJaPYN4qZzMPecWU0UqJSdQ6rgMSe3GKTng
        = mCJp6jFp1SWxNDswjwnEx9kLrH3jhrslMpGKTRUNEV64YLc5U67XzUauyzjuA5dCX9E9Rq
        = DtOFvvoXaBkEtRCq5aIJSZCbYuU94mlOk9YLK5LdPeCzoeRODOAdpjbiZIzkzXZ8wZxjEV
        = S0YB9iOPBVUt2Eu6BhYE4PkZMwpNmrXLQ6n1S5POuSsqHrCnZZ6LUWtjKaCjiDptSMMMoE
        = EteSL01JBlCRTwUaQFgnjYfshcNNcFVtSwtWvN/Fxz1XtnA9uirjTMk4e7OUEm2q1ssOZc
        = WPipAInEscr+qkHdK4TK/GDSnT89OduWe0A+aoMm6rM5ndPjqOnA9S+gig6Oq5UDj+fHJw
        = dHlcODrOTlp/tZ4sO9wv3Tlp833fapfXWnMYzqtacet/wFW2vObXs/63xfc3ZzgIbx1u1l
        = NIksOm8kcsyGo0CG3ZBgzeKs+vgbeTstlT7qVQbvkGdvRWl2lKa8DLKSmm1DLo7qcQ23Ac
        = L+wfbpuq9:FCA9
        ^FO{lvar+49.56+dll*1},{hvar+70.8}
        ^XGR:SSGFX000.GRF,1,1^FS
        ^PQ3,0,3,Y
        ^XZ
        ^IDR:SSGFX000.GRF
        ^FO{lvar+224.2+dll*1},{hvar+224.2} 
        ^BQN,2,6,3
        ^FDMM,A{uid}^FS 
        ^FO{lvar+165.2+dll*1},{hvar+188.8}^A@N,38,38,E::TIMESNEW.FNT^FDU1^FS
        ^FO{lvar+49.56+dll*1},{hvar+304.44}^A@N,30,25,E::TIMESNEW.FNT^FDSN:{uid}^FS

        ^MCY^PMN
        ^PW1957
        ~JSN
        ^JZY
        ^LH{lvar+0,hvar+0}^LRN
        ^XZ
        ~DGR:SSGFX000.GRF,2160,30,:Z64:eJx9lbFyGjEQhvcsg1wwVpokLpi7PpVLCuYOF+n
        = tGbtN/AbBFRQElEmRdLyByZPYSmNK8gAZ+yYUlBZxYXmskbLSYYgxui2Yhe/+ZVe7twJgV
        = sK7HxAwinTQClFmFWR5WKshk2FqSmjVGIiDlFjLM1VCRRKg9snyTbTT6Vh7P7Cd1ibacJE
        = V05sj70FkrS6lhpnNtAZgjKkGtLs+7WFAW/V0HKDE05kN0gEWHKK8OC6+kUbCaS1qW7D9E
        = ucF5ejsvKQt6GPBhoPAU92gzbyW5bBs4ypIu6CC5rAckL0lbSwok5Fc/bZ6LsHDeE7bS1p
        = H7S3+b6JI/lTlagZrqJ1jvYmKCnpSOSro6/eH2KSCZopMrR1ZY4eP6AytGQwVNik2so8jr
        = beujImN7sdy6eBB44uUGUg1nVibWW0Gj5jHJTo45ZF7zRINvR4d39wkN0p9vPeO1oOFlin
        = o9dmQpyk8SDIb8jiFrsLcI4EvIZVIaQL1HpzJaPYN4qZzMPecWU0UqJSdQ6rgMSe3GKTng
        = mCJp6jFp1SWxNDswjwnEx9kLrH3jhrslMpGKTRUNEV64YLc5U67XzUauyzjuA5dCX9E9Rq
        = DtOFvvoXaBkEtRCq5aIJSZCbYuU94mlOk9YLK5LdPeCzoeRODOAdpjbiZIzkzXZ8wZxjEV
        = S0YB9iOPBVUt2Eu6BhYE4PkZMwpNmrXLQ6n1S5POuSsqHrCnZZ6LUWtjKaCjiDptSMMMoE
        = EteSL01JBlCRTwUaQFgnjYfshcNNcFVtSwtWvN/Fxz1XtnA9uirjTMk4e7OUEm2q1ssOZc
        = WPipAInEscr+qkHdK4TK/GDSnT89OduWe0A+aoMm6rM5ndPjqOnA9S+gig6Oq5UDj+fHJw
        = dHlcODrOTlp/tZ4sO9wv3Tlp833fapfXWnMYzqtacet/wFW2vObXs/63xfc3ZzgIbx1u1l
        = NIksOm8kcsyGo0CG3ZBgzeKs+vgbeTstlT7qVQbvkGdvRWl2lKa8DLKSmm1DLo7qcQ23Ac
        = L+wfbpuq9:FCA9
        ^FO{lvar+49.56+dll*2},{hvar+70.8}
        ^XGR:SSGFX000.GRF,1,1^FS
        ^PQ3,0,3,Y
        ^XZ
        ^IDR:SSGFX000.GRF
        ^FO{lvar+224.2+dll*2},{hvar+224.2} 
        ^BQN,2,6,3
        ^FDMM,A{uid}^FS 
        ^FO{lvar+165.2+dll*2},{hvar+188.8}^A@N,38,38,E::TIMESNEW.FNT^FDU1^FS
        ^FO{lvar+49.56+dll*2},{hvar+304.44}^A@N,30,25,E::TIMESNEW.FNT^FDSN:{uid}^FS

        ^XZ"""
        case 2:
            dll = 17 * 23.6
            zpl_data = f"""
        ^XA
        ^SZ2^JMA
        ^MCY^PMN
        ^PW1957
        ~JSN
        ^JZY
        ^LH{lvar+0,hvar+0}^LRN
        ~DGR:SSGFX000.GRF,2160,30,:Z64:eJx9lbFyGjEQhvcsg1wwVpokLpi7PpVLCuYOF+ntGbtN/AbBFRQElEmRdLyByZPYSmNK8gAZ+yYUlBZxYXmskbLSYYgxui2Yhe/+ZVe7twJgVsK7HxAwinTQClFmFWR5WKshk2FqSmjVGIiDlFjLM1VCRRKg9snyTbTT6Vh7P7Cd1ibacJEV05sj70FkrS6lhpnNtAZgjKkGtLs+7WFAW/V0HKDE05kN0gEWHKK8OC6+kUbCaS1qW7D9EucF5ejsvKQt6GPBhoPAU92gzbyW5bBs4ypIu6CC5rAckL0lbSwok5Fc/bZ6LsHDeE7bS1pH7S3+b6JI/lTlagZrqJ1jvYmKCnpSOSro6/eH2KSCZopMrR1ZY4eP6AytGQwVNik2so8jrbeujImN7sdy6eBB44uUGUg1nVibWW0Gj5jHJTo45ZF7zRINvR4d39wkN0p9vPeO1oOFlino9dmQpyk8SDIb8jiFrsLcI4EvIZVIaQL1HpzJaPYN4qZzMPecWU0UqJSdQ6rgMSe3GKTngmCJp6jFp1SWxNDswjwnEx9kLrH3jhrslMpGKTRUNEV64YLc5U67XzUauyzjuA5dCX9E9RqDtOFvvoXaBkEtRCq5aIJSZCbYuU94mlOk9YLK5LdPeCzoeRODOAdpjbiZIzkzXZ8wZxjEVS0YB9iOPBVUt2Eu6BhYE4PkZMwpNmrXLQ6n1S5POuSsqHrCnZZ6LUWtjKaCjiDptSMMMoEEteSL01JBlCRTwUaQFgnjYfshcNNcFVtSwtWvN/Fxz1XtnA9uirjTMk4e7OUEm2q1ssOZcWPipAInEscr+qkHdK4TK/GDSnT89OduWe0A+aoMm6rM5ndPjqOnA9S+gig6Oq5UDj+fHJwdHlcODrOTlp/tZ4sO9wv3Tlp833fapfXWnMYzqtacet/wFW2vObXs/63xfc3ZzgIbx1u1lNIksOm8kcsyGo0CG3ZBgzeKs+vgbeTstlT7qVQbvkGdvRWl2lKa8DLKSmm1DLo7qcQ23AcL+wfbpuq9:FCA9
        ^FO{36,0}
        ^XGR:SSGFX000.GRF,1,1^FS
        ^IDR:SSGFX000.GRF
        ^FO{lvar+330.4},{hvar+30} 
        ^BQN,2,10,5
        ^FDMM,A{uid}^FS 
        ^FO{lvar+159},{hvar+150}^A@N,60,60,E:TIMESNER.FNT^FDG1^FS
        ^FO{lvar+49.623},{hvar+280}^A@N,45,43,E:TIMESNER.FNT^FDSN:{uid}^FS

        ^SZ2^JMA
        ^MCY^PMN
        ^PW1957
        ~JSN
        ^JZY
        ^LH{lvar+0,hvar+0}^LRN
        ~DGR:SSGFX000.GRF,2160,30,:Z64:eJx9lbFyGjEQhvcsg1wwVpokLpi7PpVLCuYOF+ntGbtN/AbBFRQElEmRdLyByZPYSmNK8gAZ+yYUlBZxYXmskbLSYYgxui2Yhe/+ZVe7twJgVsK7HxAwinTQClFmFWR5WKshk2FqSmjVGIiDlFjLM1VCRRKg9snyTbTT6Vh7P7Cd1ibacJEV05sj70FkrS6lhpnNtAZgjKkGtLs+7WFAW/V0HKDE05kN0gEWHKK8OC6+kUbCaS1qW7D9EucF5ejsvKQt6GPBhoPAU92gzbyW5bBs4ypIu6CC5rAckL0lbSwok5Fc/bZ6LsHDeE7bS1pH7S3+b6JI/lTlagZrqJ1jvYmKCnpSOSro6/eH2KSCZopMrR1ZY4eP6AytGQwVNik2so8jrbeujImN7sdy6eBB44uUGUg1nVibWW0Gj5jHJTo45ZF7zRINvR4d39wkN0p9vPeO1oOFlino9dmQpyk8SDIb8jiFrsLcI4EvIZVIaQL1HpzJaPYN4qZzMPecWU0UqJSdQ6rgMSe3GKTngmCJp6jFp1SWxNDswjwnEx9kLrH3jhrslMpGKTRUNEV64YLc5U67XzUauyzjuA5dCX9E9RqDtOFvvoXaBkEtRCq5aIJSZCbYuU94mlOk9YLK5LdPeCzoeRODOAdpjbiZIzkzXZ8wZxjEVS0YB9iOPBVUt2Eu6BhYE4PkZMwpNmrXLQ6n1S5POuSsqHrCnZZ6LUWtjKaCjiDptSMMMoEEteSL01JBlCRTwUaQFgnjYfshcNNcFVtSwtWvN/Fxz1XtnA9uirjTMk4e7OUEm2q1ssOZcWPipAInEscr+qkHdK4TK/GDSnT89OduWe0A+aoMm6rM5ndPjqOnA9S+gig6Oq5UDj+fHJwdHlcODrOTlp/tZ4sO9wv3Tlp833fapfXWnMYzqtacet/wFW2vObXs/63xfc3ZzgIbx1u1lNIksOm8kcsyGo0CG3ZBgzeKs+vgbeTstlT7qVQbvkGdvRWl2lKa8DLKSmm1DLo7qcQ23AcL+wfbpuq9:FCA9
        ^FO{36+dll*1,0}
        ^XGR:SSGFX000.GRF,1,1^FS
        ^IDR:SSGFX000.GRF
        ^FO{lvar+330.4+dll*1},{hvar+30} 
        ^BQN,2,10,5
        ^FDMM,A{uid}^FS 
        ^FO{lvar+159+dll*1},{hvar+150}^A@N,60,60,E:TIMESNER.FNT^FDG1^FS
        ^FO{lvar+49.623+dll*1},{hvar+280}^A@N,45,43,E:TIMESNER.FNT^FDSN:{uid}^FS

        ^SZ2^JMA
        ^MCY^PMN
        ^PW1957
        ~JSN
        ^JZY
        ^LH{lvar+0,hvar+0}^LRN
        ~DGR:SSGFX000.GRF,2160,30,:Z64:eJx9lbFyGjEQhvcsg1wwVpokLpi7PpVLCuYOF+ntGbtN/AbBFRQElEmRdLyByZPYSmNK8gAZ+yYUlBZxYXmskbLSYYgxui2Yhe/+ZVe7twJgVsK7HxAwinTQClFmFWR5WKshk2FqSmjVGIiDlFjLM1VCRRKg9snyTbTT6Vh7P7Cd1ibacJEV05sj70FkrS6lhpnNtAZgjKkGtLs+7WFAW/V0HKDE05kN0gEWHKK8OC6+kUbCaS1qW7D9EucF5ejsvKQt6GPBhoPAU92gzbyW5bBs4ypIu6CC5rAckL0lbSwok5Fc/bZ6LsHDeE7bS1pH7S3+b6JI/lTlagZrqJ1jvYmKCnpSOSro6/eH2KSCZopMrR1ZY4eP6AytGQwVNik2so8jrbeujImN7sdy6eBB44uUGUg1nVibWW0Gj5jHJTo45ZF7zRINvR4d39wkN0p9vPeO1oOFlino9dmQpyk8SDIb8jiFrsLcI4EvIZVIaQL1HpzJaPYN4qZzMPecWU0UqJSdQ6rgMSe3GKTngmCJp6jFp1SWxNDswjwnEx9kLrH3jhrslMpGKTRUNEV64YLc5U67XzUauyzjuA5dCX9E9RqDtOFvvoXaBkEtRCq5aIJSZCbYuU94mlOk9YLK5LdPeCzoeRODOAdpjbiZIzkzXZ8wZxjEVS0YB9iOPBVUt2Eu6BhYE4PkZMwpNmrXLQ6n1S5POuSsqHrCnZZ6LUWtjKaCjiDptSMMMoEEteSL01JBlCRTwUaQFgnjYfshcNNcFVtSwtWvN/Fxz1XtnA9uirjTMk4e7OUEm2q1ssOZcWPipAInEscr+qkHdK4TK/GDSnT89OduWe0A+aoMm6rM5ndPjqOnA9S+gig6Oq5UDj+fHJwdHlcODrOTlp/tZ4sO9wv3Tlp833fapfXWnMYzqtacet/wFW2vObXs/63xfc3ZzgIbx1u1lNIksOm8kcsyGo0CG3ZBgzeKs+vgbeTstlT7qVQbvkGdvRWl2lKa8DLKSmm1DLo7qcQ23AcL+wfbpuq9:FCA9
        ^FO{36+dll*2,0}
        ^XGR:SSGFX000.GRF,1,1^FS
        ^IDR:SSGFX000.GRF
        ^FO{lvar+330.4+dll*2},{hvar+30} 
        ^BQN,2,10,5
        ^FDMM,A{uid}^FS 
        ^FO{lvar+159+dll*2},{hvar+150}^A@N,60,60,E:TIMESNER.FNT^FDG1^FS
        ^FO{lvar+49.623+dll*2},{hvar+280}^A@N,45,43,E:TIMESNER.FNT^FDSN:{uid}^FS
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
        ^LH{lvar+0,hvar+0}^LRN
        ~DGR:SSGFX000.GRF,960,20,:Z64:eJxtkkFvEkEUx98wZLlQaBMPkECHo0eIB6EYt4f6ETya4qnXJRzUWMukHJp48QuYqicTD2jSgyQSd4xNelM/gKaT9sCNJcEohmWfb7c0gR3+h3+yv/3vezPvLXAXbkBMHOVBnDFUbTOnbWnkRnYMdT0McKiX2LMHONv9tb3ESgyDeL115roixnKA+EqZ7DzG0sS85baQhDZijFmUQ52A6gJLhLmRBc4C42ATE3D1eSlyBvZH94NgrxcYSHsaTuYqN2+mxD9UgoVH3LkX+Q5oe0K5znd0g8nMIz/woSH8tmp9OUfbb87Ig6YPJeHb8unX4+5W/+LT8fut7kUP1oUvoHlWsJyiqrxMOQWVg5wIsnI86GVGNV3vZZyirhL7zOHN23K6lJe3q1a5KMuQzgYJ0F41o+tqQF5TDiRTCEz9oToVuUe+QczKInAdODXdkkPnjq7TlXiU23fy6hF8o94taAB/gZLLgN4P5JCq/aUcS6Fkcv+0+WPv/s/fT8jp0p0wV5uOLz3sT8djD2mz3JVJqJwcHaXc4kmHnGZzieGEDg+fZ97djJyeHuJ8vYX5ckm3wgKh7ka+GdoGgqH8dW5Baytya4HJkn2TJXyTsccm45MVuZHJrn+SJW2vYI04+A9dst+V:15D5
        ^FO{lvar+278+dll*0},{hvar+270}
        ^GE20,21,21^FS
        ^FO{lvar+30+dll*0},{hvar+9} 
        ^XGR:SSGFX000.GRF,1,1^FS
        ^IDR:SSGFX000.GRF
        ^FO{lvar+140+dll*0},{hvar+51.92} 
        ^BQN,2,6,3
        ^FDMM,A{uid}^FS 
        ^FO{lvar+50+dll*0},{hvar+100}^A@N,38,38,E:TIMESNER.FNT^FDTag^FS
        ^FO{lvar+10+dll*0},{hvar+200}^A@N,30,25,E:TIMESNER.FNT^FDModel:PM12T^FS
        ^FO{lvar+10+dll*0},{hvar+235}^A@N,30,25,E:TIMESNER.FNT^FDSN:{uid}^FS

        ^SZ2^JMA
        ^MCY^PMN
        ^PW1694
        ~JSN
        ^JZY
        ^LH{lvar+0,hvar+0}^LRN
        ~DGR:SSGFX000.GRF,960,20,:Z64:eJxtkkFvEkEUx98wZLlQaBMPkECHo0eIB6EYt4f6ETya4qnXJRzUWMukHJp48QuYqicTD2jSgyQSd4xNelM/gKaT9sCNJcEohmWfb7c0gR3+h3+yv/3vezPvLXAXbkBMHOVBnDFUbTOnbWnkRnYMdT0McKiX2LMHONv9tb3ESgyDeL115roixnKA+EqZ7DzG0sS85baQhDZijFmUQ52A6gJLhLmRBc4C42ATE3D1eSlyBvZH94NgrxcYSHsaTuYqN2+mxD9UgoVH3LkX+Q5oe0K5znd0g8nMIz/woSH8tmp9OUfbb87Ig6YPJeHb8unX4+5W/+LT8fut7kUP1oUvoHlWsJyiqrxMOQWVg5wIsnI86GVGNV3vZZyirhL7zOHN23K6lJe3q1a5KMuQzgYJ0F41o+tqQF5TDiRTCEz9oToVuUe+QczKInAdODXdkkPnjq7TlXiU23fy6hF8o94taAB/gZLLgN4P5JCq/aUcS6Fkcv+0+WPv/s/fT8jp0p0wV5uOLz3sT8djD2mz3JVJqJwcHaXc4kmHnGZzieGEDg+fZ97djJyeHuJ8vYX5ckm3wgKh7ka+GdoGgqH8dW5Baytya4HJkn2TJXyTsccm45MVuZHJrn+SJW2vYI04+A9dst+V:15D5
        ^FO{lvar+278+dll*1},{hvar+270}
        ^GE20,21,21^FS
        ^FO{lvar+30+dll*1},{hvar+9} 
        ^XGR:SSGFX000.GRF,1,1^FS
        ^IDR:SSGFX000.GRF
        ^FO{lvar+140+dll*1},{hvar+51.92} 
        ^BQN,2,6,3
        ^FDMM,A{uid}^FS 
        ^FO{lvar+50+dll*1},{hvar+100}^A@N,38,38,E:TIMESNER.FNT^FDTag^FS
        ^FO{lvar+10+dll*1},{hvar+200}^A@N,30,25,E:TIMESNER.FNT^FDModel:PM12T^FS
        ^FO{lvar+10+dll*1},{hvar+235}^A@N,30,25,E:TIMESNER.FNT^FDSN:{uid}^FS

        ^SZ2^JMA
        ^MCY^PMN
        ^PW1694
        ~JSN
        ^JZY
        ^LH{lvar+0,hvar+0}^LRN
        ~DGR:SSGFX000.GRF,960,20,:Z64:eJxtkkFvEkEUx98wZLlQaBMPkECHo0eIB6EYt4f6ETya4qnXJRzUWMukHJp48QuYqicTD2jSgyQSd4xNelM/gKaT9sCNJcEohmWfb7c0gR3+h3+yv/3vezPvLXAXbkBMHOVBnDFUbTOnbWnkRnYMdT0McKiX2LMHONv9tb3ESgyDeL115roixnKA+EqZ7DzG0sS85baQhDZijFmUQ52A6gJLhLmRBc4C42ATE3D1eSlyBvZH94NgrxcYSHsaTuYqN2+mxD9UgoVH3LkX+Q5oe0K5znd0g8nMIz/woSH8tmp9OUfbb87Ig6YPJeHb8unX4+5W/+LT8fut7kUP1oUvoHlWsJyiqrxMOQWVg5wIsnI86GVGNV3vZZyirhL7zOHN23K6lJe3q1a5KMuQzgYJ0F41o+tqQF5TDiRTCEz9oToVuUe+QczKInAdODXdkkPnjq7TlXiU23fy6hF8o94taAB/gZLLgN4P5JCq/aUcS6Fkcv+0+WPv/s/fT8jp0p0wV5uOLz3sT8djD2mz3JVJqJwcHaXc4kmHnGZzieGEDg+fZ97djJyeHuJ8vYX5ckm3wgKh7ka+GdoGgqH8dW5Baytya4HJkn2TJXyTsccm45MVuZHJrn+SJW2vYI04+A9dst+V:15D5
        ^FO{lvar+278+dll*2},{hvar+270}
        ^GE20,21,21^FS
        ^FO{lvar+30+dll*2},{hvar+9} 
        ^XGR:SSGFX000.GRF,1,1^FS
        ^IDR:SSGFX000.GRF
        ^FO{lvar+140+dll*2},{hvar+51.92} 
        ^BQN,2,6,3
        ^FDMM,A{uid}^FS 
        ^FO{lvar+50+dll*2},{hvar+100}^A@N,38,38,E:TIMESNER.FNT^FDTag^FS
        ^FO{lvar+10+dll*2},{hvar+200}^A@N,30,25,E:TIMESNER.FNT^FDModel:PM12T^FS
        ^FO{lvar+10+dll*2},{hvar+235}^A@N,30,25,E:TIMESNER.FNT^FDSN:{uid}^FS

        
        ^SZ2^JMA
        ^MCY^PMN
        ^PW1694
        ~JSN
        ^JZY
        ^LH{lvar+0,hvar+0}^LRN
        ~DGR:SSGFX000.GRF,960,20,:Z64:eJxtkkFvEkEUx98wZLlQaBMPkECHo0eIB6EYt4f6ETya4qnXJRzUWMukHJp48QuYqicTD2jSgyQSd4xNelM/gKaT9sCNJcEohmWfb7c0gR3+h3+yv/3vezPvLXAXbkBMHOVBnDFUbTOnbWnkRnYMdT0McKiX2LMHONv9tb3ESgyDeL115roixnKA+EqZ7DzG0sS85baQhDZijFmUQ52A6gJLhLmRBc4C42ATE3D1eSlyBvZH94NgrxcYSHsaTuYqN2+mxD9UgoVH3LkX+Q5oe0K5znd0g8nMIz/woSH8tmp9OUfbb87Ig6YPJeHb8unX4+5W/+LT8fut7kUP1oUvoHlWsJyiqrxMOQWVg5wIsnI86GVGNV3vZZyirhL7zOHN23K6lJe3q1a5KMuQzgYJ0F41o+tqQF5TDiRTCEz9oToVuUe+QczKInAdODXdkkPnjq7TlXiU23fy6hF8o94taAB/gZLLgN4P5JCq/aUcS6Fkcv+0+WPv/s/fT8jp0p0wV5uOLz3sT8djD2mz3JVJqJwcHaXc4kmHnGZzieGEDg+fZ97djJyeHuJ8vYX5ckm3wgKh7ka+GdoGgqH8dW5Baytya4HJkn2TJXyTsccm45MVuZHJrn+SJW2vYI04+A9dst+V:15D5
        ^FO{lvar+278+dll*3},{hvar+270}
        ^GE20,21,21^FS
        ^FO{lvar+30+dll*3},{hvar+9} 
        ^XGR:SSGFX000.GRF,1,1^FS
        ^IDR:SSGFX000.GRF
        ^FO{lvar+140+dll*3},{hvar+51.92} 
        ^BQN,2,6,3
        ^FDMM,A{uid}^FS 
        ^FO{lvar+50+dll*3},{hvar+100}^A@N,38,38,E:TIMESNER.FNT^FDTag^FS
        ^FO{lvar+10+dll*3},{hvar+200}^A@N,30,25,E:TIMESNER.FNT^FDModel:PM12T^FS
        ^FO{lvar+10+dll*3},{hvar+235}^A@N,30,25,E:TIMESNER.FNT^FDSN:{uid}^FS

        ^SZ2^JMA
        ^MCY^PMN
        ^PW1694
        ~JSN
        ^JZY
        ^LH{lvar+0,hvar+0}^LRN
        ~DGR:SSGFX000.GRF,960,20,:Z64:eJxtkkFvEkEUx98wZLlQaBMPkECHo0eIB6EYt4f6ETya4qnXJRzUWMukHJp48QuYqicTD2jSgyQSd4xNelM/gKaT9sCNJcEohmWfb7c0gR3+h3+yv/3vezPvLXAXbkBMHOVBnDFUbTOnbWnkRnYMdT0McKiX2LMHONv9tb3ESgyDeL115roixnKA+EqZ7DzG0sS85baQhDZijFmUQ52A6gJLhLmRBc4C42ATE3D1eSlyBvZH94NgrxcYSHsaTuYqN2+mxD9UgoVH3LkX+Q5oe0K5znd0g8nMIz/woSH8tmp9OUfbb87Ig6YPJeHb8unX4+5W/+LT8fut7kUP1oUvoHlWsJyiqrxMOQWVg5wIsnI86GVGNV3vZZyirhL7zOHN23K6lJe3q1a5KMuQzgYJ0F41o+tqQF5TDiRTCEz9oToVuUe+QczKInAdODXdkkPnjq7TlXiU23fy6hF8o94taAB/gZLLgN4P5JCq/aUcS6Fkcv+0+WPv/s/fT8jp0p0wV5uOLz3sT8djD2mz3JVJqJwcHaXc4kmHnGZzieGEDg+fZ97djJyeHuJ8vYX5ckm3wgKh7ka+GdoGgqH8dW5Baytya4HJkn2TJXyTsccm45MVuZHJrn+SJW2vYI04+A9dst+V:15D5
        ^FO{lvar+278+dll*4},{hvar+270}
        ^GE20,21,21^FS
        ^FO{lvar+30+dll*4},{hvar+9} 
        ^XGR:SSGFX000.GRF,1,1^FS
        ^IDR:SSGFX000.GRF
        ^FO{lvar+140+dll*4},{hvar+51.92} 
        ^BQN,2,6,3
        ^FDMM,A{uid}^FS 
        ^FO{lvar+50+dll*4},{hvar+100}^A@N,38,38,E:TIMESNER.FNT^FDTag^FS
        ^FO{lvar+10+dll*4},{hvar+200}^A@N,30,25,E:TIMESNER.FNT^FDModel:PM12T^FS
        ^FO{lvar+10+dll*4},{hvar+235}^A@N,30,25,E:TIMESNER.FNT^FDSN:{uid}^FS
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
                ipsc_uid_print_win.add_log("Started page printer")

                # 打印ZPL数据
                win32print.WritePrinter(hPrinter, zpl_data.encode("utf-8"))
                ipsc_uid_print_win.add_log("Printed ZPL data")

                # 结束打印页面
                win32print.EndPagePrinter(hPrinter)
                ipsc_uid_print_win.add_log("Ended page printer")

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
    lambda e: threading.Thread(target=jlink.product_test_master, daemon=True).start(),
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

ipsc_uid_print_win.mainloop()
config_data["HVar"] = ipsc_uid_print_win.Hvar.get()
config_data["LVar"] = ipsc_uid_print_win.Lvar.get()
config_data["set_value"] = ipsc_uid_print_win.get_test_params()

with open("config.json", "w") as file:
    json.dump(config_data, file, indent=4)
