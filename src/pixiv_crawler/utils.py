"""工具函数模块"""

import os
import re
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

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

def merge_series(series_dir: str, output_filename: Optional[str] = None) -> Optional[str]:
    """合并系列小说
    
    Args:
        series_dir: 系列小说所在目录
        output_filename: 输出文件名（可选）
        
    Returns:
        合并后的文件路径，失败则返回 None
    """
    try:
        if not os.path.exists(series_dir):
            logging.error(f"系列目录不存在: {series_dir}")
            return None
            
        # 获取所有txt文件（排除series_completed.txt）
        files = [f for f in os.listdir(series_dir) if f.endswith('.txt') and f != 'series_completed.txt']
        if not files:
            logging.error(f"目录中没有找到小说文件: {series_dir}")
            return None
            
        # 读取所有文件的内容和元数据
        novels = []
        for filename in files:
            filepath = os.path.join(series_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 分离元数据和正文
                    parts = content.split("="*50)
                    if len(parts) >= 2:
                        metadata = parts[0].strip()
                        novel_content = parts[1].strip()
                        # 提取章节序号（如果有）
                        order = 0
                        title_match = re.search(r'标题：.*?第(\d+)章', metadata)
                        if title_match:
                            order = int(title_match.group(1))
                        novels.append({
                            'order': order,
                            'filename': filename,
                            'metadata': metadata,
                            'content': novel_content
                        })
            except Exception as e:
                logging.warning(f"读取文件失败 {filename}: {str(e)}")
                continue
        
        if not novels:
            logging.error("没有成功读取任何小说文件")
            return None
        
        # 按章节序号排序
        novels.sort(key=lambda x: x['order'])
        
        # 生成输出文件名
        if not output_filename:
            series_name = os.path.basename(series_dir)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f"{series_name}_合并_{timestamp}.txt"
        
        output_path = os.path.join(series_dir, output_filename)
        
        # 写入合并后的文件
        with open(output_path, 'w', encoding='utf-8') as f:
            # 写入系列信息
            f.write(f"系列名称：{os.path.basename(series_dir)}\n")
            f.write(f"合并时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"总章节数：{len(novels)}\n")
            f.write("\n" + "="*50 + "\n\n")
            
            # 写入目录
            f.write("目录\n\n")
            for i, novel in enumerate(novels, 1):
                title = re.search(r'标题：(.*?)\n', novel['metadata'])
                if title:
                    f.write(f"{i}. {title.group(1)}\n")
            f.write("\n" + "="*50 + "\n\n")
            
            # 写入正文
            for i, novel in enumerate(novels, 1):
                f.write(f"\n\n第 {i} 章\n")
                f.write(novel['metadata'])
                f.write("\n" + "="*50 + "\n\n")
                f.write(novel['content'])
                f.write("\n\n" + "="*50 + "\n")
        
        logging.info(f"系列小说已合并至: {output_path}")
        return output_path
        
    except Exception as e:
        logging.error(f"合并系列小说失败: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return None 