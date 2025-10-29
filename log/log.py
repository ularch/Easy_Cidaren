import logging
import os
import datetime
import glob
import shutil
from PyQt6.QtWidgets import QFileDialog, QMessageBox

# 创建logs目录（如果不存在）
log_dir = os.path.join(os.path.dirname(__file__), '.', 'logs')
os.makedirs(log_dir, exist_ok=True)


# 清理旧的日志文件，只保留最近的20个
def clean_old_logs():
    log_files = glob.glob(os.path.join(log_dir, "app_*.log"))
    log_files.sort(key=os.path.getmtime, reverse=True)
    for old_file in log_files[20:]:
        try:
            os.remove(old_file)
        except OSError:
            pass  # 如果删除失败，忽略错误


# 执行清理操作
clean_old_logs()

# 生成带时间戳的日志文件名
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = os.path.join(log_dir, f"app_{timestamp}.log")

# logger变量
logger_instance = None


def setup_logger():
    """
    配置日志格式和处理器
    """
    global logger_instance
    logger_instance = logging.getLogger()
    logger_instance.setLevel(logging.INFO)

    # 清除现有的处理器以避免重复
    logger_instance.handlers.clear()

    formatter = logging.Formatter(
        "[%(asctime)s] %(name)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %I:%M:%S"
    )

    file_handler = logging.FileHandler(log_filename, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger_instance.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger_instance.addHandler(console_handler)

    return logger_instance


# 初始化日志
setup_logger()


def export_logs(main_window):
    """
    导出日志文件到用户指定位置
    """
    global logger_instance
    file_handler = None
    for handler in logger_instance.handlers:
        if isinstance(handler, logging.FileHandler):
            file_handler = handler
            break
    
    if file_handler:
        file_path = file_handler.baseFilename
        file_handler.close()
        logger_instance.removeHandler(file_handler)
        
        # 弹出文件保存对话框，将默认路径设置为C盘根目录
        default_save_path = os.path.join("C:\\", os.path.basename(file_path))
        file_name, _ = QFileDialog.getSaveFileName(
            main_window, 
            "导出日志文件", 
            default_save_path, 
            "Log Files (*.log);;All Files (*)"
        )
        
        if file_name:
            try:
                # 复制文件到用户选择的位置
                shutil.copy2(file_path, file_name)
                QMessageBox.information(main_window, "导出成功", f"日志文件已成功导出到：{file_name}")
                # 日志输出
                logger_instance.info(f"日志文件已成功导出到：{file_name}")
            except Exception as e:
                QMessageBox.critical(main_window, "导出失败", f"导出日志文件时发生错误：{str(e)}")
                logger_instance.error(f"导出日志文件时发生错误：{str(e)}")
            finally:
                # 恢复日志记录
                logger_instance.addHandler(file_handler)
        else:
            # 用户取消了保存操作
            logger_instance.addHandler(file_handler)
    else:
        QMessageBox.warning(main_window, "导出失败", "无法获取当前日志文件信息")
        logger_instance.error("导出日志失败：无法获取当前日志文件信息")


class Log:
    def __init__(self, logger_name: str):
        self.logger = logging.getLogger(logger_name)

    def open_logs_folder(self):
        """
        打开日志文件夹
        """
        import os
        import subprocess
        import sys

        logs_path = os.path.join(os.path.dirname(__file__), './logs')
        os.makedirs(logs_path, exist_ok=True)

        if sys.platform == 'win32':
            os.startfile(logs_path)
        elif sys.platform == 'darwin':  # macOS
            subprocess.Popen(['open', logs_path])
        else:  # linux
            subprocess.Popen(['xdg-open', logs_path])

    @staticmethod
    def prepare_export(main_window):
        """
        为导出准备日志文件，临时关闭文件处理器以解锁文件
        :return : 文件路径和文件处理器
        """
        global logger_instance
        file_handler = None
        for handler in logger_instance.handlers:
            if isinstance(handler, logging.FileHandler):
                file_handler = handler
                break

        if file_handler:
            file_path = file_handler.baseFilename
            file_handler.close()
            logger_instance.removeHandler(file_handler)
            return file_path, file_handler
        return None, None

    def resume_logging(self, file_handler):
        """
        在导出完成后恢复日志记录
        """
        global logger_instance
        if file_handler:
            logger_instance.addHandler(file_handler)