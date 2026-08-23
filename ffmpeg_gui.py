import json
import os
import sys
import subprocess
import shutil
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import time
# ==================== 格式配置 ====================
FORMAT_CONFIG = {
    "mp4":  {"video": "libx264", "audio": "aac", "vcodec": "libx264", "acodec": "aac", "ext": ".mp4"},
    "avi":  {"video": "mpeg4",   "audio": "libmp3lame", "vcodec": "mpeg4", "acodec": "libmp3lame", "ext": ".avi"},
    "mkv":  {"video": "libx264", "audio": "aac", "vcodec": "libx264", "acodec": "aac", "ext": ".mkv"},
    "mov":  {"video": "libx264", "audio": "aac", "vcodec": "libx264", "acodec": "aac", "ext": ".mov"},
    "mp3":  {"video": None,      "audio": "libmp3lame", "acodec": "libmp3lame", "ext": ".mp3"},
    "aac":  {"video": None,      "audio": "aac", "acodec": "aac", "ext": ".aac"},
    "wav":  {"video": None,      "audio": "pcm_s16le", "acodec": "pcm_s16le", "ext": ".wav"},
    "flac": {"video": None,      "audio": "flac", "acodec": "flac", "ext": ".flac"},
    "ogg":  {"video": None,      "audio": "libvorbis", "acodec": "libvorbis", "ext": ".ogg"},
}

# ==================== 1. 自动查找 FFmpeg ====================
def find_ffmpeg_bin():
    search_dirs = [ os.path.join(os.getcwd(),'ffmpeg-8.1.2-full_build', "bin"), 
        os.path.join(os.path.dirname(sys.argv[0]),'ffmpeg-8.1.2-full_build' , "bin"),  os.path.dirname(sys.argv[0])]
    for base in search_dirs:
        for root, dirs, files in os.walk(base):
            if "ffmpeg.exe" in files:
                return root
            if "bin" in dirs and "ffmpeg.exe" in os.listdir(os.path.join(root, "bin")):
                return os.path.join(root, "bin")
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return os.path.dirname(ffmpeg_path)
    return None

BIN_DIR = find_ffmpeg_bin()
if not BIN_DIR:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("错误", "未找到 FFmpeg！\n请确保 ffmpeg.exe 在程序所在目录或系统 PATH 中。")
    sys.exit(1)

FFMPEG = os.path.join(BIN_DIR, "ffmpeg.exe")
FFPLAY = os.path.join(BIN_DIR, "ffplay.exe")
FFPROBE = os.path.join(BIN_DIR, "ffprobe.exe")

# ==================== 2. 全局日志输出 ====================
log_widget = None

def log(message, end='\n'):
    """向 GUI 日志区域输出信息"""
    if log_widget:
        log_widget.insert(tk.END, message + end)
        log_widget.see(tk.END)
        log_widget.update_idletasks()
    else:
        print(message, end=end)

def clear_log():
    if log_widget:
        log_widget.delete(1.0, tk.END)

# ==================== 3. 执行命令（后台运行，不阻塞界面） ====================
def run_cmd_async(args, callback=None):
    """在子线程中执行命令，并将输出实时显示到日志"""
    def target():
        try:
            log(f"执行命令: {' '.join(args)}")
            process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='gbk',
                errors='ignore',
                bufsize=1
            )
            for line in process.stdout:
                log(line, end='')
            process.wait()
            if process.returncode == 0:
                log("操作成功完成！")
            else:
                log(f"命令执行失败，错误码: {process.returncode}")
            if callback:
                callback(process.returncode)
        except Exception as e:
            log(f"发生异常: {str(e)}")
            if callback:
                callback(-1)
    threading.Thread(target=target, daemon=True).start()

# ==================== 4. 各功能模块 ====================
def browse_file(entry, filetypes=[("所有文件", "*.*")]):
    """浏览文件并将路径填入Entry"""
    path = filedialog.askopenfilename(title="选择文件", filetypes=filetypes)
    if path:
        entry.delete(0, tk.END)
        entry.insert(0, path)

def browse_save(entry, defaultextension=".mp3", filetypes=[("MP3文件", "*.mp3")]):
    """浏览保存位置"""
    path = filedialog.asksaveasfilename(title="保存为", defaultextension=defaultextension, filetypes=filetypes)
    if path:
        entry.delete(0, tk.END)
        entry.insert(0, path)

