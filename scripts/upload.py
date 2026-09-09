#!/usr/bin/env python3
"""
上传STRM文件中的文件到123云盘
"""

import os
import sys
import argparse
import logging
import requests
import urllib3
from pathlib import Path
from urllib.parse import urlparse, unquote
import tempfile
import shutil

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProgressFile:
    """带进度显示的文件包装类"""
    
    def __init__(self, file_path, total_size):
        self.file_path = file_path
        self.total_size = total_size
        self.uploaded = 0
        self.last_log_time = 0
        self.file = open(file_path, 'rb')
    
    def read(self, chunk_size=65536):
        data = self.file.read(chunk_size)
        if data:
            self.uploaded += len(data)
            self._log_progress()
        return data
    
    def _log_progress(self):
        import time
        current_time = time.time()
        # 每3秒打印一次进度
        if current_time - self.last_log_time >= 3 or self.uploaded == self.total_size:
            if self.total_size > 0:
                percent = (self.uploaded / self.total_size) * 100
                logger.info(f"上传进度: {percent:.1f}% ({self.uploaded}/{self.total_size})")
            self.last_log_time = current_time
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file.close()
        return False
    
    def __iter__(self):
        return self
    
    def __next__(self):
        data = self.read()
        if not data:
            raise StopIteration
        return data


class WebDAVClient:
    """WebDAV客户端"""
    
    def __init__(self, address, username, password):
        self.address = address.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.auth = (username, password)
    
    def upload_file(self, local_path, remote_path):
        """上传文件到WebDAV"""
        url = f"{self.address}{remote_path}"
        
        # 确保远程目录存在
        self._ensure_remote_dir(os.path.dirname(remote_path))
        
        # 获取文件大小
        file_size = os.path.getsize(local_path)
        logger.info(f"开始上传: {remote_path} ({self._format_size(file_size)})")
        
        # 创建带进度的文件包装
        progress_file = ProgressFile(local_path, file_size)
        
        # 上传文件，设置超时
        response = self.session.put(url, data=progress_file, timeout=(30, 1800))
        response.raise_for_status()
        
        logger.info(f"上传成功: {remote_path}")
        return True
    
    def _format_size(self, size_bytes):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} TB"
    
    def _ensure_remote_dir(self, remote_dir):
        """确保远程目录存在"""
        if not remote_dir or remote_dir == '/':
            return
        
        url = f"{self.address}{remote_dir}"
        
        # 检查目录是否存在
        try:
            response = self.session.request('HEAD', url)
            if response.status_code == 200:
                return
        except:
            pass
        
        # 创建目录
        try:
            response = self.session.request('MKCOL', url)
            if response.status_code in [200, 201, 405]:  # 405表示目录已存在
                logger.info(f"目录已存在或创建成功: {remote_dir}")
            else:
                response.raise_for_status()
        except Exception as e:
            logger.warning(f"创建目录失败: {remote_dir}, 错误: {e}")
    
    def check_connection(self):
        """检查WebDAV连接"""
        try:
            response = self.session.request('HEAD', self.address)
            return response.status_code in [200, 207, 401, 403]
        except Exception as e:
            logger.error(f"WebDAV连接失败: {e}")
            return False


def read_strm_file(strm_path):
    """读取STRM文件，返回URL"""
    try:
        with open(strm_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # STRM文件通常只包含一个URL
        if content.startswith('http://') or content.startswith('https://'):
            return content
        
        # 如果不是URL，可能是路径，需要处理
        logger.warning(f"STRM文件内容不是URL: {strm_path}")
        return None
    except Exception as e:
        logger.error(f"读取STRM文件失败: {strm_path}, 错误: {e}")
        return None


def download_file(url, local_path):
    """下载文件"""
    try:
        logger.info(f"开始下载: {url}")
        response = requests.get(url, stream=True, timeout=(30, 300), verify=False)
        response.raise_for_status()
        
        # 获取文件大小
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=65536):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        if downloaded % (1024 * 1024) < 65536:  # 每MB打印一次
                            logger.info(f"下载进度: {percent:.1f}% ({downloaded}/{total_size})")
        
        logger.info(f"下载完成: {local_path}")
        return True
    except Exception as e:
        logger.error(f"下载失败: {url}, 错误: {e}")
        return False


