# -*- coding: utf-8 -*-
"""
用户模型和管理器
"""

import os
import json
import uuid
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class User:
    """用户模型"""
    
    def __init__(self, username: str, password_hash: str, is_admin: bool = False, 
                 created_at: str = None, last_login: str = None):
        self.username = username
        self.password_hash = password_hash
        self.is_admin = is_admin
        self.created_at = created_at or datetime.now().isoformat()
        self.last_login = last_login
    
    def check_password(self, password: str) -> bool:
        """验证密码"""
        return self.password_hash == self._hash_password(password)
    
    @staticmethod
    def _hash_password(password: str) -> str:
        """密码哈希"""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'username': self.username,
            'password_hash': self.password_hash,
            'is_admin': self.is_admin,
            'created_at': self.created_at,
            'last_login': self.last_login
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'User':
        """从字典创建用户"""
        return cls(
            username=data['username'],
            password_hash=data['password_hash'],
            is_admin=data.get('is_admin', False),
            created_at=data.get('created_at'),
            last_login=data.get('last_login')
        )


class UserManager:
    """用户管理器"""
    
    def __init__(self, data_file: str = 'users.json'):
        self.data_file = data_file
        self.users: Dict[str, User] = {}
        self.sessions: Dict[str, Dict] = {}  # session_id -> {username, expires}
        self.admin_password = None
        self._load_users()
        self._ensure_admin_user()
    
    def _load_users(self):
        """加载用户数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for username, user_data in data.items():
                        self.users[username] = User.from_dict(user_data)
            except Exception as e:
                print(f"加载用户数据失败: {e}")
    
    def _save_users(self):
        """保存用户数据"""
        try:
            data = {username: user.to_dict() for username, user in self.users.items()}
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存用户数据失败: {e}")
    
    def _ensure_admin_user(self):
        """确保存在admin用户"""
        # 从环境变量获取admin密码，如果没有则生成随机密码
        admin_password = os.environ.get('ADMIN_PASSWORD')
        if not admin_password:
            admin_password = secrets.token_urlsafe(16)
            print(f"生成的admin密码: {admin_password}")
            print("请保存此密码，或通过环境变量ADMIN_PASSWORD设置自定义密码")
        
        self.admin_password = admin_password
        
        # 创建或更新admin用户
        admin_hash = User._hash_password(admin_password)
        if 'admin' not in self.users:
            self.users['admin'] = User('admin', admin_hash, is_admin=True)
        else:
            # 更新admin密码
            self.users['admin'].password_hash = admin_hash
        
        self._save_users()
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """用户认证"""
        user = self.users.get(username)
        if user and user.check_password(password):
            user.last_login = datetime.now().isoformat()
            self._save_users()
            return user
        return None
    
    def create_session(self, username: str) -> str:
        """创建会话"""
        session_id = secrets.token_urlsafe(32)
        expires = datetime.now() + timedelta(hours=24)  # 24小时过期
        self.sessions[session_id] = {
            'username': username,
            'expires': expires.isoformat()
        }
        return session_id
    
    def get_user_by_session(self, session_id: str) -> Optional[User]:
        """通过会话ID获取用户"""
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        # 检查会话是否过期
        expires = datetime.fromisoformat(session['expires'])
        if datetime.now() > expires:
            del self.sessions[session_id]
            return None
        
        return self.users.get(session['username'])
    
    def logout(self, session_id: str):
        """登出"""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def create_user(self, admin_username: str) -> Optional[Dict]:
        """创建新用户（只有admin可以创建）"""
        admin_user = self.users.get(admin_username)
        if not admin_user or not admin_user.is_admin:
            return None
        
        # 生成随机用户名和密码
        username = f"user_{secrets.token_hex(4)}"
        password = secrets.token_urlsafe(12)
        
        # 确保用户名唯一
        while username in self.users:
            username = f"user_{secrets.token_hex(4)}"
        
        # 创建用户
        password_hash = User._hash_password(password)
        self.users[username] = User(username, password_hash, is_admin=False)
        self._save_users()
        
        return {
            'username': username,
            'password': password,
            'created_at': self.users[username].created_at
        }
    
    def list_users(self, admin_username: str) -> Optional[List[Dict]]:
        """列出所有用户（只有admin可以查看）"""
        admin_user = self.users.get(admin_username)
        if not admin_user or not admin_user.is_admin:
            return None
        
        return [
            {
                'username': user.username,
                'is_admin': user.is_admin,
                'created_at': user.created_at,
                'last_login': user.last_login
            }
            for user in self.users.values()
        ]
    
    def delete_user(self, admin_username: str, target_username: str) -> bool:
        """删除用户（只有admin可以删除，不能删除admin）"""
        admin_user = self.users.get(admin_username)
        if not admin_user or not admin_user.is_admin:
            return False
        
        if target_username == 'admin':
            return False  # 不能删除admin用户
        
        if target_username in self.users:
            del self.users[target_username]
            # 删除该用户的所有会话
            sessions_to_remove = [
                sid for sid, session in self.sessions.items()
                if session['username'] == target_username
            ]
            for sid in sessions_to_remove:
                del self.sessions[sid]
            
            self._save_users()
            return True
        
        return False
    
    def cleanup_expired_sessions(self):
        """清理过期会话"""
        now = datetime.now()
        expired_sessions = [
            sid for sid, session in self.sessions.items()
            if datetime.fromisoformat(session['expires']) <= now
        ]
        for sid in expired_sessions:
            del self.sessions[sid]
