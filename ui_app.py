import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QListWidget, QVBoxLayout,
    QPushButton, QHBoxLayout, QMessageBox, QInputDialog, QLineEdit
)
from PyQt5.QtCore import Qt

from session_manager import SessionManager, SessionData
from browser import get_browser
from proxy_extension import ProxyExtension


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Browser Session Manager")
        self.resize(600, 400)

        # Менеджер сессий (загружает из sessions.json)
        self.session_manager = SessionManager()

        # Будем хранить { session_id: driver }
        self.active_drivers = {}

        # Основной виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Список сессий
        self.session_list = QListWidget()
        self.session_list.setSelectionMode(QListWidget.SingleSelection)
        self.load_session_list()

        # Кнопки
        btn_create = QPushButton("Создать сессию")
        btn_create.clicked.connect(self.create_session)
        btn_rename = QPushButton("Переименовать")
        btn_rename.clicked.connect(self.rename_session)
        btn_start = QPushButton("Запустить выбранную")
        btn_start.clicked.connect(self.start_session)
        btn_set_proxy = QPushButton("Установить прокси")
        btn_set_proxy.clicked.connect(self.set_proxy_for_session)

        btn_stop = QPushButton("Остановить выбранную")
        btn_stop.clicked.connect(self.stop_session)

        btn_delete = QPushButton("Удалить выбранную")
        btn_delete.clicked.connect(self.delete_session)

        # Layout кнопок
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_create)
        btn_layout.addWidget(btn_rename)
        btn_layout.addWidget(btn_start)
        btn_layout.addWidget(btn_stop)
        btn_layout.addWidget(btn_delete)
        btn_layout.addWidget(btn_set_proxy)

        layout = QVBoxLayout()
        layout.addWidget(self.session_list)
        layout.addLayout(btn_layout)

        central_widget.setLayout(layout)

    def load_session_list(self):
        self.session_list.clear()
        for session_data in self.session_manager.list_sessions():
            self.session_list.addItem(
                f"{session_data.session_id} ({session_data.session_name}) | {session_data.user_data_dir}"
            )

    def get_selected_session_id(self):
        selected_items = self.session_list.selectedItems()
        if not selected_items:
            return None
        # Строка вида: "xxxxxxx | /path/to/user_data_dir"
        text = selected_items[0].text()
        parts = text.split("|", 1)
        if len(parts) < 2:
            return None
        left_part = parts[0].strip()
        session_id = left_part.split("(", 1)[0].strip()
        return session_id

    def create_session(self):
        s_data = self.session_manager.create_session()
        self.load_session_list()
        QMessageBox.information(self, "Сессия создана", f"Создана сессия: {s_data.session_id}")

    def start_session(self):
        session_id = self.get_selected_session_id()
        if not session_id:
            QMessageBox.warning(self, "Нет сессии", "Сначала выберите сессию")
            return

        if session_id in self.active_drivers:
            QMessageBox.information(self, "Уже запущен", "Браузер для этой сессии уже запущен.")
            return

        s_data = self.session_manager.get_session(session_id)
        if not s_data:
            QMessageBox.warning(self, "Ошибка", "Сессия не найдена.")
            return

        proxy_ext = ProxyExtension(
            host=s_data.proxy_host,
            port=s_data.proxy_port,
            user=s_data.proxy_user,
            password=s_data.proxy_password
        )

        driver = get_browser(extensions=[proxy_ext], user_data_dir=s_data.user_data_dir)
        self.active_drivers[session_id] = driver

        QMessageBox.information(
            self, "Браузер запущен",
            f"Сессия {session_id} запущена.\nUser data dir: {s_data.user_data_dir}"
        )

    def stop_session(self):
        session_id = self.get_selected_session_id()
        if not session_id:
            QMessageBox.warning(self, "Нет сессии", "Сначала выберите сессию")
            return

        driver = self.active_drivers.get(session_id)
        if driver is None:
            QMessageBox.information(self, "Нет браузера", "Для этой сессии браузер не запущен.")
            return

        try:
            driver.quit()
        except Exception as e:
            print(f"Ошибка при закрытии драйвера: {e}")
        finally:
            if session_id in self.active_drivers:
                del self.active_drivers[session_id]

        QMessageBox.information(self, "Остановлено", f"Сессия {session_id} остановлена")

    def rename_session(self):
        session_id = self.get_selected_session_id()
        if not session_id:
            QMessageBox.warning(self, "Нет сессии", "Сначала выберите сессию")
            return

        new_name, ok = QInputDialog.getText(
            self,
            "Переименовать сессию",
            "Введите новое имя для сессии:"
        )
        if ok and new_name.strip():
            self.session_manager.rename_session(session_id, new_name.strip())
            self.load_session_list()
            QMessageBox.information(
                self,
                "Сессия переименована",
                f"Сессия {session_id} теперь называется '{new_name}'"
            )

    def delete_session(self):
        session_id = self.get_selected_session_id()
        if not session_id:
            QMessageBox.warning(self, "Нет сессии", "Сначала выберите сессию")
            return

        if session_id in self.active_drivers:
            self.stop_session()

        self.session_manager.delete_session(session_id)
        self.load_session_list()
        QMessageBox.information(self, "Сессия удалена", f"Сессия {session_id} удалена")

    def set_proxy_for_session(self):
        session_id = self.get_selected_session_id()
        if not session_id:
            QMessageBox.warning(self, "Нет сессии", "Сначала выберите сессию")
            return

        host, ok = QInputDialog.getText(
            self,
            "Proxy host",
            "Введите прокси хост (IP или домен):",
            QLineEdit.Normal
        )
        if not ok:
            return

        port, ok = QInputDialog.getText(
            self,
            "Proxy port",
            "Введите порт прокси:",
            QLineEdit.Normal
        )
        if not ok:
            return

        user, ok = QInputDialog.getText(
            self,
            "Proxy user",
            "Введите имя пользователя (если нужно):",
            QLineEdit.Normal
        )
        if not ok:
            return

        password, ok = QInputDialog.getText(
            self,
            "Proxy password",
            "Введите пароль (если нужно):",
            QLineEdit.Normal
        )
        if not ok:
            return

        self.session_manager.set_proxy(session_id, host, port, user, password)
        QMessageBox.information(
            self,
            "Прокси установлена",
            f"Для сессии {session_id} установлены:\n"
            f"host={host}\nport={port}\nuser={user}\npassword={password}"
        )


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
