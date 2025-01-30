# Pixiv 小说下载器

一个用于下载 Pixiv 小说的工具，支持命令行和图形界面。

## 功能特点

### GUI 版本
- 简洁美观的图形界面
- 支持输入小说 ID 或 URL 链接
- 显示完整的下载进度和状态
- 支持系列小说批量下载
- 自动合并系列小说
- 实时显示下载日志
- 可配置下载设置（Cookie、下载目录等）

### 命令行版本
- 支持单章小说下载
- 支持系列小说批量下载
- 自动获取系列信息
- 保存元数据信息

## 使用说明

### GUI 版本使用
1. 运行 `python pixiv_gui.py`
2. 在输入框中输入小说 ID 或 URL
3. 点击"下载"按钮开始下载
4. 下载完成后可以在"合并"标签页中合并系列小说

### 命令行版本使用
```bash
# 下载单章小说
python pixiv.py -n 小说ID

# 下载系列小说
python pixiv.py -s 系列ID
```

## 配置说明

### 必要配置
- `COOKIE`: Pixiv 的登录 Cookie（必需）

### 可选配置
- `DOWNLOAD_PATH`: 下载目录，默认为 `novels`
- `SLEEP_TIME`: 下载间隔时间（秒），默认为 1
- `MAX_RETRIES`: 最大重试次数，默认为 3
- `RETRY_DELAY`: 重试等待时间（秒），默认为 2
- `SAVE_METADATA`: 是否保存元数据，默认为 True
- `SHOW_PROGRESS`: 是否显示进度，默认为 True
- `LOG_LEVEL`: 日志级别，默认为 INFO

## 更新日志

### v1.1.0 (GUI版本)
- 添加图形界面支持
- 实时显示下载进度
- 支持系列小说自动合并
- 优化下载日志显示
- 添加配置界面
- 支持URL输入

### v1.0.0
- 实现基本的下载功能
- 支持系列小说下载
- 添加命令行参数支持
- 实现基本的错误处理

## 注意事项
1. 使用前需要配置 Pixiv 的登录 Cookie
2. 下载速度建议设置合理的间隔时间，避免被限制
3. 部分小说可能需要登录才能访问
4. 建议使用稳定的网络连接

## 依赖
- Python 3.6+
- requests
- PyQt6 (GUI版本)
- beautifulsoup4

## 安装
```bash
# 克隆仓库
git clone https://github.com/your-username/pixiv-novel-downloader.git

# 安装依赖
pip install -r requirements.txt
```

## 贡献
欢迎提交 Issue 和 Pull Request！

## 许可
MIT License 