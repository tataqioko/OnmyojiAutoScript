# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey

import json

from module.config.config import Config
from module.config.utils import convert_to_underscore
from module.config.config_model import ConfigModel

from module.logger import logger
from pydantic import BaseModel, ValidationError



class ConfigModify(Config):
    """
    这个类的出现是为了修补一个架构问题：
    不同于Alas,我默认用户在GUI界面点击的时候就启动了脚本进程，初始化会直接同时初始化一个config和一个device
    如果用户配置不对这个进程直接挂掉了，用户甚至没有修改config的机会，即时重启了也会由于没有修改config而再次挂掉

    因此这个类的出现是为了在脚本进程挂掉的时候，用户可以修改config，然后再次启动脚本进程


    """

    def __init__(self, config: str) -> None:
        super().__init__(config)


    def gui_args(self, task: str) -> str:
        """
        获取给gui显示的参数
        :return:
        """
        return super().gui_args(task=task)

    def gui_task(self, task: str) -> str:
        """
        获取给gui显示的任务 的参数的具体值
        :return:
        """
        return self.model.gui_task(task=task)

    def gui_set_task(self, task: str, group: str, argument: str, value) -> bool:
        """
        设置给gui显示的任务 的参数的具体值
        :return:
        """
        task = convert_to_underscore(task)
        group = convert_to_underscore(group)
        argument = convert_to_underscore(argument)

        path = f'{task}.{group}.{argument}'
        task_object = getattr(self.model, task, None)
        group_object = getattr(task_object, group, None)
        argument_object = getattr(group_object, argument, None)

        if argument_object is None:
            logger.error(f'gui_set_task {task}.{group}.{argument}.{value} failed')
            return False

        try:
            setattr(group_object, argument, value)
            argument_object = getattr(group_object, argument, None)
            logger.info(f'gui_set_task {task}.{group}.{argument}.{argument_object}')
            super().save()  # 我是没有想到什么方法可以使得属性改变自动保存的
            return True
        except ValidationError as e:
            logger.error(e)
            return False

    def gui_task_list(self) -> str:
        """
        获取给gui显示的任务列表
        :return:
        """
        result = {}
        for key, value in self.model.model_dump().items():
            if isinstance(value, str):
                continue
            if key == "restart":
                continue
            if "scheduler" not in value:
                continue

            scheduler = value["scheduler"]
            item = {"enable": scheduler["enable"],
                    "next_run": str(scheduler["next_run"])}
            key = self.model.type(key)
            result[key] = item
        return json.dumps(result)

    def gui_run_task_immediately(self, task: str) -> bool:
        """
        立即运行指定的任务，无视调度时间
        :param task: 任务名称（可以是显示名、大驼峰名或下划线格式）
        :return: 成功返回True，失败返回False
        """
        try:
            logger.info(f'ConfigModify requesting immediate run of task: {task}')
            
            # 如果传入的是显示名（中文），需要反向查找到内部名称
            internal_task_name = self._find_internal_task_name(task)
            if internal_task_name:
                task = internal_task_name
                logger.info(f'Resolved display name to internal task: {internal_task_name}')
            
            result = self.task_call(task, force_call=True, immediate=True)
            if result:
                logger.info(f'Task {task} scheduled for immediate execution via ConfigModify')
            else:
                logger.warning(f'Failed to schedule immediate execution for task {task} via ConfigModify')
            return result
        except Exception as e:
            logger.error(f'Error in ConfigModify.gui_run_task_immediately for task {task}: {e}')
            return False
    
    def _find_internal_task_name(self, display_task_name: str) -> str:
        """
        根据显示名称查找内部任务名称
        :param display_task_name: 显示名称（中文或英文）
        :return: 内部下划线格式的任务名称，找不到返回None
        """
        try:
            # 先检查是否已经是正确的格式
            if hasattr(self.model, display_task_name):
                return display_task_name
            
            # 检查是否是大驼峰格式，尝试转换为下划线格式
            underscore_name = convert_to_underscore(display_task_name)
            if hasattr(self.model, underscore_name):
                return underscore_name
            
            # 反向查找：遍历所有任务，比较显示名称
            for attr_name in dir(self.model):
                if not attr_name.startswith('_'):
                    try:
                        attr_obj = getattr(self.model, attr_name)
                        if hasattr(attr_obj, 'scheduler'):
                            # 获取这个任务的显示名称
                            class_name = self.model.type(attr_name)
                            if class_name == display_task_name:
                                return attr_name
                    except:
                        continue
            
            logger.warning(f'Could not find internal task name for display name: {display_task_name}')
            return None
            
        except Exception as e:
            logger.error(f'Error in _find_internal_task_name for {display_task_name}: {e}')
            return None
