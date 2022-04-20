from main_window import *

if __name__ == "__main__":
    app = QApplication(sys.argv)
    a = MainWindow()
    a.show()
    sys.exit(app.exec_())