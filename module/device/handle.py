# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
import re

from enum import Enum
from cached_property import cached_property
from anytree import NodeMixin, RenderTree, PreOrderIter
from win32api import GetSystemMetrics, SendMessage, MAKELONG, PostMessage
from win32print import GetDeviceCaps
from win32process import GetWindowThreadProcessId
from win32gui import (GetWindowText, EnumWindows, FindWindow, FindWindowEx,
                      IsWindow, GetWindowRect, GetWindowDC, DeleteObject,
                      SetForegroundWindow, IsWindowVisible, GetDC, GetParent,
                      EnumChildWindows)
from win32con import (SRCCOPY, DESKTOPHORZRES, DESKTOPVERTRES, WM_LBUTTONUP,
                      WM_LBUTTONDOWN, WM_ACTIVATE, WA_ACTIVE, MK_LBUTTON,
                      WM_NCHITTEST, WM_SETCURSOR, HTCLIENT, WM_MOUSEMOVE)
from module.config.config import Config
from module.logger import logger


def handle_title2num(title: str) -> int:
    """
    从标题到句柄号
    :param title:
    :return:  如果没有找到就是返回零
    """
    return FindWindow(None, title)


def find_window_by_parent_title(parent_title: str, child_name = None) -> int:
    """
    通过父窗口标题查找子窗口句柄，用于解决模拟器重启后句柄变化的问题
    :param parent_title: 父窗口标题（模糊匹配）
    :param child_name: 子窗口名称（可选，用于精确匹配特定子窗口）
    :return: 找到的窗口句柄，未找到返回0
    """
    def enum_windows_callback(hwnd, result_list):
        window_text = GetWindowText(hwnd)
        if parent_title in window_text:
            result_list.append(hwnd)
    
    parent_windows = []
    EnumWindows(enum_windows_callback, parent_windows)
    
    if not parent_windows:
        logger.warning(f'No parent window found with title containing: {parent_title}')
        return 0
    
    # 如果找到多个父窗口，选择第一个
    parent_hwnd = parent_windows[0]
    if len(parent_windows) > 1:
        logger.warning(f'Multiple parent windows found, using first one: {GetWindowText(parent_hwnd)}')
    
    # 如果没有指定子窗口名称，直接返回父窗口句柄
    if child_name is None:
        logger.info(f'Found parent window: {GetWindowText(parent_hwnd)} (handle: {parent_hwnd})')
        return parent_hwnd
    
    # 查找指定名称的子窗口
    def enum_child_callback(child_hwnd, result_list):
        child_text = GetWindowText(child_hwnd)
        if child_text == child_name:
            result_list.append(child_hwnd)
    
    child_windows = []
    EnumChildWindows(parent_hwnd, enum_child_callback, child_windows)
    
    if child_windows:
        child_hwnd = child_windows[0]
        logger.info(f'Found child window: {child_name} (handle: {child_hwnd}) under parent: {GetWindowText(parent_hwnd)}')
        return child_hwnd
    else:
        logger.warning(f'Child window "{child_name}" not found under parent: {GetWindowText(parent_hwnd)}')
        return parent_hwnd  # 返回父窗口作为备选


