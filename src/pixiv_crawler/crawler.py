"""爬虫核心模块"""

import os
import time
import json
import logging
from typing import Dict, List, Optional, Union

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from . import utils

class PixivNovelCrawler:
    """Pixiv小说爬虫类"""
    
    def __init__(self, config: Dict):
        """初始化爬虫
        
        Args:
            config: 配置字典，包含必要的设置项
        """
        self.config = config
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
        
        if not self.setup_session():
            raise ValueError("Cookie设置失败")

    def setup_session(self) -> bool:
        """设置会话，添加必要的cookie"""
        if not self.config.get('COOKIE'):
            logging.error("请先设置 COOKIE！")
            return False

        try:
            for cookie_pair in self.config['COOKIE'].split(';'):
                if not cookie_pair.strip():
                    continue
                name, value = cookie_pair.strip().split('=', 1)
                self.session.cookies.set(name, value)
            return True
        except Exception as e:
            logging.error(f"Cookie 设置失败: {str(e)}")
            return False

    def make_request(self, url: str) -> Optional[requests.Response]:
        """发送请求并处理重试"""
        retry_delay = self.config.get('RETRY_DELAY', 2)
        max_retries = self.config.get('MAX_RETRIES', 3)
        
        for i in range(max_retries):
            try:
                response = self.session.get(url)
                response.raise_for_status()
                return response
            except Exception as e:
                logging.warning(f"请求失败 (尝试 {i+1}/{max_retries}): {str(e)}")
                if i < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避
                else:
                    raise
        return None

    def get_novel_info(self, novel_id: Union[str, int]) -> Optional[Dict]:
        """获取小说信息"""
        try:
            # 获取小说元数据
            ajax_url = f"{self.base_url}/ajax/novel/{novel_id}"
            logging.info(f"正在获取小说信息: {ajax_url}")
            
            response = self.make_request(ajax_url)
            if not response:
                return None
            
            novel_data = response.json()
            if not novel_data.get('body'):
                logging.error("无法获取小说信息，可能是未登录或Cookie已过期")
                return None
            
            novel = novel_data['body']
            logging.info(f"成功获取小说信息: {novel['title']}")
            
            # 获取小说正文
            logging.info("正在获取小说页面...")
            page_url = f"{self.base_url}/novel/show.php?id={novel_id}"
            
            page_response = self.make_request(page_url)
            if not page_response:
                return None
            
            # 解析页面获取小说内容
            soup = BeautifulSoup(page_response.text, 'html.parser')
            content = ""
            
            # 尝试从预加载数据中获取内容
            preload_data = soup.find('meta', {'id': 'meta-preload-data'})
            if preload_data:
                try:
                    data = json.loads(preload_data.get('content', '{}'))
                    if data.get('novel') and data['novel'].get(str(novel_id)):
                        content = data['novel'][str(novel_id)].get('content', '')
                except:
                    pass
            
            # 如果预加载数据中没有内容，尝试从页面元素中获取
            if not content:
                content_div = soup.find('div', {'id': 'novel-content'})
                if content_div:
                    content = content_div.get_text('\n', strip=True)
            
            if not content:
                logging.error("无法获取小说内容")
                return None
            
            logging.info("成功获取小说正文")
            
            # 检查是否为系列作品
            series_info = None
            if novel.get('seriesNavData'):
                series = novel['seriesNavData']
                series_info = {
                    'id': series['seriesId'],
                    'title': series['title']
                }
                logging.info(f"检测到系列作品: {series['title']}")
            
            # 获取标签
            tags = []
            if novel.get('tags'):
                if isinstance(novel['tags'], list):
                    tags = [tag['tag'] for tag in novel['tags']]
                elif isinstance(novel['tags'], dict) and novel['tags'].get('tags'):
                    tags = [tag['tag'] for tag in novel['tags']['tags']]
            
            return {
                'id': str(novel_id),
                'title': novel['title'],
                'author': novel['userName'],
                'content': content,
                'series_info': series_info,
                'create_date': novel.get('createDate', ''),
                'tags': tags
            }
            
        except Exception as e:
            logging.error(f"获取小说信息失败: {str(e)}")
            return None

    def get_series_novels(self, series_id: Union[str, int]) -> List[str]:
        """获取系列小说列表"""
        try:
            novels = []
            
            # 先获取当前小说的信息
            ajax_url = f"{self.base_url}/ajax/novel/{series_id}"
            logging.info(f"正在获取小说信息: {ajax_url}")
            
            response = self.make_request(ajax_url)
            if not response:
                return []
            
            novel_data = response.json()
            if not novel_data.get('body'):
                logging.error("无法获取小说信息")
                return []
            
            # 获取系列信息
            series_nav = novel_data['body'].get('seriesNavData')
            if not series_nav:
                logging.info("不是系列作品")
                return []
            
            # 获取系列ID
            series_id = str(series_nav.get('seriesId'))
            if not series_id:
                logging.error("无法获取系列ID")
                return []
            
            # 获取系列所有章节
            series_url = f"{self.base_url}/ajax/novel/series/{series_id}?limit=500&last_order=0&order_by=asc"
            series_response = self.make_request(series_url)
            
            if not series_response:
                return []
            
            series_data = series_response.json()
            if series_data.get('body') and series_data['body'].get('page') and series_data['body']['page'].get('series'):
                for novel in series_data['body']['page']['series']:
                    if novel.get('id'):
                        novels.append(str(novel['id']))
            
            # 如果从系列API获取失败，使用导航数据
            if not novels:
                logging.info("从系列API获取失败，使用导航数据...")
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
            logging.info(f"找到 {len(novels)} 篇系列小说")
            return novels
            
        except Exception as e:
            logging.error(f"获取系列小说列表失败: {str(e)}")
            return []

    def crawl_novel(self, novel_id: Union[str, int]) -> bool:
        """爬取小说"""
        try:
            logging.info(f"\n开始爬取小说 ID: {novel_id}")
            novel_info = self.get_novel_info(novel_id)
            
            if not novel_info:
                return False
            
            if novel_info['series_info']:
                # 如果是系列作品，创建系列目录
                series_dir = os.path.join(self.config['DOWNLOAD_PATH'], novel_info['series_info']['title'])
            else:
                # 如果是单独作品，保存在主目录
                series_dir = self.config['DOWNLOAD_PATH']
            
            saved_file = utils.save_novel(novel_info, series_dir)
            
            # 如果是系列作品，检查是否需要下载其他部分
            if novel_info['series_info']:
                logging.info(f"\n检测到系列作品：{novel_info['series_info']['title']}")
                
                # 获取系列列表
                series_novels = self.get_series_novels(novel_id)
                if not series_novels:
                    return True
                
                # 获取已下载的小说ID
                downloaded_novels = utils.get_downloaded_novels(series_dir)
                
                # 计算需要下载的小说
                novels_to_download = [nid for nid in series_novels if nid not in downloaded_novels]
                
                if not novels_to_download:
                    logging.info("系列中的所有小说都已下载完成")
                    utils.mark_series_completed(series_dir)
                    return True
                
                logging.info(f"发现 {len(novels_to_download)} 篇未下载的小说")
                
                # 下载未下载的小说
                with tqdm(total=len(novels_to_download), desc="下载进度", disable=not self.config.get('SHOW_PROGRESS', True)) as pbar:
                    for idx, series_novel_id in enumerate(novels_to_download, 1):
                        logging.info(f"\n爬取系列作品 {idx}/{len(novels_to_download)}")
                        self.crawl_novel(series_novel_id)
                        time.sleep(self.config.get('SLEEP_TIME', 1))
                        pbar.update(1)
                
                utils.mark_series_completed(series_dir)
            
            return True
            
        except Exception as e:
            logging.error(f"爬取失败: {str(e)}")
            return False 