def get_filename_from_strm(strm_path, url):
    """从STRM文件名或URL获取文件名"""
    # 优先使用STRM文件名（去掉.strm扩展名）
    strm_filename = Path(strm_path).stem
    
    # 如果STRM文件名包含特殊字符，使用URL中的文件名
    if '@' in strm_filename or len(strm_filename) > 100:
        parsed_url = urlparse(url)
        url_filename = unquote(os.path.basename(parsed_url.path))
        if url_filename:
            return url_filename
    
    # 尝试从URL获取扩展名
    parsed_url = urlparse(url)
    url_path = unquote(parsed_url.path)
    url_ext = os.path.splitext(url_path)[1]
    
    # 如果STRM文件名没有扩展名，添加URL的扩展名
    strm_ext = os.path.splitext(strm_filename)[1]
    if not strm_ext and url_ext:
        return strm_filename + url_ext
    
    return strm_filename


def process_strm_files(strm_folder, upload_path, webdav_client):
    """处理所有STRM文件"""
    strm_folder = Path(strm_folder)
    
    if not strm_folder.exists():
        logger.error(f"STRM文件夹不存在: {strm_folder}")
        return False
    
    # 查找所有STRM文件
    strm_files = list(strm_folder.glob("*.strm"))
    
    if not strm_files:
        logger.warning(f"未找到STRM文件: {strm_folder}")
        return False
    
    logger.info(f"找到 {len(strm_files)} 个STRM文件")
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        success_count = 0
        fail_count = 0
        
        for strm_file in strm_files:
            logger.info(f"处理: {strm_file.name}")
            
            # 读取URL
            url = read_strm_file(strm_file)
            if not url:
                fail_count += 1
                continue
            
            # 获取文件名
            filename = get_filename_from_strm(strm_file, url)
            local_path = os.path.join(temp_dir, filename)
            
            # 下载文件
            if not download_file(url, local_path):
                fail_count += 1
                continue
            
            # 构建远程路径
            remote_path = f"{upload_path.rstrip('/')}/{filename}"
            
            # 上传到WebDAV
            try:
                webdav_client.upload_file(local_path, remote_path)
                success_count += 1
            except Exception as e:
                logger.error(f"上传失败: {filename}, 错误: {e}")
                fail_count += 1
    
    logger.info(f"处理完成: 成功 {success_count}, 失败 {fail_count}")
    return fail_count == 0


def main():
    parser = argparse.ArgumentParser(description='上传STRM文件中的文件到123云盘')
    parser.add_argument('--strm-folder', required=True, help='STRM文件所在文件夹路径')
    parser.add_argument('--upload-path', required=True, help='123云盘保存路径')
    
    args = parser.parse_args()
    
    # 获取WebDAV配置
    webdav_address = os.environ.get('WEBDAV_ADDRESS')
    webdav_username = os.environ.get('WEBDAV_USERNAME')
    webdav_password = os.environ.get('WEBDAV_PASSWORD')
    
    if not all([webdav_address, webdav_username, webdav_password]):
        logger.error("请设置WebDAV环境变量: WEBDAV_ADDRESS, WEBDAV_USERNAME, WEBDAV_PASSWORD")
        sys.exit(1)
    
    # 创建WebDAV客户端
    webdav_client = WebDAVClient(webdav_address, webdav_username, webdav_password)
    
    # 检查连接
    if not webdav_client.check_connection():
        logger.error("WebDAV连接失败，请检查配置")
        sys.exit(1)
    
    logger.info("WebDAV连接成功")
    
    # 处理STRM文件
    success = process_strm_files(args.strm_folder, args.upload_path, webdav_client)
    
    if success:
        logger.info("所有文件上传成功")
        sys.exit(0)
    else:
        logger.error("部分文件上传失败")
        sys.exit(1)


if __name__ == '__main__':
    main()