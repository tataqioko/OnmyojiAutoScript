#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
翻译文件备份管理器
自动备份和恢复zh_CN.ts文件，防止意外丢失
"""

import os
import shutil
import time
from datetime import datetime
from pathlib import Path

class TranslationBackupManager:
    def __init__(self):
        self.i18n_dir = Path(__file__).parent
        self.translation_file = self.i18n_dir / "zh_CN.ts"
        self.backup_dir = self.i18n_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
    def create_backup(self, suffix=""):
        """创建翻译文件的备份"""
        if not self.translation_file.exists():
            print(f"警告：翻译文件 {self.translation_file} 不存在！")
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"zh_CN_{timestamp}{suffix}.ts"
        backup_path = self.backup_dir / backup_name
        
        try:
            shutil.copy2(self.translation_file, backup_path)
            print(f"✅ 创建备份成功: {backup_path}")
            
            # 记录文件大小和行数
            with open(backup_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                line_count = len(lines)
                file_size = backup_path.stat().st_size
                
            print(f"   📊 备份信息: {line_count} 行, {file_size} 字节")
            return backup_path
            
        except Exception as e:
            print(f"❌ 创建备份失败: {e}")
            return None
    
    def list_backups(self):
        """列出所有备份文件"""
        backups = list(self.backup_dir.glob("zh_CN_*.ts"))
        backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        print("📁 可用的备份文件:")
        for i, backup in enumerate(backups, 1):
            stat = backup.stat()
            mod_time = datetime.fromtimestamp(stat.st_mtime)
            size = stat.st_size
            
            # 快速检查行数
            try:
                with open(backup, 'r', encoding='utf-8') as f:
                    line_count = sum(1 for _ in f)
            except:
                line_count = "未知"
                
            print(f"   {i}. {backup.name}")
            print(f"      时间: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"      大小: {size} 字节, {line_count} 行")
            print()
            
        return backups
    
    def restore_from_backup(self, backup_path):
        """从备份恢复翻译文件"""
        backup_path = Path(backup_path)
        if not backup_path.exists():
            print(f"❌ 备份文件不存在: {backup_path}")
            return False
            
        try:
            # 先备份当前文件（如果存在）
            if self.translation_file.exists():
                current_backup = self.create_backup("_before_restore")
                print(f"📦 当前文件已备份为: {current_backup}")
            
            # 恢复备份
            shutil.copy2(backup_path, self.translation_file)
            print(f"✅ 从备份恢复成功: {backup_path}")
            
            # 验证恢复的文件
            with open(self.translation_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                line_count = len(lines)
                
            print(f"   📊 恢复的文件: {line_count} 行")
            return True
            
        except Exception as e:
            print(f"❌ 恢复失败: {e}")
            return False
    
    def check_file_integrity(self):
        """检查翻译文件的完整性"""
        if not self.translation_file.exists():
            print("❌ 翻译文件不存在！")
            return False
            
        try:
            with open(self.translation_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 基本XML结构检查
            if not content.startswith('<?xml'):
                print("❌ 文件格式错误：不是有效的XML文件")
                return False
                
            if '<TS version=' not in content:
                print("❌ 文件格式错误：不是有效的Qt翻译文件")
                return False
                
            if not content.strip().endswith('</TS>'):
                print("❌ 文件格式错误：XML结构不完整")
                return False
                
            # 统计翻译项数量
            message_count = content.count('<message>')
            context_count = content.count('<context>')
            line_count = content.count('\n')
            
            print(f"✅ 翻译文件完整性检查通过")
            print(f"   📊 统计信息:")
            print(f"      行数: {line_count}")
            print(f"      上下文: {context_count}")
            print(f"      翻译项: {message_count}")
            
            return True
            
        except Exception as e:
            print(f"❌ 检查文件时出错: {e}")
            return False
    
    def cleanup_old_backups(self, keep_count=10):
        """清理旧的备份文件，保留最新的几个"""
        backups = list(self.backup_dir.glob("zh_CN_*.ts"))
        backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        if len(backups) <= keep_count:
            print(f"📁 当前有 {len(backups)} 个备份，无需清理")
            return
            
        to_remove = backups[keep_count:]
        print(f"🧹 清理旧备份，保留最新的 {keep_count} 个")
        
        for backup in to_remove:
            try:
                backup.unlink()
                print(f"   删除: {backup.name}")
            except Exception as e:
                print(f"   删除失败 {backup.name}: {e}")
    
    def monitor_file_changes(self):
        """监控翻译文件的变化"""
        if not self.translation_file.exists():
            print("❌ 翻译文件不存在，无法监控")
            return
            
        print(f"👁️ 开始监控翻译文件: {self.translation_file}")
        last_modified = self.translation_file.stat().st_mtime
        
        while True:
            try:
                time.sleep(5)  # 每5秒检查一次
                
                if not self.translation_file.exists():
                    print("⚠️ 警告：翻译文件已消失！")
                    # 尝试从最新备份恢复
                    backups = self.list_backups()
                    if backups:
                        print("🔄 尝试从最新备份自动恢复...")
                        if self.restore_from_backup(backups[0]):
                            print("✅ 自动恢复成功！")
                        else:
                            print("❌ 自动恢复失败！")
                    break
                    
                current_modified = self.translation_file.stat().st_mtime
                if current_modified != last_modified:
                    print(f"📝 检测到文件变化: {datetime.now()}")
                    # 创建自动备份
                    self.create_backup("_auto")
                    last_modified = current_modified
                    
            except KeyboardInterrupt:
                print("\n👋 停止监控")
                break
            except Exception as e:
                print(f"❌ 监控过程中出错: {e}")
                time.sleep(10)

def main():
    """主函数 - 命令行界面"""
    manager = TranslationBackupManager()
    
    print("🔧 翻译文件备份管理器")
    print("=" * 50)
    
    while True:
        print("\n请选择操作:")
        print("1. 创建备份")
        print("2. 列出备份")
        print("3. 从备份恢复")
        print("4. 检查文件完整性")
        print("5. 清理旧备份")
        print("6. 监控文件变化")
        print("0. 退出")
        
        choice = input("\n请输入选择 (0-6): ").strip()
        
        if choice == "0":
            print("👋 再见！")
            break
        elif choice == "1":
            manager.create_backup()
        elif choice == "2":
            manager.list_backups()
        elif choice == "3":
            backups = manager.list_backups()
            if backups:
                try:
                    index = int(input("请输入备份编号: ")) - 1
                    if 0 <= index < len(backups):
                        manager.restore_from_backup(backups[index])
                    else:
                        print("❌ 无效的备份编号")
                except ValueError:
                    print("❌ 请输入有效的数字")
        elif choice == "4":
            manager.check_file_integrity()
        elif choice == "5":
            try:
                keep = int(input("保留多少个最新备份 (默认10): ") or "10")
                manager.cleanup_old_backups(keep)
            except ValueError:
                print("❌ 请输入有效的数字")
        elif choice == "6":
            manager.monitor_file_changes()
        else:
            print("❌ 无效的选择，请重试")

if __name__ == "__main__":
    main()