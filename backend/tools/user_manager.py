#!/usr/bin/env python3
"""用户管理工具 - 用于手动添加和管理用户"""
import sys
from pathlib import Path
import argparse

# 添加backend目录到路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from db import Database, User
from config.settings import DB_FILE


class UserManager:
    """用户管理工具类"""
    
    def __init__(self):
        self.db = Database(DB_FILE)
        self.user_model = User(self.db)
    
    def add_user(self, username: str, password: str, email: str = None, is_guest: bool = False, role: str = 'user'):
        """
        添加新用户
        
        Args:
            username: 用户名
            password: 原始密码（将自动哈希）
            email: 邮箱（可选）
            is_guest: 是否为游客账号
            role: 用户角色 (guest/user/admin)
        
        Returns:
            str: 用户ID，如果失败返回None
        """
        try:
            # 检查用户名是否已存在
            existing_user = self.user_model.get_by_username(username)
            if existing_user:
                print(f"✗ 错误: 用户名 '{username}' 已存在")
                return None
            
            # 验证角色
            if role not in ['guest', 'user', 'admin']:
                print(f"✗ 错误: 无效的角色 '{role}'，必须是 guest/user/admin 之一")
                return None
            
            # 创建用户
            user_id = self.user_model.create(
                username=username,
                password=password,
                email=email,
                is_guest=is_guest,
                role=role
            )
            
            if user_id:
                role_display = {'guest': '游客', 'user': '普通用户', 'admin': '管理员'}.get(role, role)
                print(f"✓ 成功创建用户:")
                print(f"  - 用户ID: {user_id}")
                print(f"  - 用户名: {username}")
                print(f"  - 邮箱: {email or '未设置'}")
                print(f"  - 角色: {role_display}")
                return user_id
            else:
                print("✗ 创建用户失败")
                return None
                
        except Exception as e:
            print(f"✗ 创建用户时发生错误: {e}")
            return None
    
    def list_users(self):
        """列出所有用户"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT user_id, username, email, is_guest, role, created_at, last_login
                    FROM users
                    ORDER BY created_at DESC
                """)
                
                users = cursor.fetchall()
                
                if not users:
                    print("数据库中没有用户")
                    return
                
                print(f"\n共有 {len(users)} 个用户:\n")
                print(f"{'用户ID':<38} {'用户名':<20} {'邮箱':<30} {'角色':<10} {'创建时间':<20}")
                print("-" * 130)
                
                for user in users:
                    user_id, username, email, is_guest, role, created_at, last_login = user
                    role_display = {'guest': '游客', 'user': '普通用户', 'admin': '管理员'}.get(role or 'user', role or 'user')
                    email_display = email or "-"
                    print(f"{user_id:<38} {username:<20} {email_display:<30} {role_display:<10} {created_at:<20}")
            
        except Exception as e:
            print(f"✗ 列出用户时发生错误: {e}")
    
    def delete_user(self, username: str):
        """
        删除用户
        
        Args:
            username: 要删除的用户名
        """
        try:
            user = self.user_model.get_by_username(username)
            if not user:
                print(f"✗ 用户 '{username}' 不存在")
                return False
            
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # 删除用户
                cursor.execute("DELETE FROM users WHERE username = ?", (username,))
                conn.commit()
            
            print(f"✓ 已删除用户: {username}")
            return True
            
        except Exception as e:
            print(f"✗ 删除用户时发生错误: {e}")
            return False
    
    def update_password(self, username: str, new_password: str):
        """
        更新用户密码
        
        Args:
            username: 用户名
            new_password: 新密码（原始密码，将自动哈希）
        """
        try:
            user = self.user_model.get_by_username(username)
            if not user:
                print(f"✗ 用户 '{username}' 不存在")
                return False
            
            success = self.user_model.update_password(username, new_password)
            
            if success:
                print(f"✓ 已更新用户 '{username}' 的密码")
                return True
            else:
                print(f"✗ 更新密码失败")
                return False
                
        except Exception as e:
            print(f"✗ 更新密码时发生错误: {e}")
            return False


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description='Easy-BabelDOC 用户管理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 添加新用户
  python user_manager.py add --username admin --password 123456 --email admin@example.com
  
  # 列出所有用户
  python user_manager.py list
  
  # 删除用户
  python user_manager.py delete --username guest_12345678
  
  # 更新密码
  python user_manager.py passwd --username admin --password new_password
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 添加用户命令
    add_parser = subparsers.add_parser('add', help='添加新用户')
    add_parser.add_argument('--username', required=True, help='用户名')
    add_parser.add_argument('--password', required=True, help='密码')
    add_parser.add_argument('--email', help='邮箱（可选）')
    add_parser.add_argument('--guest', action='store_true', help='创建为游客账号')
    add_parser.add_argument('--role', choices=['guest', 'user', 'admin'], default='user', help='用户角色 (guest/user/admin)')
    
    # 列出用户命令
    subparsers.add_parser('list', help='列出所有用户')
    
    # 删除用户命令
    delete_parser = subparsers.add_parser('delete', help='删除用户')
    delete_parser.add_argument('--username', required=True, help='要删除的用户名')
    
    # 更新密码命令
    passwd_parser = subparsers.add_parser('passwd', help='更新用户密码')
    passwd_parser.add_argument('--username', required=True, help='用户名')
    passwd_parser.add_argument('--password', required=True, help='新密码')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = UserManager()
    
    if args.command == 'add':
        manager.add_user(
            username=args.username,
            password=args.password,
            email=args.email,
            is_guest=args.guest,
            role=args.role
        )
    
    elif args.command == 'list':
        manager.list_users()
    
    elif args.command == 'delete':
        confirm = input(f"确定要删除用户 '{args.username}' 吗? (yes/no): ")
        if confirm.lower() in ['yes', 'y']:
            manager.delete_user(args.username)
        else:
            print("已取消")
    
    elif args.command == 'passwd':
        manager.update_password(args.username, args.password)


if __name__ == "__main__":
    main()
