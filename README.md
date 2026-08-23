# ffmpeg_gui

一个基于 Python + Tkinter 的 FFmpeg 图形界面工具，让你无需记忆命令行就能轻松完成音视频处理：提取音频、裁剪、循环、查看信息、预览和格式转换。

##功能一览

- **提取音频**：从视频中提取 MP3，可自定义比特率
- **裁剪**：按开始时间和持续时长剪切音视频（无损拷贝）
- **循环**：指定重复次数或总时长，生成循环音频
- **查看信息**：以中文显示媒体文件的详细流信息（分辨率、编码、帧率等）
- **预览**：调用 ffplay 播放文件，支持从指定时间开始
- **格式转换**：在 mp4 / avi / mkv / mov / mp3 / aac / wav / flac / ogg 之间互转

##安装与依赖

### 1. 安装 Python
- 需要 **Python 3.6+**（[官网下载](https://www.python.org/downloads/)）

### 2. 安装 FFmpeg（核心）
本项目依赖 FFmpeg 套件（ffmpeg.exe / ffplay.exe / ffprobe.exe）。  
**下载方式**（三选一）：
- **方式一（推荐）**：从 [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) 下载 **ffmpeg-release-full.7z**，解压后将 `bin` 文件夹内的所有 `.exe` 复制到项目根目录下的 `ffmpeg-8.1.2-full_build/bin/`（与代码中查找路径一致）
- **方式二**：将 `ffmpeg.exe` 所在目录添加到系统 `PATH` 环境变量
- **方式三**：将 `ffmpeg.exe` 直接放在项目根目录（代码会自动查找）

>如果程序启动时弹窗“未找到 FFmpeg”，请检查上述路径设置。

### 3. 无需额外 Python 库
代码仅使用标准库（`tkinter`、`subprocess` 等），不需要 `pip install` 任何第三方包。

##使用方法

1. 下载本项目所有文件（至少需要 `ffmpeg_gui.py`）。
2. 将 FFmpeg 按上述要求放置好。
3. 双击运行 `ffmpeg_gui.py`（或在终端执行 `python ffmpeg_gui.py`）。
4. 在图形界面中选择对应的标签页，填写输入文件、参数，点击“开始”按钮即可。
5. 所有操作结果和日志会显示在上方的“运行日志”区域。

##界面预览

<img width="562" height="549" alt="image" src="https://github.com/user-attachments/assets/86fd8810-9c0e-4ff4-a674-f49b9e71414d" />

##文件结构

├── ffmpeg_gui.py

├── ffmpeg-8.1.2-full_build/

│ └── bin/

│ ├── ffmpeg.exe

│ ├── ffplay.exe

│ └── ffprobe.exe

└── README.md


##许可证

本项目采用 [MIT License](LICENSE)

##致谢

[FFmpeg](https://ffmpeg.org/) – 强大的多媒体处理框架
