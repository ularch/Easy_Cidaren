import os
import sys
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextBrowser, QMessageBox
from PyQt6.QtCore import QThread, pyqtSignal
from api.token_capture_service import TokenCaptureService


class TokenCaptureWorker(QThread):
    """工作线程：负责在后台调用 Token 捕获服务"""
    token_captured = pyqtSignal(str)  # 捕获到 token 的信号
    status_update = pyqtSignal(str)   # 状态更新信号
    error_occurred = pyqtSignal(str)  # 错误信号

    def __init__(self, fetch_token_path):
        super().__init__()
        self.fetch_token_path = fetch_token_path
        self.service = None

    def run(self):
        """在线程中执行 token 捕获"""
        try:
            # 创建后端服务实例
            self.service = TokenCaptureService(self.fetch_token_path)
            
            # 调用后端服务，传入回调函数
            token = self.service.start_capture(
                status_callback=lambda msg: self.status_update.emit(msg),
                token_callback=lambda token: self.token_captured.emit(token),
                error_callback=lambda err: self.error_occurred.emit(err)
            )
            
            # 如果没有通过回调返回，检查返回值
            if token and not self.isInterruptionRequested():
                self.token_captured.emit(token)
                
        except Exception as e:
            self.error_occurred.emit(f"发生错误: {str(e)}")

    def stop(self):
        """停止工作线程"""
        if self.service:
            self.service.stop()


class BuiltinTokenDialog(QDialog):
    """内置 Token 获取对话框"""
    
    def __init__(self, parent=None, fetch_token_path=None):
        super().__init__(parent)
        self.fetch_token_path = fetch_token_path
        self.worker = None
        self.captured_token = None
        self.setup_ui()
        
    def setup_ui(self):
        """设置 UI 界面"""
        self.setWindowTitle("内置获取 Token")
        self.setFixedSize(600, 400)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("内置 Token 获取工具")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        main_layout.addWidget(title_label)
        
        # 说明文本
        info_text = (
            "使用说明：\n"
            "1. 点击'开始捕获'按钮\n"
            "2. 打开 PC 微信并访词达人学生端\n"
            "3. 等待自动捕获 UserToken\n"
            "4. 捕获成功后会自动填充到主界面"
        )
        info_label = QLabel(info_text)
        info_label.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        info_label.setWordWrap(True)
        main_layout.addWidget(info_label)
        
        # 状态显示区域
        status_label = QLabel("状态信息：")
        status_label.setStyleSheet("font-weight: bold; padding-top: 10px;")
        main_layout.addWidget(status_label)
        
        self.status_browser = QTextBrowser()
        self.status_browser.setMaximumHeight(150)
        self.status_browser.setStyleSheet("background-color: #fafafa;")
        main_layout.addWidget(self.status_browser)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("开始捕获")
        self.start_button.clicked.connect(self.start_capture)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("停止捕获")
        self.stop_button.clicked.connect(self.stop_capture)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        self.close_button = QPushButton("关闭")
        self.close_button.clicked.connect(self.close_dialog)
        button_layout.addWidget(self.close_button)
        
        main_layout.addLayout(button_layout)
        
        # 添加分隔线
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        main_layout.addWidget(separator)
        
        # 提示信息
        hint_label = QLabel("提示：如果捕获失败，请检查是否已安装 mitmproxy 并关闭其他代理软件")
        hint_label.setStyleSheet("color: #666; font-size: 11px; padding: 5px;")
        hint_label.setWordWrap(True)
        main_layout.addWidget(hint_label)
    
    def append_status(self, message):
        """追加状态信息"""
        self.status_browser.append(message)
        # 自动滚动到底部
        scrollbar = self.status_browser.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def start_capture(self):
        """开始捕获 token"""
        if not self.fetch_token_path or not os.path.exists(self.fetch_token_path):
            QMessageBox.warning(self, "错误", "fetch_token 路径不存在！")
            return
        
        # 清空之前的状态
        self.status_browser.clear()
        self.captured_token = None
        
        # 禁用开始按钮，启用停止按钮
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.close_button.setEnabled(False)
        
        # 创建工作线程
        self.worker = TokenCaptureWorker(self.fetch_token_path)
        self.worker.status_update.connect(self.append_status)
        self.worker.token_captured.connect(self.on_token_captured)
        self.worker.error_occurred.connect(self.on_error)
        self.worker.start()
        
        self.append_status("开始捕获流程...")
    
    def stop_capture(self):
        """停止捕获"""
        if self.worker and self.worker.isRunning():
            self.append_status("正在停止捕获...")
            self.worker.stop()
            self.worker.quit()
            self.worker.wait()
        
        self.reset_buttons()
    
    def on_token_captured(self, token):
        """token 捕获成功"""
        self.captured_token = token
        self.append_status(f"\nToken 已捕获！长度: {len(token)}")
        
        # 停止工作线程
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.quit()
            self.worker.wait()
        
        # 通知父窗口
        if self.parent():
            self.parent().on_builtin_token_captured(token)
        
        # 显示成功消息
        QMessageBox.information(
            self, 
            "成功", 
            f"Token 捕获成功！\n\nToken 已自动填充到主界面。\n\n您可以点击'关闭'按钮关闭此窗口。"
        )
        
        self.reset_buttons()
    
    def on_error(self, error_message):
        """发生错误"""
        self.append_status(f"\n错误: {error_message}")
        QMessageBox.critical(self, "错误", f"捕获过程中发生错误:\n\n{error_message}")
        self.reset_buttons()
    
    def reset_buttons(self):
        """重置按钮状态"""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.close_button.setEnabled(True)
    
    def close_dialog(self):
        """关闭对话框"""
        # 如果工作线程还在运行，先停止它
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.quit()
            self.worker.wait()
        
        self.accept()