def do_extract_audio(input_entry, output_entry, bitrate_entry):
    input_file = input_entry.get().strip()
    if not input_file:
        messagebox.showerror("错误", "请选择输入文件")
        return
    output_file = output_entry.get().strip()
    if not output_file:
        messagebox.showerror("错误", "请指定输出文件名")
        return
    bitrate = bitrate_entry.get().strip() or "192"
    cmd = [FFMPEG, "-i", input_file, "-vn", "-acodec", "libmp3lame", "-ab", f"{bitrate}k", output_file]
    run_cmd_async(cmd)

def do_trim(input_entry, start_entry, duration_entry, output_entry):
    input_file = input_entry.get().strip()
    if not input_file:
        messagebox.showerror("错误", "请选择输入文件")
        return
    try:
        start = float(start_entry.get().strip())
        duration = float(duration_entry.get().strip())
    except ValueError:
        messagebox.showerror("错误", "开始时间和持续时长必须为数字")
        return
    output_file = output_entry.get().strip()
    if not output_file:
        messagebox.showerror("错误", "请指定输出文件名")
        return
    cmd = [FFMPEG, "-i", input_file, "-ss", str(start), "-t", str(duration), "-c", "copy", output_file]
    run_cmd_async(cmd)

def do_loop(input_entry, output_entry, loop_var, total_time_entry):
    input_file = input_entry.get().strip()
    if not input_file:
        messagebox.showerror("错误", "请选择输入文件")
        return
    output_file = output_entry.get().strip()
    if not output_file:
        messagebox.showerror("错误", "请指定输出文件名")
        return
    mode = loop_var.get()
    if mode == 1:  # 重复次数
        times = total_time_entry.get().strip()
        try:
            count = int(times)
            if count < 1:
                messagebox.showerror("错误", "重复次数必须大于0")
                return
            loop_count = count - 1
            cmd = [FFMPEG, "-stream_loop", str(loop_count), "-i", input_file, "-c", "copy", output_file]
        except ValueError:
            messagebox.showerror("错误", "请输入有效整数")
            return
    else:  # 总时长
        sec = total_time_entry.get().strip()
        try:
            sec_float = float(sec)
            if sec_float <= 0:
                messagebox.showerror("错误", "总时长必须大于0")
                return
        except ValueError:
            messagebox.showerror("错误", "请输入有效数字")
            return
        cmd = [FFMPEG, "-stream_loop", "-1", "-i", input_file, "-t", str(sec_float), "-c", "copy", output_file]
    run_cmd_async(cmd)

