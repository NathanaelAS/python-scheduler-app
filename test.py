from PyQt5.QtCore import Qt

try:
    print(Qt.LeftButton)
except AttributeError as e:
    print(f"Error: {e}. Qt.LeftButton is not recognized.")