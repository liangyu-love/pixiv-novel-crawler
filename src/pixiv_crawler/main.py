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

def show_help():
    """显示帮助信息"""
    print("\n使用方法:")
    print("1. 下载小说：直接输入小说ID")
    print("2. 合并系列：merge 系列目录名 [输出文件名]")
    print("3. 退出程序：输入 q 或 quit")
    print("\n示例:")
    print("- 下载小说：23792182")
    print("- 合并系列：merge 邂逅少女与禁忌欲望")
    print("- 指定输出：merge 邂逅少女与禁忌欲望 全本.txt")
    print("- 显示帮助：help")
    print("- 退出程序：q")

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
        
        print("\n欢迎使用 Pixiv 小说下载器！输入 help 获取帮助。")
        
        while True:
            cmd = input("\n请输入命令: ").strip()
            
            if cmd.lower() in ('q', 'quit'):
                break
            elif cmd.lower() == 'help':
                show_help()
            elif cmd.lower().startswith('merge '):
                # 合并系列小说
                parts = cmd[6:].strip().split(maxsplit=1)
                if not parts:
                    print("请指定系列名称！")
                    continue
                
                series_name = parts[0]
                output_filename = parts[1] if len(parts) > 1 else None
                
                series_dir = os.path.join(config['DOWNLOAD_PATH'], series_name)
                if not os.path.exists(series_dir):
                    print(f"系列目录不存在: {series_dir}")
                    continue
                
                print(f"\n开始合并系列：{series_name}")
                if output_filename:
                    print(f"指定输出文件名：{output_filename}")
                
                output_file = utils.merge_series(series_dir, output_filename)
                if output_file:
                    print(f"合并完成！文件已保存至: {output_file}")
                else:
                    print("合并失败！")
            else:
                # 下载小说
                novel_id = cmd
                if not novel_id.isdigit():
                    print("无效的小说ID！")
                    continue
                
                crawler.crawl_novel(novel_id)
                print("\n" + "="*50)
            
    except KeyboardInterrupt:
        print("\n程序已终止")
    except Exception as e:
        print(f"\n程序出错: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 