def find_mumu_window_by_display_title(display_title: str) -> int:
    """
    专门针对MuMu模拟器的窗口查找，通过显示标题（如yys1）查找正确的截图句柄
    MuMu模拟器的窗口层级结构：
    Desktop -> yys1 -> MuMuNxDevice -> nemudisplay (目标窗口)
    
    :param display_title: 显示标题，如"yys1"
    :return: nemudisplay窗口的句柄，未找到返回0
    """
    def enum_windows_callback(hwnd, result_list):
        window_text = GetWindowText(hwnd)
        if window_text == display_title:
            result_list.append(hwnd)
    
    # 查找显示标题匹配的顶级窗口
    display_windows = []
    EnumWindows(enum_windows_callback, display_windows)
    
    if not display_windows:
        logger.warning(f'No window found with display title: {display_title}')
        return 0
    
    display_hwnd = display_windows[0]
    if len(display_windows) > 1:
        logger.warning(f'Multiple windows found with title "{display_title}", using first one')
    
    logger.info(f'Found display window: {display_title} (handle: {display_hwnd})')
    
    # 递归查找nemudisplay子窗口
    def find_nemudisplay_recursive(parent_hwnd, level=0):
        if level > 5:  # 防止无限递归
            return 0
            
        child_windows = []
        try:
            EnumChildWindows(parent_hwnd, lambda hwnd, param: param.append(hwnd), child_windows)
        except:
            return 0
        
        for child_hwnd in child_windows:
            if GetParent(child_hwnd) == parent_hwnd:
                child_text = GetWindowText(child_hwnd)
                logger.info(f'{"  " * level}Checking child: {child_text} (handle: {child_hwnd})')
                
                # 找到nemudisplay窗口
                if child_text == 'nemudisplay':
                    logger.info(f'Found target nemudisplay window: {child_hwnd}')
                    return child_hwnd
                
                # 继续在子窗口中递归查找
                result = find_nemudisplay_recursive(child_hwnd, level + 1)
                if result != 0:
                    return result
        
        return 0
    
    # 从显示窗口开始递归查找nemudisplay
    nemudisplay_hwnd = find_nemudisplay_recursive(display_hwnd)
    
    if nemudisplay_hwnd != 0:
        logger.info(f'Successfully found nemudisplay window: {nemudisplay_hwnd} for display title: {display_title}')
        return nemudisplay_hwnd
    else:
        logger.warning(f'nemudisplay window not found under display title: {display_title}')
        return display_hwnd  # 返回显示窗口作为备选


def enhanced_handle_title2num(title: str) -> int:
    """
    增强的标题到句柄转换，支持父窗口标题识别和MuMu模拟器的特殊处理
    :param title: 窗口标题
    :return: 窗口句柄，未找到返回0
    """
    # 首先检查是否为MuMu模拟器的显示标题
    # 特殊处理：如果标题看起来像MuMu模拟器的显示标题（不包含"模拟器"等关键词）
    traditional_emulator_keywords = ['模拟器', 'Player', 'Emulator', 'MuMu', '雷电', '夜神', '蓝叠', '逍遥']
    is_traditional_title = any(keyword in title for keyword in traditional_emulator_keywords)
    
    # 对于非传统标题，优先尝试MuMu显示标题检测
    if not is_traditional_title:
        logger.info(f'Trying MuMu display title detection for: {title}')
        mumu_handle = find_mumu_window_by_display_title(title)
        if mumu_handle != 0:
            return mumu_handle
    
    # 然后尝试直接匹配
    direct_handle = FindWindow(None, title)
    if direct_handle != 0:
        logger.info(f'Direct window match found: {title} (handle: {direct_handle})')
        
        # 如果是直接匹配但可能是MuMu显示窗口，尝试查找nemudisplay子窗口
        if not is_traditional_title:
            logger.info(f'Direct match found, but checking for nemudisplay child window...')
            mumu_handle = find_mumu_window_by_display_title(title)
            if mumu_handle != 0 and mumu_handle != direct_handle:
                logger.info(f'Found better nemudisplay window: {mumu_handle} instead of {direct_handle}')
                return mumu_handle
        
        return direct_handle
    
    # 如果直接匹配失败，尝试其他增强检测
    logger.info(f'Direct match failed for "{title}", trying enhanced detection...')
    
    # 对于传统的模拟器标题，尝试通过父窗口标题查找
    emulator_mappings = {
        'MuMu模拟器12': ('MuMu', 'MuMuPlayer'),
        'MuMu模拟器': ('MuMu', 'NemuPlayer'), 
        '雷电模拟器': ('雷电', 'TheRender'),
        '夜神模拟器': ('夜神', 'Nox'),
        '蓝叠模拟器': ('蓝叠', 'HD-Player'),
    }
    
    for exact_title, (parent_keyword, child_name) in emulator_mappings.items():
        if exact_title in title or parent_keyword in title:
            parent_handle = find_window_by_parent_title(parent_keyword, child_name)
            if parent_handle != 0:
                return parent_handle
    
    # 最后尝试模糊匹配父窗口
    for keyword in ['模拟器', 'Player', 'Emulator']:
        if keyword in title:
            parent_handle = find_window_by_parent_title(keyword)
            if parent_handle != 0:
                return parent_handle
    
    logger.error(f'No window found for title: {title}')
    return 0


