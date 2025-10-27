import logging
import os
import datetime
import glob

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

# 配置日志格式和处理器
logging.basicConfig(
    format="[%(asctime)s] %(name)s %(levelname)s: %(message)s", 
    datefmt="%Y-%m-%d %I:%M:%S",
    level=logging.INFO,
    handlers=[
        logging.FileHandler(log_filename, encoding="utf-8"),
        logging.StreamHandler()  # 保持控制台输出
    ]
)


class Log:
    def __init__(self, logger_name: str):
        self.logger = logging.getLogger(logger_name)