#!/usr/bin/env python3
import sys
import os
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt, QPoint, QTimer
from PyQt6.QtGui import QKeyEvent, QColor, QCloseEvent
from pynput import keyboard

class GnomeBotOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.is_running = False
        self.drag_position = QPoint()
        self._allow_close = False  # Flag to allow programmatic closing
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI"""
        # Configure window to be overlay-style
        self.setWindowTitle("Gnome Bot Overlay")
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |  # Always on top
            Qt.WindowType.FramelessWindowHint |   # No window decorations
            Qt.WindowType.Window                  # Regular window (not Tool, which can hide)
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)  # Allow activation
        
        # Set initial size and position (top-right corner)
        self.setFixedSize(200, 100)
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 220, 50)
        
        # Create main layout
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Create buttons
        self.start_button = QPushButton("Start")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                font-size: 12px;
                padding: 5px 20px;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.start_button.clicked.connect(self.start_bot)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                font-size: 12px;
                padding: 5px 20px;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        self.stop_button.clicked.connect(self.stop_bot)
        
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        self.setLayout(layout)
        
        # Store button styles for later use
        self.button_styles = {
            'start': self.start_button.styleSheet(),
            'stop': self.stop_button.styleSheet()
        }
        
        # Set initial background color (red = stopped)
        self.update_background_color('red')
        
        # Prevent window from closing when clicking outside
        self.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, False)
        
        # Set up a timer to ensure window stays visible
        self.visibility_timer = QTimer()
        self.visibility_timer.timeout.connect(self.ensure_visible)
        self.visibility_timer.start(500)  # Check every 500ms
        
        # Set up global hotkey listener for Control+Q (or Command+Q on Mac)
        self.setup_global_hotkey()
        
    def setup_global_hotkey(self):
        """Set up global hotkey listener for Control+Q (or Command+Q on Mac)"""
        # Track modifier keys
        self.ctrl_pressed = False
        self.cmd_pressed = False
        
        def on_press(key):
            try:
                # Track modifier keys
                if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                    self.ctrl_pressed = True
                elif key == keyboard.Key.cmd_l or key == keyboard.Key.cmd_r:
                    self.cmd_pressed = True
                
                # Check if 'q' key is pressed with modifier
                if hasattr(key, 'char') and key.char == 'q':
                    if self.ctrl_pressed or self.cmd_pressed:
                        # Schedule quit on main thread
                        QTimer.singleShot(1, self.quit_app)
            except AttributeError:
                # Special keys don't have char attribute
                pass
        
        def on_release(key):
            try:
                # Track modifier key release
                if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                    self.ctrl_pressed = False
                elif key == keyboard.Key.cmd_l or key == keyboard.Key.cmd_r:
                    self.cmd_pressed = False
            except:
                pass
        
        # Start listener in a separate thread
        self.listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self.listener.daemon = True  # Thread dies when main thread dies
        self.listener.start()
        
    def closeEvent(self, event: QCloseEvent):
        """Handle close event - only allow closing via Control+Q"""
        # Only allow closing if we explicitly set the flag
        if self._allow_close:
            event.accept()
        else:
            # Prevent accidental closing by clicking outside or system close
            event.ignore()
        
    def changeEvent(self, event):
        """Prevent window from minimizing or closing when losing focus"""
        if event.type() == event.Type.WindowStateChange:
            # Keep window visible
            if self.isMinimized():
                self.showNormal()
        elif event.type() == event.Type.ActivationChange:
            # Ensure window stays visible even when not active
            if not self.isVisible():
                self.show()
        super().changeEvent(event)
        
    def hideEvent(self, event):
        """Prevent window from being hidden"""
        # Force window to stay visible
        self.show()
        event.ignore()
        
    def ensure_visible(self):
        """Periodically ensure the window stays visible"""
        if not self.isVisible():
            self.show()
            self.raise_()  # Bring to front
            self.activateWindow()  # Activate if possible
        
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events - Control+Q to quit"""
        if event and event.key() == Qt.Key.Key_Q:
            # Check if Control or Command modifier is pressed
            modifiers = event.modifiers()
            if modifiers & Qt.KeyboardModifier.ControlModifier or modifiers & Qt.KeyboardModifier.MetaModifier:
                self.quit_app()
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)
        
    def mousePressEvent(self, event):
        """Handle mouse press for dragging"""
        if event and event.button() == Qt.MouseButton.LeftButton:
            try:
                self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()
            except Exception as e:
                print(f"Error in mousePressEvent: {e}")
                event.ignore()
        else:
            event.ignore()
            
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging"""
        if event and event.buttons() == Qt.MouseButton.LeftButton:
            try:
                self.move(event.globalPos() - self.drag_position)
                event.accept()
            except Exception as e:
                print(f"Error in mouseMoveEvent: {e}")
                event.ignore()
        else:
            event.ignore()
            
    def update_background_color(self, color):
        """Update the background color while preserving button styles"""
        base_style = f"QWidget {{ background-color: {color}; }}"
        self.setStyleSheet(base_style)
        # Reapply button styles
        self.start_button.setStyleSheet(self.button_styles['start'])
        self.stop_button.setStyleSheet(self.button_styles['stop'])
        
    def start_bot(self):
        """Start the bot"""
        self.is_running = True
        self.update_background_color('green')
        print("Bot started")
        
    def stop_bot(self):
        """Stop the bot"""
        self.is_running = False
        self.update_background_color('red')
        print("Bot stopped")
        
    def quit_app(self):
        """Quit the application"""
        # Stop the visibility timer
        if hasattr(self, 'visibility_timer'):
            self.visibility_timer.stop()
        
        # Stop the global hotkey listener
        if hasattr(self, 'listener'):
            try:
                self.listener.stop()
            except:
                pass
        
        self._allow_close = True
        self.close()
        
        # Flush any pending output
        sys.stdout.flush()
        sys.stderr.flush()
        
        # Quit the application
        QApplication.instance().quit()
        
        # Force immediate exit - os._exit terminates the process immediately
        # This bypasses all Python cleanup and returns control to terminal
        os._exit(0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Install exception handler to catch any unhandled errors
    def exception_handler(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        print(f"Unhandled exception: {exc_type.__name__}: {exc_value}")
        import traceback
        traceback.print_exception(exc_type, exc_value, exc_traceback)
    
    sys.excepthook = exception_handler
    
    overlay = GnomeBotOverlay()
    overlay.show()
    sys.exit(app.exec())

