from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QComboBox, QProgressBar, QPushButton, QApplication, QMainWindow
from PyQt5.QtGui import QPixmap, QIcon

from minecraft_launcher_lib.utils import get_minecraft_directory, get_available_versions
from minecraft_launcher_lib.install import install_minecraft_version
from minecraft_launcher_lib.command import get_minecraft_command

from subprocess import call 
from sys import argv, exit
from uuid import uuid1
import psutil
import os

# Minecraft directory
minecraft_directory = get_minecraft_directory().replace('minecraft', 'dlwrtlauncher')

class LaunchThread(QThread):
    launch_setup_signal = pyqtSignal(str, str, str)
    progress_update_signal = pyqtSignal(int, int, str)
    state_update_signal = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.launch_setup_signal.connect(self.launch_setup)

    # Variables
    version_id = ''
    username = ''
    progress = 0
    progress_max = 0
    progress_label = ''

    # Launch setup
    def launch_setup(self, version_id, username, mem):
        self.version_id = version_id
        self.username = username
        self.mem = mem
    
    # Update progress
    def update_progress_label(self, value):
        self.progress_label = value
        self.progress_update_signal.emit(self.progress, self.progress_max, self.progress_label)
    def update_progress(self, value):
        self.progress = value
        self.progress_update_signal.emit(self.progress, self.progress_max, self.progress_label)
    def update_progress_max(self, value):
        self.progress_max = value
        self.progress_update_signal.emit(self.progress, self.progress_max, self.progress_label)

    # Run func
    def run(self):
        self.state_update_signal.emit(True)

        # Install Minecraft
        install_minecraft_version(versionid=self.version_id, minecraft_directory=minecraft_directory, callback={ 'setStatus': self.update_progress_label, 'setProgress': self.update_progress, 'setMax': self.update_progress_max })

        #if self.username == '':
        #    self.username = generate_username()[0]
        
        # Config
        options = {
            'username': self.username,
            'uuid': str(uuid1()),
            'token': ''
        }

        # Set RAM for java
        options["jvmArguments"] = [f"-Xmx{self.mem}G", f"-Xms{self.mem}G"]

        # Minecraft run
        call(get_minecraft_command(version=self.version_id, minecraft_directory=minecraft_directory, options=options))
        self.state_update_signal.emit(False)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Assets
        script_dir = os.path.dirname(os.path.abspath(__file__))
        resources_dir = os.path.join(script_dir, 'assets')

        # Window setup
        self.setWindowTitle('Dlwrty Launcher')
        self.adjustSize()

        # Title
        self.centralwidget = QWidget(self)  
        self.logo = QLabel(self.centralwidget)
        image_path = os.path.join(resources_dir, 'title.png')
        self.logo.setPixmap(QPixmap(image_path))
        self.logo.setFixedSize(600, 50)
        self.logo.setScaledContents(True)

        # Icon application
        icon_path = os.path.join(resources_dir, 'minecraft.ico')
        self.setWindowIcon(QIcon(icon_path))

        # Username
        self.username = QLineEdit(self.centralwidget)
        self.username.setPlaceholderText('Username')
        
        # Version select
        self.version_select = QComboBox(self.centralwidget)
        for version in get_available_versions(minecraft_directory):
            self.version_select.addItem(version['id'])
        
        # RAM select
        total_memory = psutil.virtual_memory().total
        mem = round(total_memory / 1024 ** 2 / 1024)
        self.mem = QComboBox(self.centralwidget)
        for i in range(1, mem + 1):
            self.mem.addItem(str(i))
        
        # Loading text
        self.start_progress_label = QLabel(self.centralwidget)
        self.start_progress_label.setText('')
        self.start_progress_label.setVisible(False)

        # Progress bar
        self.start_progress = QProgressBar(self.centralwidget)
        self.start_progress.setProperty('value', 50)
        self.start_progress.setVisible(False)
        
        # Play button
        self.start_button = QPushButton(self.centralwidget)
        self.start_button.setText('Play')
        self.start_button.clicked.connect(self.launch_game)

        # Vertical layout
        self.vertical_layout = QVBoxLayout(self.centralwidget)
        self.vertical_layout.setContentsMargins(15, 15, 15, 15)
        self.vertical_layout.addWidget(self.logo, 0, Qt.AlignmentFlag.AlignHCenter)
        self.vertical_layout.addWidget(self.username)
        self.vertical_layout.addWidget(self.mem)
        self.vertical_layout.addWidget(self.version_select)
        self.vertical_layout.addWidget(self.start_progress_label) 
        self.vertical_layout.addWidget(self.start_progress)
        self.vertical_layout.addWidget(self.start_button)

        # Launch thread
        self.launch_thread = LaunchThread()
        self.launch_thread.state_update_signal.connect(self.state_update)
        self.launch_thread.progress_update_signal.connect(self.update_progress)

        self.setCentralWidget(self.centralwidget)
    
    # Update values
    def state_update(self, value):
        self.start_button.setDisabled(value)
        self.start_progress_label.setVisible(value)
        self.start_progress.setVisible(value)
    def update_progress(self, progress, max_progress, label):
        self.start_progress.setValue(progress)
        self.start_progress.setMaximum(max_progress)
        self.start_progress_label.setText(label)
    def launch_game(self):
        self.launch_thread.launch_setup_signal.emit(self.version_select.currentText(), self.username.text(), self.mem.currentText())
        self.launch_thread.start()

if __name__ == '__main__':
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)

    app = QApplication(argv)
    window = MainWindow()
    window.show()

    exit(app.exec_())
