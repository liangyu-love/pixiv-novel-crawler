"""工具函数模块"""

import os
import re
import json
import logging
from typing import Dict, List, Optional

def setup_logging(level: str = 'INFO') -> None:
    """设置日志配置"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def clean_filename(filename: str) -> str:
    """清理文件名中的非法字符"""
    return "".join(x for x in filename if x.isalnum() or x in (' ', '-', '_'))

def get_downloaded_novels(series_dir: str) -> set:
    """获取已下载的小说ID列表"""
    downloaded = set()
    if os.path.exists(series_dir):
        for file in os.listdir(series_dir):
            if file.endswith('.txt') and file != 'series_completed.txt':
                try:
                    with open(os.path.join(series_dir, file), 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'pixiv.net/novel/show.php?id=' in content:
                            novel_id = content.split('pixiv.net/novel/show.php?id=')[1].split()[0]
                            downloaded.add(novel_id)
                except:
                    continue
    return downloaded

def save_novel(novel_info: Dict, output_dir: str) -> Optional[str]:
    """保存小说到文件"""
    try:
        os.makedirs(output_dir, exist_ok=True)
        title = clean_filename(novel_info['title'])
        output_file = os.path.join(output_dir, f"{title}.txt")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"标题：{novel_info['title']}\n")
            f.write(f"作者：{novel_info['author']}\n")
            f.write(f"创建时间：{novel_info['create_date']}\n")
            f.write(f"标签：{', '.join(novel_info['tags'])}\n")
            f.write(f"链接：https://www.pixiv.net/novel/show.php?id={novel_info['id']}\n")
            f.write("\n" + "="*50 + "\n\n")
            f.write(novel_info['content'])
        
        logging.info(f"小说已保存至: {output_file}")
        return output_file
    except Exception as e:
        logging.error(f"保存小说失败: {str(e)}")
        return None

def mark_series_completed(series_dir: str) -> None:
    """标记系列已完成"""
    with open(os.path.join(series_dir, 'series_completed.txt'), 'w') as f:
        f.write('completed') 