def do_info(input_entry):
    input_file = input_entry.get().strip()
    if not input_file:
        messagebox.showerror("错误", "请选择输入文件")
        return
    clear_log()
    
    def info_task():
        try:
            # 执行 ffprobe 获取 JSON 数据
            cmd = [FFPROBE, "-v", "quiet", "-print_format", "json", "-show_streams", "-show_format", input_file]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            if result.returncode != 0:
                log(f"ffprobe 执行失败: {result.stderr}")
                return
            data = json.loads(result.stdout)
            
            # ---------- 组装中文输出 ----------
            lines = []
            lines.append("=" * 60)
            lines.append("媒体文件信息")
            lines.append("=" * 60)
            
            # 格式信息（文件整体）
            fmt = data.get('format', {})
            lines.append(f"文件名: {fmt.get('filename', '未知')}")
            size = fmt.get('size')
            if size:
                lines.append(f"文件大小: {int(size) / (1024*1024):.2f} MB")
            duration = fmt.get('duration')
            if duration:
                sec = float(duration)
                hours = int(sec // 3600)
                minutes = int((sec % 3600) // 60)
                seconds = sec % 60
                if hours > 0:
                    lines.append(f"时长: {hours:02d}:{minutes:02d}:{seconds:06.3f}")
                else:
                    lines.append(f"时长: {minutes:02d}:{seconds:06.3f}")
            bitrate = fmt.get('bit_rate')
            if bitrate:
                lines.append(f"总比特率: {int(bitrate)//1000} kbps")
            
            # 流信息（视频/音频/字幕等）
            streams = data.get('streams', [])
            if streams:
                lines.append("-" * 60)
                lines.append("流信息:")
            for idx, stream in enumerate(streams):
                codec_type = stream.get('codec_type', '未知')
                if codec_type == 'video':
                    lines.append(f"\n视频流 #{idx}:")
                    lines.append(f"   编码: {stream.get('codec_name', '未知')}")
                    w = stream.get('width', '?')
                    h = stream.get('height', '?')
                    lines.append(f"   分辨率: {w} x {h}")
                    fps = stream.get('r_frame_rate', '0/0')
                    if fps != '0/0':
                        try:
                            num, den = fps.split('/')
                            fps_val = float(num)/float(den) if float(den)!=0 else 0
                            lines.append(f"   帧率: {fps_val:.2f} fps")
                        except:
                            pass
                    bitrate = stream.get('bit_rate')
                    if bitrate:
                        lines.append(f"   比特率: {int(bitrate)//1000} kbps")
                    pix_fmt = stream.get('pix_fmt')
                    if pix_fmt:
                        lines.append(f"   像素格式: {pix_fmt}")
                    level = stream.get('level')
                    if level:
                        lines.append(f"   Level: {level}")
                elif codec_type == 'audio':
                    lines.append(f"\n音频流 #{idx}:")
                    lines.append(f"   编码: {stream.get('codec_name', '未知')}")
                    sample_rate = stream.get('sample_rate')
                    if sample_rate:
                        lines.append(f"   采样率: {int(sample_rate)//1000} kHz")
                    channels = stream.get('channels', '?')
                    lines.append(f"   声道数: {channels}")
                    bitrate = stream.get('bit_rate')
                    if bitrate:
                        lines.append(f"   比特率: {int(bitrate)//1000} kbps")
                elif codec_type == 'subtitle':
                    lines.append(f"\n字幕流 #{idx}:")
                    lines.append(f"   编码: {stream.get('codec_name', '未知')}")
                    lang = stream.get('tags', {}).get('language')
                    if lang:
                        lines.append(f"   语言: {lang}")
                else:
                    lines.append(f"\n其他流 #{idx}: {codec_type}")
                    lines.append(f"   编码: {stream.get('codec_name', '未知')}")
            
            lines.append("\n" + "=" * 60)
            log('\n'.join(lines))
            
        except json.JSONDecodeError:
            log("❌ 解析媒体信息失败，输出不是有效JSON")
        except Exception as e:
            log(f"❌ 获取信息时发生异常: {e}")
    
    # 在后台线程中执行，避免界面卡死
    threading.Thread(target=info_task, daemon=True).start()

def do_preview(input_entry, start_entry):
    input_file = input_entry.get().strip()
    if not input_file:
        messagebox.showerror("错误", "请选择输入文件")
        return
    start = start_entry.get().strip()
    cmd = [FFPLAY, "-i", input_file]
    if start:
        try:
            float(start)  # 验证是否为数字
            cmd.extend(["-ss", start])
        except ValueError:
            messagebox.showerror("错误", "开始时间必须为数字")
            return
    # ffplay 会打开新窗口，我们在后台启动，不阻塞
    def play():
        try:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            log(f"启动播放器失败: {e}")
    threading.Thread(target=play, daemon=True).start()
def do_convert(input_entry, format_var, output_entry, bitrate_entry):
    input_file = input_entry.get().strip()
    if not input_file:
        messagebox.showerror("错误", "请选择输入文件")
        return
    fmt = format_var.get()
    if not fmt:
        messagebox.showerror("错误", "请选择输出格式")
        return
    output_file = output_entry.get().strip()
    if not output_file:
        messagebox.showerror("错误", "请指定输出文件名")
        return
    config = FORMAT_CONFIG.get(fmt)
    if not config:
        messagebox.showerror("错误", "不支持的格式")
        return
    ext = config["ext"]
    # 智能替换扩展名：去掉原有后缀（如果有），换上正确的目标后缀
    base_name, old_ext = os.path.splitext(output_file)
    output_file = base_name + ext
    output_entry.delete(0, tk.END)
    output_entry.insert(0, output_file)

    cmd = [FFMPEG, "-i", input_file]
    vcodec = config.get("vcodec")
    acodec = config.get("acodec")
    if vcodec:
        cmd.extend(["-c:v", vcodec])
    else:
        cmd.append("-vn")  # 无视频，纯音频
    if acodec:
        cmd.extend(["-c:a", acodec])
    bitrate = bitrate_entry.get().strip()
    if bitrate:
        try:
            br = int(bitrate)
            if vcodec:
                cmd.extend(["-b:v", f"{br}k"])
            else:
                cmd.extend(["-b:a", f"{br}k"])
        except ValueError:
            messagebox.showerror("错误", "比特率请输入有效整数")
            return
    cmd.append(output_file)
    run_cmd_async(cmd)
# ==================== 5. 创建主窗口 ====================
class App:
    def __init__(self, root):
        self.root = root
        root.title("FFmpeg 三件套 GUI 助手")
        root.geometry("750x700")
        root.minsize(750, 700)

        # 全局日志文本框
        global log_widget
        log_frame = ttk.LabelFrame(root, text="运行日志", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        log_widget = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=12)
        log_widget.pack(fill=tk.BOTH, expand=True)

        # 创建 Notebook (标签页)
        nb = ttk.Notebook(root)
        nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ---- 标签页1: 提取音频 ----
        tab1 = ttk.Frame(nb)
        nb.add(tab1, text="提取音频")

        ttk.Label(tab1, text="输入 MP4 文件:").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        entry1_in = ttk.Entry(tab1, width=60)
        entry1_in.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(tab1, text="浏览", command=lambda: browse_file(entry1_in, [("视频文件", "*.mp4"), ("所有文件", "*.*")])).grid(row=0, column=2, padx=5)

        ttk.Label(tab1, text="输出 MP3 文件:").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        entry1_out = ttk.Entry(tab1, width=60)
        entry1_out.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(tab1, text="另存为", command=lambda: browse_save(entry1_out, ".mp3", [("MP3文件", "*.mp3")])).grid(row=1, column=2, padx=5)

        ttk.Label(tab1, text="比特率 (kbps, 默认192):").grid(row=2, column=0, sticky='e', padx=5, pady=5)
        entry1_bit = ttk.Entry(tab1, width=10)
        entry1_bit.grid(row=2, column=1, sticky='w', padx=5, pady=5)

        ttk.Button(tab1, text="开始提取", command=lambda: do_extract_audio(entry1_in, entry1_out, entry1_bit)).grid(row=3, column=1, pady=15)

        # ---- 标签页2: 裁剪 ----
        tab2 = ttk.Frame(nb)
        nb.add(tab2, text="裁剪")

        ttk.Label(tab2, text="输入文件:").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        entry2_in = ttk.Entry(tab2, width=60)
        entry2_in.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(tab2, text="浏览", command=lambda: browse_file(entry2_in)).grid(row=0, column=2, padx=5)

        ttk.Label(tab2, text="开始时间 (秒):").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        entry2_start = ttk.Entry(tab2, width=10)
        entry2_start.grid(row=1, column=1, sticky='w', padx=5, pady=5)

        ttk.Label(tab2, text="持续时长 (秒):").grid(row=2, column=0, sticky='e', padx=5, pady=5)
        entry2_dur = ttk.Entry(tab2, width=10)
        entry2_dur.grid(row=2, column=1, sticky='w', padx=5, pady=5)

        ttk.Label(tab2, text="输出文件:").grid(row=3, column=0, sticky='e', padx=5, pady=5)
        entry2_out = ttk.Entry(tab2, width=60)
        entry2_out.grid(row=3, column=1, padx=5, pady=5)
        ttk.Button(tab2, text="另存为", command=lambda: browse_save(entry2_out, ".mp3", [("音频文件", "*.mp3"), ("视频文件", "*.mp4")])).grid(row=3, column=2, padx=5)

        ttk.Button(tab2, text="开始裁剪", command=lambda: do_trim(entry2_in, entry2_start, entry2_dur, entry2_out)).grid(row=4, column=1, pady=15)

        # ---- 标签页3: 循环 ----
        tab3 = ttk.Frame(nb)
        nb.add(tab3, text="循环")

        ttk.Label(tab3, text="输入音频:").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        entry3_in = ttk.Entry(tab3, width=60)
        entry3_in.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(tab3, text="浏览", command=lambda: browse_file(entry3_in, [("音频文件", "*.mp3"), ("所有文件", "*.*")])).grid(row=0, column=2, padx=5)

        loop_var = tk.IntVar(value=1)
        ttk.Radiobutton(tab3, text="指定重复次数", variable=loop_var, value=1).grid(row=1, column=0, sticky='w', padx=10)
        ttk.Radiobutton(tab3, text="指定总时长 (秒)", variable=loop_var, value=2).grid(row=2, column=0, sticky='w', padx=10)

        ttk.Label(tab3, text="次数 / 总时长:").grid(row=1, column=1, sticky='e', padx=5)  # 右对齐
        entry3_time = ttk.Entry(tab3, width=10)
        entry3_time.grid(row=1, column=2, sticky='w', padx=5)  # 移到第2列，去掉rowspan

        ttk.Label(tab3, text="输出文件:").grid(row=3, column=0, sticky='e', padx=5, pady=5)
        entry3_out = ttk.Entry(tab3, width=60)
        entry3_out.grid(row=3, column=1, padx=5, pady=5)
        ttk.Button(tab3, text="另存为", command=lambda: browse_save(entry3_out, ".mp3", [("MP3文件", "*.mp3")])).grid(row=3, column=2, padx=5)

        ttk.Button(tab3, text="开始循环", command=lambda: do_loop(entry3_in, entry3_out, loop_var, entry3_time)).grid(row=4, column=1, pady=15)

        # ---- 标签页4: 查看信息 ----
        tab4 = ttk.Frame(nb)
        nb.add(tab4, text="信息")

        ttk.Label(tab4, text="文件:").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        entry4_in = ttk.Entry(tab4, width=60)
        entry4_in.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(tab4, text="浏览", command=lambda: browse_file(entry4_in)).grid(row=0, column=2, padx=5)

        ttk.Button(tab4, text="查看信息 (JSON)", command=lambda: do_info(entry4_in)).grid(row=1, column=1, pady=15)

        # ---- 标签页5: 预览 ----
        tab5 = ttk.Frame(nb)
        nb.add(tab5, text="预览")

        ttk.Label(tab5, text="文件:").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        entry5_in = ttk.Entry(tab5, width=60)
        entry5_in.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(tab5, text="浏览", command=lambda: browse_file(entry5_in)).grid(row=0, column=2, padx=5)

        ttk.Label(tab5, text="从第几秒开始 (可选):").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        entry5_start = ttk.Entry(tab5, width=10)
        entry5_start.grid(row=1, column=1, sticky='w', padx=5, pady=5)

        ttk.Button(tab5, text="播放", command=lambda: do_preview(entry5_in, entry5_start)).grid(row=2, column=1, pady=15)
        ttk.Label(tab5, text="快捷键: ESC退出, ←/→ 快进/快退10秒, ↑/↓ 快进/快退1分钟", font=("Arial", 9), foreground="gray").grid(row=3, column=0, columnspan=3, pady=5)
        # ---- 标签页6: 格式转换 ----
        tab6 = ttk.Frame(nb)
        nb.add(tab6, text="格式转换")

        ttk.Label(tab6, text="输入文件:").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        entry6_in = ttk.Entry(tab6, width=60)
        entry6_in.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(tab6, text="浏览", command=lambda: browse_file(entry6_in)).grid(row=0, column=2, padx=5)

        ttk.Label(tab6, text="输出格式:").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        format_var = tk.StringVar()
        format_combo = ttk.Combobox(tab6, textvariable=format_var, values=list(FORMAT_CONFIG.keys()), state="readonly", width=10)
        format_combo.grid(row=1, column=1, sticky='w', padx=5, pady=5)
        format_combo.set("mp4")

        ttk.Label(tab6, text="输出文件:").grid(row=2, column=0, sticky='e', padx=5, pady=5)
        entry6_out = ttk.Entry(tab6, width=60)
        entry6_out.grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(tab6, text="另存为", command=lambda: browse_save(entry6_out, defaultextension=".mp4", filetypes=[("所有文件", "*.*")])).grid(row=2, column=2, padx=5)

        ttk.Label(tab6, text="比特率 (kbps, 可选):").grid(row=3, column=0, sticky='e', padx=5, pady=5)
        entry6_bit = ttk.Entry(tab6, width=10)
        entry6_bit.grid(row=3, column=1, sticky='w', padx=5, pady=5)

        ttk.Button(tab6, text="开始转换", command=lambda: do_convert(entry6_in, format_var, entry6_out, entry6_bit)).grid(row=4, column=1, pady=15)
# 底部清空日志按钮
        bottom_frame = ttk.Frame(root)
        bottom_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        ttk.Button(bottom_frame, text="清空日志", command=clear_log).pack(side=tk.RIGHT)

# ==================== 6. 启动 ====================
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()