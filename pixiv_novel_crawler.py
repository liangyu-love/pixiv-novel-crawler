import os
import time
import json
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import config
import re

class PixivNovelCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.pixiv.net/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'dnt': '1',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1'
        }
        self.session.headers.update(self.headers)
        self.base_url = "https://www.pixiv.net"
        self.setup_session()

    def setup_session(self):
        """设置会话，添加必要的cookie"""
        if not config.COOKIE:
            print("请先在 config.py 中设置 COOKIE！")
            print("\n获取 Cookie 的方法：")
            print("1. 用浏览器打开 pixiv.net 并登录")
            print("2. 按 F12 打开开发者工具")
            print("3. 切换到 Network 标签")
            print("4. 刷新页面")
            print("5. 在请求列表中找到 www.pixiv.net")
            print("6. 在右侧 Headers 中找到 Cookie")
            print("7. 复制整个 Cookie 的值")
            print("8. 粘贴到 config.py 中的 COOKIE 变量中")
            return False

        # 解析并设置cookie
        try:
            for cookie_pair in config.COOKIE.split(';'):
                if not cookie_pair.strip():
                    continue
                name, value = cookie_pair.strip().split('=', 1)
                self.session.cookies.set(name, value)
            return True
        except Exception as e:
            print(f"Cookie 设置失败: {str(e)}")
            return False

    def make_request(self, url, max_retries=3, retry_delay=2):
        """发送请求并处理重试"""
        for i in range(max_retries):
            try:
                response = self.session.get(url)
                response.raise_for_status()
                return response
            except Exception as e:
                print(f"请求失败 (尝试 {i+1}/{max_retries}): {str(e)}")
                if i < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避
                else:
                    raise
                    
    def get_novel_info(self, novel_id):
        try:
            # 获取小说元数据
            ajax_url = f"{self.base_url}/ajax/novel/{novel_id}"
            print(f"正在获取小说信息: {ajax_url}")
            
            # 使用重试机制发送请求
            response = self.make_request(ajax_url)
            
            if response.status_code != 200:
                print(f"获取小说信息失败: HTTP {response.status_code}")
                try:
                    print(f"错误响应: {response.text}")
                except:
                    pass
                return None
                
            novel_data = response.json()
            if not novel_data.get('body'):
                print("无法获取小说信息，可能是未登录或Cookie已过期")
                print(f"服务器响应: {novel_data}")
                return None
                
            novel = novel_data['body']
            print(f"成功获取小说信息: {novel['title']}")
            
            # 获取小说正文 - 直接从页面获取
            print("正在获取小说页面...")
            page_url = f"{self.base_url}/novel/show.php?id={novel_id}"
            
            # 使用重试机制发送请求
            page_response = self.make_request(page_url)
            
            if page_response.status_code != 200:
                print(f"获取小说页面失败: HTTP {page_response.status_code}")
                return None
            
            # 解析页面获取小说内容
            soup = BeautifulSoup(page_response.text, 'html.parser')
            
            # 尝试从预加载数据中获取内容
            preload_data = soup.find('meta', {'id': 'meta-preload-data'})
            content = ""
            
            if preload_data:
                try:
                    data = json.loads(preload_data.get('content', '{}'))
                    if data.get('novel') and data['novel'].get(novel_id):
                        content = data['novel'][novel_id].get('content', '')
                except:
                    pass
            
            # 如果预加载数据中没有内容，尝试从页面元素中获取
            if not content:
                content_div = soup.find('div', {'id': 'novel-content'})
                if content_div:
                    content = content_div.get_text('\n', strip=True)
            
            if not content:
                print("无法获取小说内容")
                return None
                
            print("成功获取小说正文")

            # 检查是否为系列作品
            series_info = None
            if novel.get('seriesNavData'):
                series = novel['seriesNavData']
                series_info = {
                    'id': series['seriesId'],
                    'title': series['title']
                }
                print(f"检测到系列作品: {series['title']}")

            # 获取标签
            tags = []
            if novel.get('tags'):
                if isinstance(novel['tags'], list):
                    tags = [tag['tag'] for tag in novel['tags']]
                elif isinstance(novel['tags'], dict) and novel['tags'].get('tags'):
                    tags = [tag['tag'] for tag in novel['tags']['tags']]

            return {
                'id': novel_id,
                'title': novel['title'],
                'author': novel['userName'],
                'content': content,
                'series_info': series_info,
                'create_date': novel.get('createDate', ''),
                'tags': tags
            }
        except Exception as e:
            print(f"获取小说信息失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return None

    def get_series_novels(self, series_id):
        try:
            novels = []
            
            # 先获取当前小说的信息
            ajax_url = f"{self.base_url}/ajax/novel/{series_id}"
            print(f"正在获取小说信息: {ajax_url}")
            
            # 使用重试机制发送请求
            response = self.make_request(ajax_url)
            
            if response.status_code != 200:
                print(f"获取小说信息失败: HTTP {response.status_code}")
                return []
            
            novel_data = response.json()
            if not novel_data.get('body'):
                print("无法获取小说信息")
                return []
            
            # 获取系列信息
            series_nav = novel_data['body'].get('seriesNavData')
            if not series_nav:
                print("不是系列作品")
                return []
            
            # 获取系列ID
            series_id = str(series_nav.get('seriesId'))
            if not series_id:
                print("无法获取系列ID")
                return []
            
            # 获取系列所有章节
            series_url = f"{self.base_url}/ajax/novel/series/{series_id}?limit=500&last_order=0&order_by=asc"
            series_response = self.make_request(series_url)
            
            if series_response.status_code != 200:
                print(f"获取系列列表失败: HTTP {series_response.status_code}")
                return []
            
            series_data = series_response.json()
            if series_data.get('body') and series_data['body'].get('page') and series_data['body']['page'].get('series'):
                for novel in series_data['body']['page']['series']:
                    if novel.get('id'):
                        novels.append(str(novel['id']))
            
            # 如果从系列API获取失败，使用导航数据
            if not novels:
                print("从系列API获取失败，使用导航数据...")
                # 添加当前小说
                novels.append(str(novel_data['body']['id']))
                
                # 获取前面的章节
                current = series_nav
                while current.get('prev') and current['prev'].get('id'):
                    novels.append(str(current['prev']['id']))
                    current = current['prev']
                
                # 获取后面的章节
                current = series_nav
                while current.get('next') and current['next'].get('id'):
                    novels.append(str(current['next']['id']))
                    current = current['next']
            
            # 去重并排序
            novels = sorted(set(novels), key=lambda x: int(x))
            print(f"找到 {len(novels)} 篇系列小说")
            return novels
            
        except Exception as e:
            print(f"获取系列小说列表失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return []

    def save_novel(self, novel_info, output_dir):
        try:
            # 创建输出目录
            os.makedirs(output_dir, exist_ok=True)
            
            # 清理文件名中的非法字符
            title = "".join(x for x in novel_info['title'] if x.isalnum() or x in (' ', '-', '_'))
            
            # 保存小说内容
            output_file = os.path.join(output_dir, f"{title}.txt")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"标题：{novel_info['title']}\n")
                f.write(f"作者：{novel_info['author']}\n")
                f.write(f"创建时间：{novel_info['create_date']}\n")
                f.write(f"标签：{', '.join(novel_info['tags'])}\n")
                f.write(f"链接：https://www.pixiv.net/novel/show.php?id={novel_info['id']}\n")
                f.write("\n" + "="*50 + "\n\n")
                f.write(novel_info['content'])
            
            print(f"小说已保存至: {output_file}")
            return output_file
        except Exception as e:
            print(f"保存小说失败: {str(e)}")
            return None

    def get_downloaded_novels(self, series_dir):
        """获取已下载的小说ID列表"""
        downloaded = set()
        if os.path.exists(series_dir):
            for file in os.listdir(series_dir):
                if file.endswith('.txt') and file != 'series_completed.txt':
                    # 尝试从文件内容中获取ID
                    try:
                        with open(os.path.join(series_dir, file), 'r', encoding='utf-8') as f:
                            content = f.read()
                            if 'pixiv.net/novel/show.php?id=' in content:
                                novel_id = content.split('pixiv.net/novel/show.php?id=')[1].split()[0]
                                downloaded.add(novel_id)
                    except:
                        continue
        return downloaded

    def crawl_novel(self, novel_id):
        try:
            print(f"\n开始爬取小说 ID: {novel_id}")
            novel_info = self.get_novel_info(novel_id)
            
            if not novel_info:
                return False
            
            if novel_info['series_info']:
                # 如果是系列作品，创建系列目录
                series_dir = os.path.join(config.DOWNLOAD_PATH, novel_info['series_info']['title'])
            else:
                # 如果是单独作品，保存在主目录
                series_dir = config.DOWNLOAD_PATH
            
            saved_file = self.save_novel(novel_info, series_dir)
            
            # 如果是系列作品，检查是否需要下载其他部分
            if novel_info['series_info']:
                print(f"\n检测到系列作品：{novel_info['series_info']['title']}")
                
                # 使用当前小说的 ID 来获取系列列表
                series_novels = self.get_series_novels(novel_id)
                if not series_novels:
                    return True
                
                # 获取已下载的小说ID
                downloaded_novels = self.get_downloaded_novels(series_dir)
                
                # 计算需要下载的小说
                novels_to_download = [nid for nid in series_novels if nid not in downloaded_novels]
                
                if not novels_to_download:
                    print("系列中的所有小说都已下载完成")
                    # 标记系列已完成
                    with open(os.path.join(series_dir, 'series_completed.txt'), 'w') as f:
                        f.write('completed')
                    return True
                
                print(f"发现 {len(novels_to_download)} 篇未下载的小说")
                
                # 下载未下载的小说
                for idx, series_novel_id in enumerate(novels_to_download, 1):
                    print(f"\n爬取系列作品 {idx}/{len(novels_to_download)}")
                    self.crawl_novel(series_novel_id)
                    time.sleep(config.SLEEP_TIME)  # 防止请求过于频繁
                
                # 标记系列已完成
                with open(os.path.join(series_dir, 'series_completed.txt'), 'w') as f:
                    f.write('completed')
            
            return True
        except Exception as e:
            print(f"爬取失败: {str(e)}")
            return False

def main():
    crawler = PixivNovelCrawler()
    
    while True:
        novel_id = input("\n请输入Pixiv小说ID（输入q退出）: ").strip()
        if novel_id.lower() == 'q':
            break
        
        crawler.crawl_novel(novel_id)
        print("\n" + "="*50)

if __name__ == "__main__":
    main() 