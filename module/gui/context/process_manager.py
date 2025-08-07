# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
import socket
import random
import zerorpc
import asyncio
import cv2
import msgpack
import numpy as np
import io
import json

from typing import Union, Any, Dict
from cached_property import cached_property
from PySide6.QtCore import QObject, Slot, Signal, Property
from PySide6.QtGui import QImage
from queue import Queue, Empty
from rich.console import Console
from multiprocessing.managers import SyncManager
# from multiprocessing import Queue
from threading import Thread

from module.base.log_highlighter import highlight_text
from module.gui.process.script_process import ScriptProcess
from module.config.config_menu import ConfigMenu
from module.config.config_modify import ConfigModify
from module.gui.context.add import Add
from module.logger import logger


def is_port_in_use(ip, port) -> bool:
    """
    检查端口是否被占用
    :param ip:
    :param port:
    :return:
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, port))
        s.shutdown(2)
        logger.info(f'Port {port} is in use')
        return True
    except:
        logger.info(f'Port {port} is not in use')
        return False




class ProcessManager(QObject):
    """
    进程管理
    """
    log_signal = Signal(str, str)  # 日志信号
    sig_update_task = Signal(str, str)  # 更新当前运行的任务任务信号
    sig_update_pending = Signal(str, str)  # 更新等待运行的任务信号
    sig_update_waiting = Signal(str, str)  # 更新等待运行的任务信号

    def __init__(self) -> None:
        """
        init
        """
        super().__init__()
        self.processes: Dict[str, ScriptProcess] = {}  # 持有所有的进程
        self.configs: Dict[str, ConfigModify] = {}  # 持有所有的配置, 权宜之计
        self.ports: Dict[str, int] = {}  # 持有所有的端口
        self.clients = {}  # zerorpc连接的客户端

        self.manager = SyncManager()  # 管理器
        self.manager.start()
        self.log_queue: Dict[str, Queue] = {}  # 日志队列
        self.log_thread: Dict[str, Thread] = {}  # 日志线程

        self.update_queue: Queue = None  # 每次更新任务的时候push进来给gui显示
        self.update_thread: Thread = None  # 更新线程
        self.start_update_tasks()  # 启动更新线程

        # self.event_loop = asyncio.get_event_loop()  # 事件循环



    @Slot()
    def create_all(self) -> None:
        """
        创建所有的配置实例
        :return:
        """
        configs = Add().all_script_files()
        for config in configs:
            self.add(config)

    @Slot(str)
    def add(self, config: str) -> None:
        """
        add
        :param config: 如oas1
        :return:
        """
        if config not in self.processes:
            # 初始化端口
            port = 40000 + random.randint(0, 200)
            while is_port_in_use('127.0.0.1', port):
                port = 40000 + random.randint(0, 200)
            self.ports[config] = port
            # 初始化日志队列
            q = self.start_log(config)

            # 初始化启动进程
            self.processes[config] = ScriptProcess(config, port, q, update_queue=self.update_queue)
            self.log_thread[config].start()

            # 下面是启动 zerorpc 客户端
            logger.info(f'Create script {config} on port {port}')
            try:
                self.clients[config] = zerorpc.Client()
                self.clients[config].connect(f'tcp://127.0.0.1:{self.ports[config]}')
            except:
                logger.exception(f'Connect to script {config} error')
                raise
            self.processes[config].start()
            logger.info(f'Add script {config}')
        else:
            logger.info(f'Script {config} is already running')

    def remove(self, config: str) -> None:
        """
        remove
        :param config:
        :return:
        """
        if config in self.processes:
            self.processes[config].stop()
            del self.processes[config]
            del self.ports[config]
            del self.clients[config]
            logger.info(f'Remove script {config}')
            logger.info(f'Port {config} is released')
        else:
            logger.info(f'Script {config} is not running')

    @Slot(str)
    def restart(self, config: str) -> None:
        """
        restart  重启某个进程（会重启zerorpc），但是ports、clients、log_queue、log_thread不会重启
        :param config:
        :return:
        """
        if config in self.processes:
            if not self.processes[config].is_alive():  # 如果进程已经死亡，那么就重新启动
                logger.info(f'{config} process is dead, restart it')


            self.processes[config].terminate()  # 强制结束进程
            if self.ports[config] is None:
                logger.error(f'{config} port {config} is None')
            if self.clients[config] is None:
                logger.error(f'{config} client {config} is None')
            if self.log_queue[config] is None:
                logger.info(f'{config} log_queue {config} is None')
                self.log_queue[config] = self.manager.Queue()
            if self.log_thread[config] is None or self.log_thread[config].is_alive() is False:
                logger.info(f'{config} log_thread {config} is None')

            self.processes[config] = ScriptProcess(config=config,
                                                   port=self.ports[config],
                                                   log_queue=self.log_queue[config],
                                                   update_queue=self.update_queue)
            self.processes[config].start()
            logger.info(f'Restart script {config}')
        else:
            logger.info(f'Script {config} is not running')

    def stop_all(self) -> None:
        """
        stop_all
        :return:
        """
        for config in self.processes:
            self.processes[config].stop()
        logger.info(f'Stop all script')

    def restart_all(self) -> None:
        """
        restart_all
        :return:
        """
        for config in self.processes:
            self.processes[config].restart()
        logger.info(f'Restart all script')

    def get_client(self, config: str) -> zerorpc.Client:
        """
        get_client
        :param config:
        :return:
        """
        if config in self.clients:
            return self.clients[config]
        else:
            logger.info(f'Script {config} is not running')
            return None

    @Slot(result="QString")
    def gui_menu(self) -> str:
        """
        get_gui_menu
        :param config:
        :return:
        """
        menu = ConfigMenu()
        return menu.gui_menu

    def check_script(self, config: str):
        """
        检查脚本是否存在
        :param config:
        :return:
        """
        if config in self.processes and self.processes[config].is_alive():  # 如果脚本进程存在
            if config in self.configs:
                del self.configs[config]
            return self.clients[config]
        else:
            if config not in self.configs:
                self.configs[config] = ConfigModify(config)  # 初始化一个
            return self.configs[config]

    @Slot(str, str, result="QString")
    def gui_args(self, config: str, task: str) -> str:
        """
        获取显示task的gui参数
        :param config:
        :param task:
        :return:
        """
        if config in self.clients:
            logger.info(f'Gui get args of {config} {task}')
            return self.check_script(config).gui_args(task)
        else:
            logger.info(f'Script {config} is not running')
            return None

    @Slot(str, str, result="QString")
    def gui_task(self, config: str, task: str) -> str:
        """
        获取显示task的gui
        :param config:
        :param task:
        :return:
        """
        if config in self.clients:
            logger.info(f'Gui get value of {config} {task}')
            return self.check_script(config).gui_task(task)
        else:
            logger.info(f'Script {config} is not running')
            return None

    @Slot(str, str, str, str, str, result="bool")
    def gui_set_task(self, config: str, task: str, group: str, arg: str, value) -> bool:
        """
        设置task的gui   是string类型的
        :param config:
        :param task:
        :param group:
        :param arg:
        :param value:
        :return:
        """
        if config in self.clients:
            logger.info(f'Gui set value of {config} {task}')
            if self.check_script(config).gui_set_task(task, group, arg, value):
                return True
            else:
                return False
        else:
            logger.info(f'Script {config} is not running')
            return False

    @Slot(str, str, str, str, bool, result="bool")
    def gui_set_task_bool(self, config: str, task: str, group: str, arg: str, value: bool) -> bool:
        """
        设置task的gui   是bool类型的
        :param config:
        :param task:
        :param group:
        :param arg:
        :param value:
        :return:
        """
        if config in self.clients:
            logger.info(f'Gui set value of {config} {task}')
            if self.check_script(config).gui_set_task(task, group, arg, value):
                return True
            else:
                return False
        else:
            logger.info(f'Script {config} is not running')
            return False

    @Slot(str, str, str, str, float, result="bool")
    def gui_set_task_number(self, config: str, task: str, group: str, arg: str, value) -> bool:
        """
        设置task的gui   是float类型的或者是int
        :param config:
        :param task:
        :param group:
        :param arg:
        :param value:
        :return:
        """
        if config in self.clients:
            logger.info(f'Gui set value of {config} {task}')
            if self.check_script(config).gui_set_task(task, group, arg, value):
                return True
            else:
                return False
        else:
            logger.info(f'Script {config} is not running')
            return False

    @Slot(str, str, result="bool")
    def gui_run_task_immediately(self, config: str, task: str) -> bool:
        """
        立即运行指定的任务，无视调度时间
        用户手动选择的任务具有最高优先级
        :param config: 配置名称
        :param task: 任务名称
        :return: 成功返回True，失败返回False
        """
        logger.info(f'User manually requested immediate run for task: {task}')
        
        return self._execute_immediate_run(config, task, user_priority=True)
    
    @Slot(str, str, bool, result="bool")
    def gui_run_task_immediately_with_options(self, config: str, task: str, stop_current: bool = False) -> bool:
        """
        高级立即运行，带冲突处理选项
        :param config: 配置名称
        :param task: 任务名称
        :param stop_current: 是否停止当前任务优先执行
        :return: 成功返回True，失败返回False
        """
        logger.info(f'User requested immediate run for task: {task}, stop_current: {stop_current}')
        
        if stop_current and config in self.clients:
            try:
                # 先通知脚本中断当前任务
                logger.info(f'Interrupting current task in {config} for priority task: {task}')
                result = self.clients[config].gui_interrupt_current_task()
                if result:
                    # 中断成功，等待当前任务停止并立即运行新任务
                    logger.info(f'Successfully sent interrupt signal, {task} will run immediately')
                    # 短暂等待中断生效，然后设置立即运行
                    from PySide6.QtCore import QTimer
                    QTimer.singleShot(500, lambda: self._execute_immediate_run(config, task, user_priority=True))
                    return True
                else:
                    # 中断失败，尝试停止整个脚本后重启
                    logger.warning(f'Failed to interrupt task, stopping script {config}')
                    self.stop_script(config)
                    # 延迟重启并执行新任务
                    from PySide6.QtCore import QTimer
                    QTimer.singleShot(2000, lambda: self._restart_and_run(config, task))
                    return True
            except Exception as e:
                logger.error(f'Failed to stop script for priority run: {e}')
                # 降级处理：直接排队执行
                return self._execute_immediate_run(config, task, user_priority=True)
        
        return self._execute_immediate_run(config, task, user_priority=True)
    
    def _execute_immediate_run(self, config: str, task: str, user_priority: bool = False) -> bool:
        """
        执行立即运行的核心逻辑
        :param config: 配置名称
        :param task: 任务名称
        :param user_priority: 是否为用户优先级任务
        :return: 成功返回True，失败返回False
        """
        priority_msg = " (USER PRIORITY)" if user_priority else ""
        logger.info(f'Executing immediate run for {config}.{task}{priority_msg}')
        
        if config in self.clients:
            try:
                # 调用后端脚本的立即运行接口
                result = self.clients[config].gui_run_task_immediately(task)
                if result:
                    logger.info(f'Task {task} successfully scheduled for immediate execution{priority_msg}')
                    # 立即运行成功，触发GUI刷新
                    self._trigger_gui_refresh(config)
                return result
            except Exception as e:
                logger.error(f'Failed to run task immediately: {e}')
                return False
        else:
            logger.info(f'Script {config} is not running, using ConfigModify for immediate run')
            try:
                # 如果脚本没有运行，使用ConfigModify来设置立即运行
                config_modify = self.check_script(config)
                result = config_modify.gui_run_task_immediately(task)
                if result:
                    logger.info(f'Task {task} configured for immediate execution when script starts{priority_msg}')
                    # 立即运行成功，触发GUI刷新
                    self._trigger_gui_refresh(config)
                return result
            except Exception as e:
                logger.error(f'Failed to set immediate run via ConfigModify: {e}')
                return False
    
    def _trigger_gui_refresh(self, config: str) -> None:
        """
        触发GUI刷新显示
        :param config: 配置名称
        """
        try:
            # 发送刷新信号，让GUI重新加载数据
            from PySide6.QtCore import QTimer
            QTimer.singleShot(500, lambda: self._delayed_refresh(config))  # 延迟500ms刷新
        except Exception as e:
            logger.debug(f'GUI refresh trigger not available: {e}')  # 降级为debug，不影响用户体验
    
    def _delayed_refresh(self, config: str) -> None:
        """
        延迟刷新GUI数据
        :param config: 配置名称
        """
        try:
            if config in self.clients:
                # 如果脚本在运行，它会自动发送更新
                pass
            else:
                # 如果脚本未运行，发送静态数据更新
                config_modify = self.check_script(config)
                task_list = config_modify.gui_task_list()
                # 这里可以发送信号更新GUI，但需要解析任务状态
                logger.info(f'Triggered delayed refresh for {config}')
        except Exception as e:
            logger.warning(f'Failed to perform delayed refresh: {e}')
    
    def _restart_and_run(self, config: str, task: str) -> None:
        """
        重启脚本并运行指定任务
        :param config: 配置名称
        :param task: 任务名称
        """
        try:
            logger.info(f'Restarting script {config} to run priority task: {task}')
            # 启动脚本
            self.start_script(config)
            # 等待脚本启动后设置立即运行
            from PySide6.QtCore import QTimer
            QTimer.singleShot(3000, lambda: self._execute_immediate_run(config, task, user_priority=True))
        except Exception as e:
            logger.error(f'Failed to restart and run: {e}')

    @Slot(str, result="bool")
    def is_running(self, config: str) -> bool:
        """
        检查指定配置的脚本是否正在运行
        :param config: 配置名称
        :return: 正在运行返回True，否则返回False
        """
        return config in self.processes and self.processes[config].is_alive()

    @Slot(str, result="QString")
    def get_current_task_status(self, config: str) -> str:
        """
        获取当前任务状态，用于冲突检查
        :param config: 配置名称
        :return: JSON格式的任务状态信息
        """
        try:
            if config in self.clients:
                # 如果脚本在运行，获取实时状态
                schedule_data = self.clients[config].gui_get_schedule_data()
                return schedule_data if schedule_data else "{}"
            else:
                # 如果脚本未运行，返回空状态
                return "{}"
        except Exception as e:
            logger.error(f'Failed to get task status for {config}: {e}')
            return "{}"

    @Slot(str, result="QImage")
    def gui_mirror_image(self, config: str) -> QImage:
        """
        :param config:
        :return:
        """
        if config in self.clients:
            logger.info(f'Gui get mirror image of {config}')
            # 接收流对象
            stream = self.clients[config].gui_mirror_image()
            # 创建 BytesIO 对象来存储图像数据
            buffer = io.BytesIO()
            for data in stream:
                buffer.write(data)
            # 将 BytesIO 对象的内容作为字节流解码为 cv2 图像
            buffer.seek(0)  # 将读取位置重置为起始位置
            image_data = np.frombuffer(buffer.getvalue(), dtype=np.uint8)
            image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)

            height, width, _ = image.shape
            image_qt = QImage(image.data, width, height, QImage.Format_RGB888).rgbSwapped()
            return image_qt



        else:
            logger.info(f'Script {config} is not running')
            return None



    @Slot(str, result="QString")
    def gui_task_list(self, config: str) -> str:
        if config in self.clients:
            logger.info(f'Gui get {config} task list')
            return self.check_script(config).gui_task_list()
        else:
            logger.info(f'Script {config} is not running')
            return None




    def start_log(self, config_name: str) -> Queue:
        """
        启动某个脚本实例config_name的log: 具体为创建一个queue信息队列，然后创建一个log线程，将queue传入log线程
        :param config_name:
        :return:
        """
        # if config_name not in self.processes:
        #     logger.error(f'Process manager has no config {config_name}')
        #     logger.info(f'Script {config_name} is not running')
        #     return None

        if config_name not in self.log_queue:
            self.log_queue[config_name] = self.manager.Queue()


        if config_name not in self.log_thread:
            self.log_thread[config_name] = Thread(target=self.log_thread_func, args=(config_name,), daemon=True)

        return self.log_queue[config_name]

    def log_thread_func(self, config_name: str) -> None:
        """
        log线程函数，将queue中的信息解析
        :param config_name:
        :return:
        """
        q = self.log_queue[config_name] if config_name in self.log_queue else None
        if q is None:
            logger.error(f'Process manager has no config {config_name}')
            logger.info(f'Script {config_name} is not running')
            return

        while self.log_thread[config_name].is_alive():
            try:
                log = q.get(timeout=1)
                if log is None:
                    continue
                log = highlight_text(str(log))
                self.log_signal.emit(config_name, log)

            except Empty:
                continue
            except Exception as e:
                logger.error(f'Log thread of {config_name} error: {e}')
                break

    def start_update_tasks(self) -> None:
        """
        启动更新任务的线程
        :return:
        """
        if self.update_queue is not None and self.update_thread is not None:
            logger.error(f'Update thread has already started')

        self.update_queue = self.manager.Queue()
        self.update_thread = Thread(target=self.update_thread_func, daemon=True)
        self.update_thread.start()

    def update_thread_func(self) -> None:
        """
        更新 任务的 线程函数
        从self.update_queue中获取信息，然后解析, 推送到gui
        :return:
        """
        logger.info(f'Update thread start')
        while self.update_thread.is_alive():
            try:
                update = self.update_queue.get(timeout=1)
                if update is None:
                    continue
                if not isinstance(update, dict):
                    continue

                logger.info(f'Update thread get')
                for key, value in update.items():
                    if "task" in value and "pending" in value and "waiting" in value:
                        self.sig_update_task.emit(key, json.dumps(value["task"]))
                        self.sig_update_pending.emit(key, json.dumps(value["pending"]))
                        self.sig_update_waiting.emit(key, json.dumps(value["waiting"]))

            except Empty:
                continue
            except Exception as e:
                logger.error(f'Update thread error: {e}')
                break

    @Slot(str)
    def start_script(self, config: str) -> None:
        """
        启动脚本的loop
        :param config:
        :return:
        """
        if not self.processes[config].is_alive():
            logger.info(f'Start script {config}')
            return self.restart(config)

        logger.info(f'Script {config} is already running')

        self.clients[config].start_loop()

    @Slot(str)
    def stop_script(self, config: str) -> None:
        """
        停止脚本的loop
        :param config:
        :return:
        """
        if config in self.processes:
            logger.info(f'Stop script {config}')
            self.processes[config].stop()
        else:
            logger.info(f'Script {config} is not running')

