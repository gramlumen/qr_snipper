"""QR Snipper —— Windows 截图二维码自动识别工具。

模块划分：
    config             配置的加载与数据结构
    clipboard_watcher  剪贴板事件监听（Win32 API）
    decoders           二维码解码后端（策略模式，可扩展）
    actions            识别成功后的动作（插件式注册，可扩展）
    tray               系统托盘图标
    app                应用编排层，把以上模块串联起来
"""

__version__ = "1.0.0"