def handle_num2title(num: int) -> str:
    """
    通过句柄号返回窗口的标题，如果传入句柄号不合法则返回空字符串
    :param num:
    :return:
    """
    if num is None or num == 0 or num == '':
        return ''
    try:
        title = GetWindowText(num)
        return title if title else ''
    except:
        return ''


def is_handle_valid(num: int) -> bool:
    """
    输入一个句柄号，如果还在返回True
    :param num:
    :return:
    """
    if num is None or num == 0:
        return False
    try:
        return bool(IsWindow(num))
    except:
        return False


def handle_num2pid(num: int) -> int:
    """
    通过句柄号获取句柄进程id，如果句柄号非法则返回0
    :param num:
    :return:
    """
    return 0 if num is None or num == 0 or num == '' else GetWindowThreadProcessId(num)[1]


def window_scale_rate() -> float:
    """
    获取window的系统缩放 一遍是1
    :return:
    """
    hDC = GetDC(0)
    # 物理上（真实的）的 横纵向分辨率
    wReal = GetDeviceCaps(hDC, DESKTOPHORZRES)
    hReal = GetDeviceCaps(hDC, DESKTOPVERTRES)
    # 缩放后的 分辨率
    wAfter = GetSystemMetrics(0)
    hAfter = GetSystemMetrics(1)
    # print(wReal, wAfter)
    return round(wReal / wAfter, 2)


class WindowNode(NodeMixin):
    def __init__(self, name, num, parent=None):
        super().__init__()
        self.name = name
        self.num = num
        self.parent = parent

    @classmethod
    def get_tree_depth(cls, root_node: 'WindowNode'):
        if not root_node.children:
            return 1 if root_node else 0
        return max(node.depth for node in root_node.descendants) + 1


class EmulatorFamily(Enum):
    FAMILY_MUMU = 10  # mumu模拟器
    FAMILY_NOX = 20  # 夜神模拟器
    FAMILY_LD = 30  # 雷电模拟器
    FAMILY_MEMU = 40  # 逍遥模拟器
    FAMILY_BLUESTACKS = 50  # 蓝叠模拟器
    FAMILY_OTHER = 60  # 其他模拟器 待定


# 各个模拟器的句柄树*******************************************************************************************************
""""
<MuMu>系列
模拟器的窗口名字
----MuMuPlayer      (!如果是mumu12是MuMuPlayer, 否则是NemuPlayer)
--------nemudisplay

<雷电模拟器系列>
雷电模拟器的窗口名字
----TheRender
--------sub

<夜神模拟器系列>  =====> 这个模拟器窗口很复杂，而且有的时候还会变化
夜神模拟器的窗口名字
----Nox
----Nox
--------toolbar_nox
--------Nox
------------Nox
----------------sub
---Nox
--------Nox
--------Nox    ==> 妈的太多了自己用spy++看吧

<蓝叠模拟器>
蓝叠模拟器的窗口名字
----HD-Player
--------_ctl.W
"""""
# **********************************************************************************************************************

