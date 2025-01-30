# Pixiv Novel Crawler

一个用于下载 Pixiv 小说的爬虫工具。支持下载单篇小说和系列小说。

## 功能特点

- 支持下载单篇小说
- 支持下载系列小说
- 自动检测并跳过已下载的章节
- 自动重试机制
- 保存小说元数据（标题、作者、标签等）
- 优雅的进度显示

## 安装

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/pixiv-novel-crawler.git
cd pixiv-novel-crawler
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

## 配置

1. 复制配置文件模板：
```bash
cp config.example.py config.py
```

2. 在 `config.py` 中设置你的 Pixiv Cookie：

获取 Cookie 的方法：
1. 用浏览器打开 pixiv.net 并登录
2. 按 F12 打开开发者工具
3. 切换到 Network 标签
4. 刷新页面
5. 在请求列表中找到 www.pixiv.net
6. 在右侧 Headers 中找到 Cookie
7. 复制整个 Cookie 的值
8. 粘贴到 config.py 中的 COOKIE 变量中

## 使用方法

1. 运行爬虫：
```bash
python src/pixiv_crawler/main.py
```

2. 输入小说 ID（可以从 Pixiv 小说页面的 URL 中获取）

3. 小说将被下载到 `novels` 目录中

## 项目结构

```
pixiv-novel-crawler/
├── src/
│   └── pixiv_crawler/
│       ├── __init__.py
│       ├── main.py
│       ├── crawler.py
│       └── utils.py
├── tests/
│   └── test_crawler.py
├── docs/
│   └── API.md
├── novels/           # 下载的小说保存在这里
├── config.py         # 配置文件
├── requirements.txt  # 项目依赖
└── README.md
```

## 注意事项

- 请遵守 Pixiv 的使用条款
- 不要过于频繁地请求，建议设置适当的延迟
- 仅用于个人学习和研究使用

## 许可证

MIT License 