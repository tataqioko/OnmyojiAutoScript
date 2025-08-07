# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey

from tasks.GameUi.game_ui import GameUi
from tasks.GameUi.page import page_main
from module.exception import TaskEnd, GameNotRunningError
from module.logger import logger


class ScriptTask(GameUi):

    def run(self) -> None:
        try:
            self.ui_get_current_page()
            self.ui_goto(page_main)
        except GameNotRunningError as e:
            logger.warning(f"Game not running in GotoMain: {e}")
            # 让异常向上传播，由script.py的异常处理机制处理
            raise
        raise TaskEnd('Goto main end')
