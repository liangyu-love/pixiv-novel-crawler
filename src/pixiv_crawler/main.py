"""主程序入口"""

import os
import sys
import importlib.util
from typing import Dict

from . import utils
from .crawler import PixivNovelCrawler

def load_config() -> Dict:
    """加载配置文件"""
    # 尝试从当前目录加载配置
    if os.path.exists('config.py'):
        spec = importlib.util.spec_from_file_location("config", "config.py")
        config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config)
        return vars(config)
    
    # 如果当前目录没有，尝试从示例配置创建
    if os.path.exists('config.example.py'):
        print("未找到配置文件，将使用示例配置...")
        spec = importlib.util.spec_from_file_location("config", "config.example.py")
        config = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config)
        return vars(config)
    
    # 如果都没有，使用默认配置
    return {
        'COOKIE': '',
        'DOWNLOAD_PATH': 'novels',
        'SLEEP_TIME': 1,
        'MAX_RETRIES': 3,
        'RETRY_DELAY': 2,
        'SAVE_METADATA': True,
        'SHOW_PROGRESS': True,
        'LOG_LEVEL': 'INFO'
    }

def main():
    """主程序入口"""
    # 加载配置
    config = load_config()
    
    # 设置日志
    utils.setup_logging(config.get('LOG_LEVEL', 'INFO'))
    
    # 创建下载目录
    os.makedirs(config.get('DOWNLOAD_PATH', 'novels'), exist_ok=True)
    
    try:
        # 创建爬虫实例
        crawler = PixivNovelCrawler(config)
        
        while True:
            novel_id = input("\n请输入Pixiv小说ID（输入q退出）: ").strip()
            if novel_id.lower() == 'q':
                break
            
            crawler.crawl_novel(novel_id)
            print("\n" + "="*50)
            
    except KeyboardInterrupt:
        print("\n程序已终止")
    except Exception as e:
        print(f"\n程序出错: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 