class Handle:
    emulator_list = ['MuMu12',
                     'MuMu',
                     '雷电',
                     '夜神',
                     '蓝叠',
                     '逍遥',
                     '模拟器']  # 最后一个我又不知道还有哪些模拟器
    emulator_handle = {
        # 夜神
        'nox_player': ['root_handle_title', 'Nox'],
        'nox_player_64': ['root_handle_title', 'Nox'],
        'nox_player_family': ['root_handle_title', 'Nox'],
        # 雷电
        'ld_player': ['TheRender'],
        'ld_player_4': ['TheRender'],
        'ld_player_9': ['TheRender'],
        'ld_player_family': ['TheRender'],
        # 逍遥
        'memu_player': ['root_handle_title'],
        'memu_player_family': ['root_handle_title'],
        # mumu
        'mumu_player': ['root_handle_title', 'NemuPlayer'],
        'mumu_player_12': ['root_handle_title', 'MuMuPlayer'],
        'mumu_player_family': ['root_handle_title', 'MuMuPlayer'],
        # 蓝叠
        'bluestacks_5': ['root_handle_title'],
        'bluestacks_family': ['root_handle_title']
    }
    config: Config = None

    def __init__(self, config) -> None:
        """

        :param config:
        """
        logger.hr('Handle')
        if self.config is None:
            if isinstance(config, str):
                self.config = Config(config, task=None)
            else:
                self.config = config
        if not self.config.script.device.handle:
            logger.info('Handle is empty. oas not use handle')
            return
        if self.config.script.device.handle == '':
            logger.info('Handle is empty. oas not use handle')
            return

        # 获取根的句柄
        self.root_handle_title = ''
        self.root_handle_num = 0
        self.root_handle = self.config.script.device.handle
        if self.root_handle == "auto":
            logger.info('Handle is auto. oas will find window emulator')
            window_list = Handle.all_windows()
            self.root_handle_title = self.auto_handle_title(window_list)
            if self.root_handle_title:
                # 首先尝试传统方法
                traditional_handle = handle_title2num(self.root_handle_title)
                if traditional_handle != 0:
                    self.root_handle_num = traditional_handle
                    logger.info(f'Auto detection using traditional method: {self.root_handle_title}')
                else:
                    # 使用增强的句柄检测方法
                    logger.info('Auto detection: traditional method failed, trying enhanced detection...')
                    enhanced_handle = enhanced_handle_title2num(self.root_handle_title)
                    if enhanced_handle != 0:
                        self.root_handle_num = enhanced_handle
                        self.root_handle_title = handle_num2title(enhanced_handle)
                        logger.info(f'Auto detection using enhanced method: {self.root_handle_title} (handle: {enhanced_handle})')
                    else:
                        logger.error(f'Auto detection failed for title: {self.root_handle_title}')
            else:
                logger.error('Auto detection failed: no emulator window found')
        if isinstance(self.root_handle, str):
            try:
                self.root_handle_num = int(self.root_handle)
                logger.info('Handle is handle num. oas use it as root handle num')
                if is_handle_valid(self.root_handle_num):
                    logger.info(f'Handle number {self.root_handle_num} is valid')
                    self.root_handle_title = handle_num2title(self.root_handle_num)
            except ValueError:
                logger.info('Handle is handle string. oas use it as root handle title')
                # 首先尝试传统方法
                traditional_handle = handle_title2num(self.root_handle)
                if traditional_handle != 0:
                    self.root_handle_num = traditional_handle
                    self.root_handle_title = self.root_handle
                    logger.info(f'Found window using traditional method: {self.root_handle}')
                else:
                    # 使用增强的句柄检测方法
                    logger.info('Traditional method failed, trying enhanced detection...')
                    enhanced_handle = enhanced_handle_title2num(self.root_handle)
                    if enhanced_handle != 0:
                        self.root_handle_num = enhanced_handle
                        self.root_handle_title = handle_num2title(enhanced_handle)
                        logger.info(f'Found window using enhanced method: {self.root_handle_title} (handle: {enhanced_handle})')
                    else:
                        logger.error(f'Failed to find window with title: {self.root_handle}')
        logger.info(f'The root handle title is {self.root_handle_title} and num is {self.root_handle_num}')

        # 获取句柄树
        self.root_node = WindowNode(name=self.root_handle_title, num=self.root_handle_num)
        Handle.handle_tree(self.root_handle_num, self.root_node)
        logger.info('Emulator handle structure:')
        for pre, fill, node in RenderTree(self.root_node):
            logger.info("%s%s" % (pre, node.name))
        for pre, fill, node in RenderTree(self.root_node):
            logger.info("%s%s" % (pre, node.num))

        # 判断是哪一个模拟器 通过句柄树结构
        logger.info(f'Emulator family: {self.emulator_family}')

        # window系统的缩放
        logger.info(f'Your window screen scale rate: {window_scale_rate()}')
        _ = self.screenshot_handle_num
        logger.info(f'Screenshot handle num: {self.screenshot_handle_num}')
        logger.info(f'Emulator screenshot size: {self.screenshot_size}')

    @staticmethod
    def all_windows() -> list:
        """
        获取桌面上的所有窗体

        :return:  类似这样['MuMu模拟器']
        """

        def enum_windows_callback(hwnd, windows):
            window_text = GetWindowText(hwnd)
            windows.append(window_text)

        windows = []
        EnumWindows(enum_windows_callback, windows)
        return windows

    @classmethod
    def auto_handle_title(cls, windows: list) -> str:
        """
        返回第一个找到的有模拟器的标题
        :param windows:
        :return:
        """
        if windows is None:
            logger.error("handle_auto not get all wnidow")

        emu_list = []
        for window_title in windows:
            for item in Handle.emulator_list:
                if window_title.find(item) != -1:
                    emu_list.append(window_title)

        if not len(emu_list):
            logger.error('Can not find emulator handle, please check your emulator is running')
            return None

        emulator_title = ''
        # 测试mumu12的时候发现 获取的全部的窗体标题有这样的: 'MuMuPlayer', 'MuMuPlayer', 'MuMuPlayer', 'MuMu模拟器12'
        # 事实上 我们只需要最后一个 'MuMu模拟器12'，其他的不重要
        if 'MuMu模拟器12' in emu_list and 'MuMuPlayer' in emu_list:
            emulator_title = 'MuMu模拟器12'

        if len(emu_list) > 1 and emulator_title == '':
            logger.warning(f'Find more than one emulator handle, oas will use the first one {emu_list[0]}')
            emulator_title = emu_list[0]

        if len(emu_list) == 1:
            emulator_title = emu_list[0]

        logger.info(f'Handle auto seclect to find {emulator_title} and use it as root_title')
        return emulator_title

    @staticmethod
    def handle_tree(hwnd, node: WindowNode, level: int = 0) -> None:
        """
        生成一个窗口的句柄树
        :param hwnd:
        :param node:
        :param level:
        :return:
        """
        child_windows = []
        EnumChildWindows(hwnd, lambda hwnd, param: param.append(hwnd), child_windows)

        if not child_windows:
            return
        for child_hwnd in child_windows:
            if GetParent(child_hwnd) == hwnd:
                child_text = GetWindowText(child_hwnd)
                child_node = WindowNode(name=child_text, num=child_hwnd, parent=node)

                # 递归遍历子窗体的子窗体
                Handle.handle_tree(child_hwnd, child_node, level + 1)

    @cached_property
    def emulator_family(self) -> EmulatorFamily:
        """
        通过句柄树来判断这个是那个模拟器大类
        :return:
        """
        children_num = len(self.root_node.children)
        if children_num == 1:  #
            name = self.root_node.children[0].name
            if name == 'MuMuPlayer':
                return EmulatorFamily.FAMILY_MUMU
            elif name == 'NemuPlayer':
                return EmulatorFamily.FAMILY_MUMU
            elif name == 'MuMuNxDevice':  # 新增：识别MuMu的显示窗口结构
                return EmulatorFamily.FAMILY_MUMU
            elif name == 'TheRender':
                return EmulatorFamily.FAMILY_LD
            elif name == 'HD-Player':
                return EmulatorFamily.FAMILY_BLUESTACKS
        elif children_num >= 3:
            name = self.root_node.children[0].name
            if name == 'Nox':
                return EmulatorFamily.FAMILY_NOX

        # 特殊检测：通过子窗口结构识别MuMu模拟器
        # 检查是否有 MuMuNxDevice -> nemudisplay 的结构
        if children_num == 1:
            first_child = self.root_node.children[0]
            if first_child.name == 'MuMuNxDevice' and len(first_child.children) >= 1:
                for grandchild in first_child.children:
                    if grandchild.name == 'nemudisplay':
                        logger.info('Detected MuMu emulator by window structure: MuMuNxDevice -> nemudisplay')
                        return EmulatorFamily.FAMILY_MUMU

        # 基于句柄标题的判定
        for emu in Handle.emulator_list:
            if self.root_handle_title.find(emu) != -1:
                if emu == 'MuMu':
                    return EmulatorFamily.FAMILY_MUMU
                elif emu == '雷电':
                    return EmulatorFamily.FAMILY_LD
                elif emu == '夜神':
                    return EmulatorFamily.FAMILY_NOX
                elif emu == '蓝叠':
                    return EmulatorFamily.FAMILY_BLUESTACKS
                elif emu == '逍遥':
                    return EmulatorFamily.FAMILY_MEMU
        return EmulatorFamily.FAMILY_OTHER

    @cached_property
    def screenshot_handle_num(self) -> int:
        """
        截屏的句柄其实并不是根句柄
        :return:  出错返回None
        """
        if self.emulator_family == EmulatorFamily.FAMILY_MUMU:
            # 使用正则匹配12 来判定是不是mumu12这并不是一个好的方法
            name = self.root_node.children[0].name
            num = self.root_node.children[0].num
            if name == 'MuMuPlayer':
                logger.info('The emulator is MuMu模拟器12')
                return num
            elif name == 'NemuPlayer':
                logger.info('The emulator is MuMu模拟器')
                return num
            elif name == 'MuMuNxDevice':
                # 新的MuMu窗口结构：yys1 -> MuMuNxDevice -> nemudisplay
                logger.info('The emulator is MuMu with display title structure')
                # 查找nemudisplay子窗口
                first_child = self.root_node.children[0]
                for grandchild in first_child.children:
                    if grandchild.name == 'nemudisplay':
                        logger.info(f'Found nemudisplay window for screenshot: {grandchild.num}')
                        return grandchild.num
                # 如果没找到nemudisplay，返回MuMuNxDevice
                logger.warning('nemudisplay not found, using MuMuNxDevice')
                return num
        # 夜神
        elif self.emulator_family == EmulatorFamily.FAMILY_NOX:
            try:
                return self.root_node.children[1].children[1].num
            except:
                return self.root_node.children[2].children[1].num

        elif self.emulator_family == EmulatorFamily.FAMILY_LD:
            for node in PreOrderIter(self.root_node):
                if node.name == Handle.emulator_handle['ld_player_family'][0]:
                    return node.num

        elif self.emulator_family == EmulatorFamily.FAMILY_MEMU:
            for node in PreOrderIter(self.root_node):
                if node.name == Handle.emulator_handle['memu_player_family']:
                    return node.num

        elif self.emulator_family == EmulatorFamily.FAMILY_BLUESTACKS:
            for node in PreOrderIter(self.root_node):
                if node.name == Handle.emulator_handle['bluestacks_family']:
                    return node.num
        return self.root_node.num

    @cached_property
    def screenshot_size(self) -> tuple:
        """
        第一个是width 第二个是heigth
        2023.7.1 在高缩放的设备上应该输出1280X720
        :return:
        """
        handle_num = int(self.screenshot_handle_num)
        winRect = GetWindowRect(handle_num)
        scale_rate = window_scale_rate()
        width_before: int = winRect[2] - winRect[0]  # 右x-左x
        height_before: int = winRect[3] - winRect[1]  # 下y - 上y 计算高度
        width, height = width_before, height_before
        if abs((width_before * scale_rate) - 1280) < 5:
            width = 1280
        if abs((height_before * scale_rate) - 720) < 5:
            height = 720
        if width is None or height is None:
            logger.error(f'Get screenshot size error, width={width}, height={height}')
            return (1280, 720)  # 返回默认值而不是None
        return width, height

    @cached_property
    def window_scale_rate(self) -> float:
        """
        获取window的系统缩放 一般是1
        :return:
        """
        hDC = GetDC(0)
        # 物理上（真实的）的 横纵向分辨率
        wReal = GetDeviceCaps(hDC, DESKTOPHORZRES)
        hReal = GetDeviceCaps(hDC, DESKTOPVERTRES)
        # 缩放后的 分辨率
        wAfter = GetSystemMetrics(0)
        hAfter = GetSystemMetrics(1)
        # print(wReal, wAfter)
        return round(wReal / wAfter, 2)


    @classmethod
    def handle_has_children(cls, hwnd: int, name: str = 'MuMuPlayer12') -> bool:
        root_node = WindowNode(name=name, num=hwnd)
        Handle.handle_tree(hwnd=hwnd, node=root_node)
        handle_depth = WindowNode.get_tree_depth(root_node)
        if handle_depth > 1:
            logger.info(f'Window handle [{hwnd}] depth: {handle_depth}')
            return True
        return False


if __name__ == '__main__':
    h = Handle(config='oas1')
    # logger.info(h.auto_handle_title(h.all_windows()))
    # logger.info(h.root_handle_num)
    # logger.info(h.emulator_family)
