# -*- coding: utf-8 -*-
"""
文件管理工具模块 - 优化版本
"""

import os
import shutil
import zipfile
import tempfile
import mimetypes
import base64
import urllib.parse
import hashlib
import time
from flask import send_from_directory, send_file, jsonify
from functools import lru_cache


class FileManager:
    """文件管理器类 - 优化版本"""
    
    def __init__(self, filter_enabled=True, env_dir_name=".conda"):
        self.filter_enabled = filter_enabled
        self.env_dir_name = env_dir_name
        # 文件预览缓存
        self._preview_cache = {}
        self._cache_max_size = 50  # 最大缓存文件数
        self._max_preview_size = 10 * 1024 * 1024  # 10MB 最大预览文件大小
        
        # 支持的文件类型扩展
        self.text_extensions = {
            '.py', '.js', '.html', '.css', '.json', '.xml', '.yaml', '.yml',
            '.txt', '.md', '.log', '.csv', '.tsv', '.sql', '.sh', '.bat',
            '.ini', '.cfg', '.conf', '.properties', '.gitignore', '.dockerfile',
            '.vue', '.jsx', '.tsx', '.scss', '.less', '.sass', '.php', '.rb',
            '.go', '.rs', '.cpp', '.c', '.h', '.hpp', '.java', '.kt', '.swift'
        }
        
        self.image_extensions = {
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.ico',
            '.tiff', '.tif', '.psd', '.raw', '.heic', '.avif'
        }
        
        self.video_extensions = {
            '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv', '.m4v',
            '.3gp', '.ogv', '.ts', '.mts', '.m2ts'
        }
        
        self.audio_extensions = {
            '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.opus'
        }
    
    def get_directory_listing(self, root_path, sort='default'):
        """获取目录列表 - 平铺展示版本"""
        items = []
        try:
            # 添加返回上级目录的选项（如果不是根目录）
            abs_root = os.path.abspath(root_path)
            abs_base = os.path.abspath('.')
            
            if abs_root != abs_base:
                parent_item = {
                    'name': '..',
                    'is_dir': True,
                    'size': 0,
                    'modified': 0,
                    'path': os.path.dirname(abs_root),
                    'file_type': 'parent',
                    'is_parent': True
                }
                items.append(parent_item)
            
            entries = list(os.scandir(root_path))
            
            for entry in entries:
                # 过滤特定目录和隐藏文件
                if self.filter_enabled and (
                    entry.name == self.env_dir_name or 
                    entry.name.startswith('.') and entry.name not in {'.gitignore', '.env'}
                ):
                    continue
                
                try:
                    stat_info = entry.stat()
                    item = {
                        'name': entry.name,
                        'is_dir': entry.is_dir(),
                        'size': stat_info.st_size if not entry.is_dir() else 0,
                        'modified': stat_info.st_mtime,
                        'path': entry.path,
                        'relative_path': os.path.relpath(entry.path, abs_base)
                    }
                    
                    if entry.is_dir():
                        item['file_type'] = 'folder'
                        item['has_children'] = self._has_children(entry.path)
                    else:
                        # 添加文件类型信息
                        item['file_type'] = self._get_file_type(entry.name)
                        item['preview_supported'] = self._is_preview_supported(entry.name, stat_info.st_size)
                        item['editable'] = self._is_text_editable(entry.name, stat_info.st_size)
                    
                    items.append(item)
                    
                except (OSError, PermissionError):
                    # 跳过无法访问的文件
                    continue
                    
        except PermissionError:
            pass  # 忽略权限错误
        
        # 排序优化
        return self._sort_items(items, sort)
    
    def _is_text_editable(self, filename, file_size):
        """检查文件是否可编辑"""
        # 文件大小限制（1MB以内可编辑）
        if file_size > 1024 * 1024:
            return False
        
        ext = os.path.splitext(filename)[1].lower()
        return ext in self.text_extensions
    
    def _sort_items(self, items, sort_type):
        """排序文件列表"""
        # 将父目录(..)始终放在最前面
        parent_items = [item for item in items if item.get('is_parent', False)]
        regular_items = [item for item in items if not item.get('is_parent', False)]
        
        if sort_type == 'name':
            regular_items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
        elif sort_type == 'size':
            regular_items.sort(key=lambda x: (not x['is_dir'], -x.get('size', 0)))
        elif sort_type == 'modified':
            regular_items.sort(key=lambda x: (not x['is_dir'], -x.get('modified', 0)))
        else:  # default
            regular_items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
        
        return parent_items + regular_items
    
    def _has_children(self, dir_path):
        """检查目录是否有子项"""
        try:
            for _ in os.scandir(dir_path):
                return True
            return False
        except (OSError, PermissionError):
            return False
    
    def _get_file_type(self, filename):
        """获取文件类型"""
        ext = os.path.splitext(filename)[1].lower()
        if ext in self.text_extensions:
            return 'text'
        elif ext in self.image_extensions:
            return 'image'
        elif ext in self.video_extensions:
            return 'video'
        elif ext in self.audio_extensions:
            return 'audio'
        else:
            return 'other'
    
    def _is_preview_supported(self, filename, file_size):
        """检查文件是否支持预览"""
        if file_size > self._max_preview_size:
            return False
        
        ext = os.path.splitext(filename)[1].lower()
        return ext in (self.text_extensions | self.image_extensions | self.video_extensions)
    
    def _sort_tree(self, tree, sort_type):
        """排序文件树"""
        if sort_type == 'name':
            tree.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
        elif sort_type == 'size':
            tree.sort(key=lambda x: (not x['is_dir'], -x.get('size', 0)))
        elif sort_type == 'modified':
            tree.sort(key=lambda x: (not x['is_dir'], -x.get('modified', 0)))
        else:  # default
            tree.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
        
        # 递归排序子目录
        for node in tree:
            if node['is_dir'] and 'children' in node:
                node['children'] = self._sort_tree(node['children'], sort_type)
        
        return tree
    
    def preview_file(self, file_path):
        """预览文件内容 - 优化版本"""
        abs_path = os.path.abspath(file_path)
        
        # 安全检查：防止越权访问
        if not abs_path.startswith(os.path.abspath('.')):
            return {'error': 'Permission denied'}, 403
        
        if not os.path.isfile(abs_path):
            return {'error': 'Not a file'}, 404
        
        # 文件大小检查
        file_size = os.path.getsize(abs_path)
        if file_size > self._max_preview_size:
            return {
                'error': f'File too large for preview (max {self._max_preview_size // 1024 // 1024}MB)',
                'size': file_size
            }, 413
        
        # 检查缓存
        file_hash = self._get_file_hash(abs_path)
        if file_hash in self._preview_cache:
            cache_entry = self._preview_cache[file_hash]
            if cache_entry['mtime'] == os.path.getmtime(abs_path):
                return cache_entry['content'], 200
        
        # 获取MIME类型
        mime, _ = mimetypes.guess_type(abs_path)
        if not mime:
            mime = 'application/octet-stream'
        
        try:
            result = None
            
            # 文本文件处理
            if self._is_text_file(abs_path, mime):
                result = self._preview_text_file(abs_path, file_size)
            
            # 图片文件处理
            elif mime.startswith('image'):
                result = self._preview_image_file(abs_path, mime, file_size)
            
            # 视频文件处理
            elif mime.startswith('video'):
                result = self._preview_video_file(abs_path, mime, file_size)
            
            # 音频文件处理
            elif mime.startswith('audio'):
                result = self._preview_audio_file(abs_path, mime, file_size)
            
            else:
                result = {
                    'type': 'other',
                    'mime': mime,
                    'size': file_size,
                    'message': 'Preview not supported for this file type'
                }
            
            # 缓存结果
            if result and result.get('type') != 'error':
                self._cache_preview(file_hash, abs_path, result)
            
            return result, 200
                
        except Exception as e:
            return {'error': str(e), 'type': 'error'}, 500
    
    def _get_file_hash(self, file_path):
        """获取文件哈希值用于缓存"""
        stat = os.stat(file_path)
        return hashlib.md5(f"{file_path}:{stat.st_size}:{stat.st_mtime}".encode()).hexdigest()
    
    def _is_text_file(self, file_path, mime):
        """判断是否为文本文件"""
        ext = os.path.splitext(file_path)[1].lower()
        return (mime.startswith('text') or 
                ext in self.text_extensions or
                mime in {'application/json', 'application/xml', 'application/javascript'})
    
    def _preview_text_file(self, file_path, file_size):
        """预览文本文件"""
        # 大文件只读取前部分
        max_chars = 100000  # 最大字符数
        
        try:
            # 尝试不同编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin1']
            content = None
            used_encoding = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        if file_size > max_chars:
                            content = f.read(max_chars)
                            truncated = True
                        else:
                            content = f.read()
                            truncated = False
                    used_encoding = encoding
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                return {'error': 'Unable to decode file', 'type': 'error'}
            
            # 检测编程语言
            ext = os.path.splitext(file_path)[1].lower()
            language = self._detect_language(ext)
            
            return {
                'type': 'text',
                'content': content,
                'encoding': used_encoding,
                'language': language,
                'truncated': truncated if file_size > max_chars else False,
                'size': file_size,
                'lines': content.count('\n') + 1
            }
            
        except Exception as e:
            return {'error': str(e), 'type': 'error'}
    
    def _preview_image_file(self, file_path, mime, file_size):
        """预览图片文件"""
        try:
            # 大图片文件警告
            if file_size > 5 * 1024 * 1024:  # 5MB
                return {
                    'type': 'image',
                    'size': file_size,
                    'warning': 'Large image file, preview may be slow',
                    'url': f'/api/file_content?path={urllib.parse.quote(file_path)}'
                }
            
            with open(file_path, 'rb') as f:
                b64 = base64.b64encode(f.read()).decode('utf-8')
            
            return {
                'type': 'image',
                'content': b64,
                'mimetype': mime,
                'size': file_size
            }
            
        except Exception as e:
            return {'error': str(e), 'type': 'error'}
    
    def _preview_video_file(self, file_path, mime, file_size):
        """预览视频文件"""
        # 视频文件不直接加载到内存，返回URL
        return {
            'type': 'video',
            'mimetype': mime,
            'size': file_size,
            'url': f'/api/file_content?path={urllib.parse.quote(file_path)}'
        }
    
    def _preview_audio_file(self, file_path, mime, file_size):
        """预览音频文件"""
        return {
            'type': 'audio',
            'mimetype': mime,
            'size': file_size,
            'url': f'/api/file_content?path={urllib.parse.quote(file_path)}'
        }
    
    def _detect_language(self, ext):
        """检测编程语言"""
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.json': 'json',
            '.xml': 'xml',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.md': 'markdown',
            '.sql': 'sql',
            '.sh': 'bash',
            '.bat': 'batch',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.cpp': 'cpp',
            '.c': 'c',
            '.java': 'java',
            '.kt': 'kotlin',
            '.swift': 'swift'
        }
        return language_map.get(ext, 'text')
    
    def _cache_preview(self, file_hash, file_path, content):
        """缓存预览内容"""
        # 清理旧缓存
        if len(self._preview_cache) >= self._cache_max_size:
            # 移除最旧的缓存项
            oldest_key = min(self._preview_cache.keys(), 
                           key=lambda k: self._preview_cache[k]['timestamp'])
            del self._preview_cache[oldest_key]
        
        self._preview_cache[file_hash] = {
            'content': content,
            'mtime': os.path.getmtime(file_path),
            'timestamp': time.time()
        }
    
    def get_file_content(self, file_path):
        """获取文件内容（用于大文件流式传输）"""
        abs_path = os.path.abspath(file_path)
        
        # 安全检查
        if not abs_path.startswith(os.path.abspath('.')):
            return None, 'Permission denied', 403
        
        if not os.path.isfile(abs_path):
            return None, 'Not a file', 404
        
        try:
            return send_file(abs_path), None, 200
        except Exception as e:
            return None, str(e), 500
    
    def download_file(self, file_path):
        """下载单个文件"""
        abs_path = os.path.abspath(file_path)
        
        # 安全检查
        if not abs_path.startswith(os.path.abspath('.')):
            return None, 'Permission denied', 403
        
        if not os.path.isfile(abs_path):
            return None, 'Not a file', 404
        
        dir_name = os.path.dirname(abs_path)
        file_name = os.path.basename(abs_path)
        
        return send_from_directory(dir_name, file_name, as_attachment=True), None, 200
    
    def download_folder(self, folder_path):
        """下载文件夹（压缩为ZIP）"""
        abs_path = os.path.abspath(folder_path)
        
        # 安全检查
        if not abs_path.startswith(os.path.abspath('.')):
            return None, 'Permission denied', 403
        
        if not os.path.isdir(abs_path):
            return None, 'Not a folder', 404
        
        # 创建临时ZIP文件
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        zip_path = tmp.name
        tmp.close()
        
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(abs_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, abs_path)
                        zf.write(file_path, arcname)
            
            download_name = os.path.basename(abs_path) + '.zip'
            return send_file(zip_path, as_attachment=True, download_name=download_name), None, 200
            
        except Exception as e:
            return None, str(e), 500
    
    def upload_files(self, files, target_path='.'):
        """上传文件"""
        abs_path = os.path.abspath(target_path)
        
        # 安全检查
        if not abs_path.startswith(os.path.abspath('.')):
            return {'success': False, 'error': 'Permission denied'}
        
        if not os.path.isdir(abs_path):
            return {'success': False, 'error': 'Not a folder'}
        
        if not files:
            return {'success': False, 'error': 'No files'}
        
        try:
            uploaded_files = []
            for f in files:
                save_path = os.path.join(abs_path, f.filename)
                f.save(save_path)
                uploaded_files.append(f.filename)
            
            return {'success': True, 'files': uploaded_files}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def delete_file_or_folder(self, path, file_type):
        """删除文件或文件夹"""
        # 路径解码
        path = urllib.parse.unquote(path)
        
        try:
            if file_type == 'folder':
                if os.path.exists(path):
                    shutil.rmtree(path)
                    return {'success': True}
                else:
                    return {'success': False, 'error': '文件夹不存在'}
            else:
                if os.path.exists(path):
                    os.remove(path)
                    return {'success': True}
                else:
                    return {'success': False, 'error': '文件不存在'}
                    
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def clear_cache(self):
        """清理预览缓存"""
        self._preview_cache.clear()
    
    def get_cache_stats(self):
        """获取缓存统计信息"""
        return {
            'cache_size': len(self._preview_cache),
            'max_size': self._cache_max_size,
            'max_preview_size': self._max_preview_size
        }
    
    def edit_file(self, file_path):
        """获取文件内容用于编辑"""
        abs_path = os.path.abspath(file_path)
        
        # 安全检查：防止越权访问
        if not abs_path.startswith(os.path.abspath('.')):
            return {'error': 'Permission denied'}, 403
        
        if not os.path.isfile(abs_path):
            return {'error': 'Not a file'}, 404
        
        # 文件大小检查（编辑限制为1MB）
        file_size = os.path.getsize(abs_path)
        if file_size > 1024 * 1024:
            return {
                'error': 'File too large for editing (max 1MB)',
                'size': file_size
            }, 413
        
        # 检查是否为文本文件
        ext = os.path.splitext(abs_path)[1].lower()
        if ext not in self.text_extensions:
            return {'error': 'File type not supported for editing'}, 422
        
        try:
            # 尝试不同编码读取文件
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin1']
            content = None
            used_encoding = None
            
            for encoding in encodings:
                try:
                    with open(abs_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    used_encoding = encoding
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                return {'error': 'Unable to decode file'}, 422
            
            # 获取文件信息
            stat_info = os.stat(abs_path)
            language = self._detect_language(ext)
            
            return {
                'content': content,
                'encoding': used_encoding,
                'language': language,
                'size': file_size,
                'lines': content.count('\n') + 1,
                'modified': stat_info.st_mtime,
                'readonly': not os.access(abs_path, os.W_OK)
            }, 200
            
        except Exception as e:
            return {'error': str(e)}, 500
    
    def save_file(self, file_path, content, encoding='utf-8'):
        """保存文件内容"""
        abs_path = os.path.abspath(file_path)
        
        # 安全检查：防止越权访问
        if not abs_path.startswith(os.path.abspath('.')):
            return {'error': 'Permission denied'}, 403
        
        # 检查是否为文本文件
        ext = os.path.splitext(abs_path)[1].lower()
        if ext not in self.text_extensions:
            return {'error': 'File type not supported for editing'}, 422
        
        try:
            # 创建备份（如果文件存在）
            backup_path = None
            if os.path.exists(abs_path):
                backup_path = abs_path + '.backup'
                shutil.copy2(abs_path, backup_path)
            
            # 保存文件
            with open(abs_path, 'w', encoding=encoding) as f:
                f.write(content)
            
            # 获取新的文件信息
            stat_info = os.stat(abs_path)
            
            # 清理相关缓存
            file_hash = self._get_file_hash(abs_path)
            if file_hash in self._preview_cache:
                del self._preview_cache[file_hash]
            
            return {
                'success': True,
                'size': stat_info.st_size,
                'modified': stat_info.st_mtime,
                'lines': content.count('\n') + 1,
                'backup_created': backup_path is not None
            }, 200
            
        except Exception as e:
            # 如果保存失败且有备份，尝试恢复
            if backup_path and os.path.exists(backup_path):
                try:
                    shutil.move(backup_path, abs_path)
                except:
                    pass
            return {'error': str(e)}, 500
    
    def create_file(self, file_path, content='', encoding='utf-8'):
        """创建新文件"""
        abs_path = os.path.abspath(file_path)
        
        # 安全检查：防止越权访问
        if not abs_path.startswith(os.path.abspath('.')):
            return {'error': 'Permission denied'}, 403
        
        # 检查文件是否已存在
        if os.path.exists(abs_path):
            return {'error': 'File already exists'}, 409
        
        # 检查是否为文本文件
        ext = os.path.splitext(abs_path)[1].lower()
        if ext not in self.text_extensions:
            return {'error': 'File type not supported for editing'}, 422
        
        try:
            # 确保目录存在
            dir_path = os.path.dirname(abs_path)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
            
            # 创建文件
            with open(abs_path, 'w', encoding=encoding) as f:
                f.write(content)
            
            # 获取文件信息
            stat_info = os.stat(abs_path)
            
            return {
                'success': True,
                'size': stat_info.st_size,
                'modified': stat_info.st_mtime,
                'lines': content.count('\n') + 1
            }, 200
            
        except Exception as e:
            return {'error': str(e)}, 500
