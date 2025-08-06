# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
#
import re
from pathlib import Path
from PySide6.QtCore import QObject, Slot, Signal

from module.logger import logger

# 震惊到我姥姥家 除了第一个函数all_script_files是我自己写的
# 后面的都是github copilot写的
class Add(QObject):
    
    def __init__(self) -> None:
        super(Add, self).__init__()


    @Slot(result="QVariantList")
    def all_script_files(self) -> list:
        """
        获取所有的脚本文件 除了tmplate
        :return: ['oas1', 'oas2']
        """
        # 获取某个路径的所有json文件名
        config_path = Path.cwd() / 'config'
        json_files = config_path.glob('*.json')
        result = []
        for json in json_files:
            if json.stem == 'template':
                continue
            result.append(json.stem)
        return result

    @Slot(result="QVariantList")
    def all_json_file(self) -> list:
        """
        获取所有的json文件
        :return: ['oas1', 'oas2']
        """
        # 获取某个路径的所有json文件名
        config_path = Path.cwd() / 'config'
        json_files = config_path.glob('*.json')
        result = []
        for json in json_files:
            if json.stem == 'template':
                result.insert(0, json.stem)
            else:
                result.append(json.stem)
        return result


    @Slot(str, str, result="bool")
    def copy(self, file: str, template: str = 'template') -> bool:
        """
        复制一个配置文件
        :param file:  不带json后缀
        :param template:
        :return: 是否成功
        """
        try:
            # 验证输入
            if not file or not file.strip():
                logger.error('File name cannot be empty')
                return False
                
            file = file.strip()
            config_path = Path.cwd() / 'config'
            template_path = config_path / f'{template}.json'
            file_path = config_path / f'{file}.json'
            
            if file_path.exists():
                logger.error(f'{file_path} already exists')
                return False
            
            if not template_path.exists():
                logger.error(f'Template {template_path} does not exist')
                return False

            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(template_content)
            logger.info(f'Successfully copied {template_path} to {file_path}')
            return True
        except Exception as e:
            logger.error(f'Error copying config {file}: {e}')
            return False


    @Slot(result="QString")
    def generate_script_name(self) -> str:
        """
        生成一个新的配置的名字
        :return:
        """
        all_script_files = self.all_script_files()
        if not all_script_files:
            return 'oas1'

        script_numbers = []
        for script_file in all_script_files:
            match = re.search(r'\d+', script_file)
            if match:
                script_number = int(match.group())
                script_numbers.append(script_number)

        if not script_numbers:
            return 'oas1'
        script_numbers.sort()
        new_script_number = script_numbers[-1] + 1
        return f'oas{new_script_number}'

    @Slot(str, result="bool")
    def delete_config(self, config_name: str) -> bool:
        """
        删除配置文件
        :param config_name: 配置文件名（不带.json后缀）
        :return: 删除是否成功
        """
        try:
            # 不允许删除template配置
            if config_name == 'template':
                logger.error(f'Cannot delete template config')
                return False
            
            config_path = Path.cwd() / 'config'
            file_path = config_path / f'{config_name}.json'
            
            if not file_path.exists():
                logger.error(f'{file_path} does not exist')
                return False
            
            # 检查是否是最后一个配置文件，如果是则不允许删除
            all_configs = self.all_script_files()
            if len(all_configs) <= 1:
                logger.error('Cannot delete the last config file')
                return False
            
            # 删除文件
            file_path.unlink()
            logger.info(f'Deleted config file: {file_path}')
            return True
            
        except Exception as e:
            logger.error(f'Error deleting config {config_name}: {e}')
            return False

if __name__ == "__main__":
    a = Add()
    print(a.all_script_files())
    print(a.all_json_file())
    print(a.generate_script_name())


