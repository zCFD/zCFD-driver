#from utils import zip_files, join_files, log, get_temp_dir
import sys, os, glob, json, re, shutil, stat, tarfile
import zipfile, traceback, platform, filecmp
from PySide import QtGui, QtCore
from PySide.QtGui import QApplication
from PySide.QtNetwork import QHttp
from PySide.QtCore import QUrl, QFileInfo, QFile, QIODevice
from zipfile import ZipFile
from tarfile import TarFile

class Setting(object):
    def __init__(self, name='', display_name=None, value=None, required=False, type=None, file_types=None, *args, **kwargs):
        self.name = name
        self.display_name = display_name if display_name else name.replace('_',' ').capitalize()
        self.value = value
        self.required = required
        self.type = type
        self.file_types = file_types
        self.default_value = kwargs.pop('default_value', None)
        if self.value is None:
            self.value = self.default_value
        
class MainWindow(QtGui.QWidget):
    
    
    app_settings = {'main': Setting(name='main', display_name='Main file', required=True, type='file', file_types='*.html *.php *.htm'),
                    'name': Setting(name='name', display_name='App Name', required=True, type='string'),
                    'description': Setting(name='description', default_default_value='', type='string'),
                    'version': Setting(name='version', default_value='0.1.0', type='string'),
                    'keywords':Setting(name='keywords', default_value='', type='string'),
                    'nodejs': Setting('nodejs', 'Include Nodejs', default_value=True, type='check'),
                    'node-main': Setting('node-main', 'Alt. Nodejs', default_value='', type='file', file_types='*.js'),
                    'single-instance': Setting('single-instance', 'Single Instance', default_value=True, type='check')}
    
    application_setting_order = ['main', 'name', 'node-main', 'description', 'version', 'keywords',
                                 'nodejs', 'single-instance']
    _setting_groups = [app_settings]
    
    def __init__(self, width, height, parent=None):
        super(MainWindow, self).__init__(parent)
        
        self.create_application_layout()

        #self.option_settings_enabled(False)

        self.setWindowTitle("zCFD UI")
        
    def create_application_layout(self):
        self.main_layout = QtGui.QVBoxLayout()
        
        self.create_layout_widgets()
        
        self.add_widgets_to_main_layout()
        
        self.setLayout(self.main_layout)
    
    def create_layout_widgets(self):
        """
        self.download_bar_widget = self.createDownloadBar()
        self.app_settings_widget = self.createApplicationSettings()
        self.win_settings_widget = self.createWindowSettings()
        self.ex_settings_widget = self.createExportSettings()
        self.dl_settings_widget = self.createDownloadSettings()
        self.directory_chooser_widget = self.createDirectoryChoose()
        """
        self.equations_widget = self.create_equations_section()
        
    
    def add_widgets_to_main_layout(self):
        """
        self.main_layout.addWidget(self.directory_chooser_widget)
        self.main_layout.addWidget(self.app_settings_widget)
        self.main_layout.addWidget(self.win_settings_widget)
        self.main_layout.addWidget(self.ex_settings_widget)
        self.main_layout.addWidget(self.dl_settings_widget)
        self.main_layout.addLayout(self.download_bar_widget)  
        """
        self.main_layout.addWidget(self.equations_widget)
     

    def create_equations_section(self):
        groupBox = QtGui.QGroupBox("Equations")
        vlayout = self.createLayout(self.application_setting_order)

        groupBox.setLayout(vlayout)
        return groupBox


    def getSetting(self, name):
        for setting_group in self._setting_groups:
            if name in setting_group:
                setting = setting_group[name]
                return setting
            
    def createLayout(self, settings, cols=3):
        glayout = QtGui.QGridLayout()

        col = 0
        row = 0

        for setting_name in settings:
            setting = self.getSetting(setting_name)
            if col >= cols*2:
                row += 1
                col = 0
            display_name = setting.display_name+':'
            if setting.required:
                display_name += '*'
            glayout.addWidget(QtGui.QLabel(display_name),row,col)
            glayout.addLayout(self.createSetting(setting_name),row,col+1)
            col += 2

        return glayout
    
    def createSetting(self, name):
        setting = self.getSetting(name)
        if setting.type == 'string':
            return self.createTextInputSetting(name)
        elif setting.type == 'file':
            return self.createTextInputWithFileSetting(name)
        elif setting.type == 'check':
            return self.createCheckSetting(name)
        elif setting.type == 'list':
            return self.createListSetting(name)
        
    def createTextInputSetting(self, name):
        hlayout = QtGui.QHBoxLayout()

        setting = self.getSetting(name)

        text = QtGui.QLineEdit()
        text.setObjectName(setting.name)

        text.textChanged.connect(self.callWithObject('settingChanged', text, setting))
        if setting.value:
            text.setText(str(setting.value))

        hlayout.addWidget(text)

        return hlayout

    def createTextInputWithFileSetting(self, name):
        hlayout = QtGui.QHBoxLayout()

        setting = self.getSetting(name)

        text = QtGui.QLineEdit()
        text.setObjectName(setting.name)

        button = QtGui.QPushButton('...')
        button.setMaximumWidth(30)
        button.setMaximumHeight(26)

        button.clicked.connect(self.callWithObject('getFile', button, text, setting))

        if setting.value:
            text.setText(str(setting.value))

        text.textChanged.connect(self.callWithObject('settingChanged', text, setting))

        hlayout.addWidget(text)
        hlayout.addWidget(button)

        return hlayout
    
    def createCheckSetting(self, name):
        hlayout = QtGui.QHBoxLayout()

        setting = self.getSetting(name)

        check = QtGui.QCheckBox()

        check.setObjectName(setting.name)

        check.clicked.connect(self.callWithObject('settingChanged', check, setting))
        check.setChecked(setting.value)

        hlayout.addWidget(check)

        return hlayout

    def createListSetting(self, name):
        hlayout = QtGui.QHBoxLayout()

        setting = self.getSetting(name)

        combo = QtGui.QComboBox()

        combo.setObjectName(setting.name)

        combo.currentIndexChanged.connect(self.callWithObject('settingChanged', combo, setting))
        combo.editTextChanged.connect(self.callWithObject('settingChanged', combo, setting))

        for val in setting.values:
            combo.addItem(val)

        default_index = combo.findData(setting.default_value)
        if default_index != -1:
            combo.setCurrentIndex(default_index)

        hlayout.addWidget(combo)

        return hlayout
    
    def callWithObject(self, name, obj, *args, **kwargs):
        """Allows arguments to be passed to click events"""
        def call():
            if hasattr(self, name):
                func = getattr(self, name)
                func(obj, *args, **kwargs)
        return call
    
    def show_and_raise(self):
        self.show()
        self.raise_()
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    frame = MainWindow(800, 500)
    frame.show_and_raise()
    
    sys.exit(app.exec_())