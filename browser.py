import sys
import json
import os
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLineEdit, QTabWidget, QLabel, QDialog, QListWidget,
                             QListWidgetItem, QInputDialog, QMessageBox, QSlider, QCheckBox, QSpinBox)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QFont, QColor
from PyQt6.QtWidgets import QComboBox
from PyQt6.QtCore import QTimer

class BrowserTab(QWidget):
    """Individual browser tab"""
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Web view
        self.web_view = QWebEngineView()
        self.web_view.loadFinished.connect(self.on_load_finished)
        self.layout.addWidget(self.web_view)
        self.setLayout(self.layout)
        self.url = ""
        self.title = ""
        
    def on_load_finished(self, success):
        """Handle page load completion"""
        if not success:
            self.show_error_page()
        
    def show_error_page(self):
        """Show error page if loading fails"""
        url = self.web_view.url().toString()
        html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background: #f0f0f0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }}
                .error-container {{
                    background: white;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    text-align: center;
                    max-width: 500px;
                }}
                .error-icon {{
                    font-size: 60px;
                    margin-bottom: 20px;
                }}
                h1 {{
                    color: #d32f2f;
                    margin: 0 0 10px 0;
                }}
                p {{
                    color: #666;
                    margin: 10px 0;
                }}
                .url {{
                    background: #f5f5f5;
                    padding: 10px;
                    border-radius: 5px;
                    word-break: break-all;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="error-container">
                <div class="error-icon">⚠️</div>
                <h1>Page Not Found</h1>
                <p>The page failed to load. This could be due to:</p>
                <ul style="text-align: left;">
                    <li>No internet connection</li>
                    <li>Invalid URL</li>
                    <li>Server is down</li>
                    <li>Too many redirects</li>
                </ul>
                <p><strong>Tried to load:</strong></p>
                <div class="url">{url}</div>
                <p style="margin-top: 20px; color: #999; font-size: 12px;">
                    Try checking the URL or connecting to the internet.
                </p>
            </div>
        </body>
        </html>
        """
        self.web_view.setHtml(html)
        
    def load_url(self, url):
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        self.url = url
        self.web_view.load(QUrl(url))
        
    def load_html(self, html):
        self.web_view.setHtml(html)


class Browser(QMainWindow):
    """Main browser window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle('MyBrowser - Enhanced Edition')
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize data storage
        self.history = []
        self.bookmarks = []
        self.downloads = []
        self.custom_shortcuts = []
        self.data_file = 'browser_data.json'
        self.dark_mode = False
        self.settings = {
            'dark_mode': False,
            'default_zoom': 100,
            'font_size': 14,
            'home_page_url': 'home',
            'auto_recover_tabs': True
        }
        self.load_data()
        self.apply_theme()
        # Create main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # ===== NAVIGATION BAR =====
        nav_layout = QHBoxLayout()
        
        # Back button
        self.back_btn = QPushButton('←')
        self.back_btn.setMaximumWidth(40)
        self.back_btn.clicked.connect(self.back)
        nav_layout.addWidget(self.back_btn)
        
        # Forward button
        self.forward_btn = QPushButton('→')
        self.forward_btn.setMaximumWidth(40)
        self.forward_btn.clicked.connect(self.forward)
        nav_layout.addWidget(self.forward_btn)
        
        # Reload button
        self.reload_btn = QPushButton('⟳')
        self.reload_btn.setMaximumWidth(40)
        self.reload_btn.clicked.connect(self.reload)
        nav_layout.addWidget(self.reload_btn)
        
        # Stop button
        self.stop_btn = QPushButton('✕')
        self.stop_btn.setMaximumWidth(40)
        self.stop_btn.clicked.connect(self.stop)
        nav_layout.addWidget(self.stop_btn)
        
        # URL/Search bar with autocomplete
        self.url_bar = QComboBox()
        self.url_bar.setEditable(True)
        self.url_bar.setMaximumHeight(30)
        self.url_bar.lineEdit().returnPressed.connect(self.navigate)
        nav_layout.addWidget(self.url_bar)
        
        # Star button (bookmark)
        self.star_btn = QPushButton('☆')
        self.star_btn.setMaximumWidth(40)
        self.star_btn.clicked.connect(self.toggle_bookmark)
        nav_layout.addWidget(self.star_btn)
        
        # Menu button
        self.menu_btn = QPushButton('≡')
        self.menu_btn.setMaximumWidth(40)
        self.menu_btn.clicked.connect(self.show_menu)
        nav_layout.addWidget(self.menu_btn)
        
        main_layout.addLayout(nav_layout)
        
        # ===== TAB WIDGET =====
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        main_layout.addWidget(self.tabs)
        
        # Add new tab button
        new_tab_btn = QPushButton('+')
        new_tab_btn.setMaximumWidth(40)
        new_tab_btn.clicked.connect(self.add_tab)
        self.tabs.setCornerWidget(new_tab_btn)
        
        # Add first tab
        self.add_tab()
        
        # Set main layout
        main_widget.setLayout(main_layout)
        
        # Update URL bar when tab changes
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        # Auto-recover tabs on startup
        self.recover_tabs()
        
        self.show()
    
    def apply_theme(self):
        """Apply dark or light theme"""
        if self.settings['dark_mode']:
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QWidget {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QPushButton {
                    background-color: #404040;
                    color: #ffffff;
                    border: 1px solid #555;
                    border-radius: 4px;
                    padding: 4px;
                }
                QPushButton:hover {
                    background-color: #505050;
                }
                QLineEdit, QComboBox {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    border: 1px solid #555;
                    border-radius: 4px;
                    padding: 4px;
                }
                QTabWidget, QTabBar {
                    background-color: #2b2b2b;
                    color: #ffffff;
                }
                QTabBar::tab {
                    background-color: #404040;
                    color: #ffffff;
                    padding: 4px 20px;
                    border: 1px solid #555;
                }
                QTabBar::tab:selected {
                    background-color: #505050;
                }
            """)
        else:
            self.setStyleSheet("")
    
    def add_tab(self, url=None):
        """Add a new tab"""
        tab = BrowserTab()
        tab_index = self.tabs.addTab(tab, f'Tab {self.tabs.count() + 1}')
        self.tabs.setCurrentIndex(tab_index)
        
        if url:
            tab.load_url(url)
        else:
            self.show_home_page(tab)
        
        # Update tab title when page loads
        tab.web_view.titleChanged.connect(lambda title: self.update_tab_title(tab_index, title))
    
    def update_tab_title(self, index, title):
        """Update tab title based on page title"""
        if title:
            short_title = title[:20] + '...' if len(title) > 20 else title
            self.tabs.setTabText(index, short_title)
    
    def close_tab(self, index):
        """Close a tab"""
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)
        else:
            self.show_message('Cannot close the last tab!')
    
    def on_tab_changed(self, index):
        """Handle tab change"""
        if index >= 0:
            current_tab = self.tabs.widget(index)
            self.update_url_bar()
    
    def navigate(self):
        """Navigate to URL in address bar"""
        url = self.url_bar.currentText().strip()
        if url:
            self.history.append(url)
            self.url_bar.addItem(url)
            current_tab = self.tabs.currentWidget()
            current_tab.load_url(url)
    
    def update_url_bar(self):
        """Update URL bar with current page URL"""
        current_tab = self.tabs.currentWidget()
        if current_tab:
            url = current_tab.web_view.url().toString()
            self.url_bar.lineEdit().setText(url)
    
    def back(self):
        """Go back"""
        current_tab = self.tabs.currentWidget()
        if current_tab:
            current_tab.web_view.back()
    
    def forward(self):
        """Go forward"""
        current_tab = self.tabs.currentWidget()
        if current_tab:
            current_tab.web_view.forward()
    
    def reload(self):
        """Reload page"""
        current_tab = self.tabs.currentWidget()
        if current_tab:
            current_tab.web_view.reload()
    
    def stop(self):
        """Stop loading"""
        current_tab = self.tabs.currentWidget()
        if current_tab:
            current_tab.web_view.stop()
    
    def toggle_bookmark(self):
        """Add/remove bookmark for current page"""
        current_tab = self.tabs.currentWidget()
        if current_tab:
            url = current_tab.web_view.url().toString()
            title = current_tab.web_view.title() or url
            
            bookmark = {'url': url, 'title': title}
            
            if bookmark in self.bookmarks:
                self.bookmarks.remove(bookmark)
                self.show_message(f'Removed bookmark: {title}')
                self.star_btn.setText('☆')
            else:
                self.bookmarks.append(bookmark)
                self.show_message(f'Bookmarked: {title}')
                self.star_btn.setText('★')
            
            self.save_data()
    
    def show_menu(self):
        """Show menu with options"""
        dialog = QDialog(self)
        dialog.setWindowTitle('Menu')
        dialog.setGeometry(self.width() - 250, 80, 250, 350)
        
        layout = QVBoxLayout()
        
        # Bookmarks button
        bookmarks_btn = QPushButton('📚 Bookmarks')
        bookmarks_btn.clicked.connect(self.show_bookmarks)
        layout.addWidget(bookmarks_btn)
        
        # History button
        history_btn = QPushButton('⏱ History')
        history_btn.clicked.connect(self.show_history)
        layout.addWidget(history_btn)
        
        # Custom Shortcuts button
        shortcuts_btn = QPushButton('⭐ Custom Shortcuts')
        shortcuts_btn.clicked.connect(self.manage_shortcuts)
        layout.addWidget(shortcuts_btn)
        
        # Downloads button
        downloads_btn = QPushButton('⬇ Downloads')
        downloads_btn.clicked.connect(self.show_downloads)
        layout.addWidget(downloads_btn)
        
        # Settings button
        settings_btn = QPushButton('⚙ Settings')
        settings_btn.clicked.connect(self.show_settings)
        layout.addWidget(settings_btn)
        
        # Developer tools button
        dev_btn = QPushButton('🔧 Developer Tools')
        dev_btn.clicked.connect(self.show_dev_tools)
        layout.addWidget(dev_btn)
        
        # Extensions button
        extensions_btn = QPushButton('🧩 Extensions')
        extensions_btn.clicked.connect(lambda: self.show_message('Extensions feature coming soon!'))
        layout.addWidget(extensions_btn)
        
        # Clear cache button
        cache_btn = QPushButton('🗑 Clear Cache')
        cache_btn.clicked.connect(self.clear_cache)
        layout.addWidget(cache_btn)
        
        # Exit button
        exit_btn = QPushButton('❌ Exit')
        exit_btn.clicked.connect(self.close)
        layout.addWidget(exit_btn)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def show_bookmarks(self):
        """Show bookmarks dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle('Bookmarks')
        dialog.setGeometry(100, 100, 500, 400)
        
        layout = QVBoxLayout()
        
        if not self.bookmarks:
            label = QLabel('No bookmarks yet!')
            layout.addWidget(label)
        else:
            bookmarks_list = QListWidget()
            for bookmark in self.bookmarks:
                item = QListWidgetItem(bookmark['title'])
                item.setData(1, bookmark['url'])
                bookmarks_list.addItem(item)
            
            bookmarks_list.itemDoubleClicked.connect(lambda item: self.load_bookmark(item))
            layout.addWidget(bookmarks_list)
            
            # Delete selected button
            delete_btn = QPushButton('Delete Selected')
            delete_btn.clicked.connect(lambda: self.delete_bookmark(bookmarks_list, dialog))
            layout.addWidget(delete_btn)
        
        close_btn = QPushButton('Close')
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def load_bookmark(self, item):
        """Load a bookmarked page"""
        url = item.data(1)
        current_tab = self.tabs.currentWidget()
        current_tab.load_url(url)
    
    def delete_bookmark(self, bookmarks_list, dialog):
        """Delete selected bookmark"""
        for item in bookmarks_list.selectedItems():
            url = item.data(1)
            self.bookmarks = [b for b in self.bookmarks if b['url'] != url]
            bookmarks_list.takeItem(bookmarks_list.row(item))
        self.save_data()
    
    def show_history(self):
        """Show history dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle('History')
        dialog.setGeometry(100, 100, 500, 400)
        
        layout = QVBoxLayout()
        
        if not self.history:
            label = QLabel('No history yet!')
            layout.addWidget(label)
        else:
            history_list = QListWidget()
            for url in reversed(self.history[-50:]):  # Show last 50 items
                item = QListWidgetItem(url)
                history_list.addItem(item)
            
            history_list.itemDoubleClicked.connect(lambda item: self.navigate_to_history(item))
            layout.addWidget(history_list)
            
            # Clear history button
            clear_btn = QPushButton('Clear All History')
            clear_btn.clicked.connect(self.clear_history)
            layout.addWidget(clear_btn)
        
        close_btn = QPushButton('Close')
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def navigate_to_history(self, item):
        """Navigate to a history item"""
        url = item.text()
        current_tab = self.tabs.currentWidget()
        current_tab.load_url(url)
    
    def clear_history(self):
        """Clear browsing history"""
        self.history = []
        self.save_data()
        self.show_message('History cleared!')
    
    def show_settings(self):
        """Show settings dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle('Settings')
        dialog.setGeometry(100, 100, 500, 600)
        
        layout = QVBoxLayout()
        
        label = QLabel('⚙ Browser Settings')
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        label.setFont(font)
        layout.addWidget(label)
        
        # Dark Mode Toggle
        dark_mode_layout = QHBoxLayout()
        dark_mode_checkbox = QCheckBox('🌙 Dark Mode')
        dark_mode_checkbox.setChecked(self.settings['dark_mode'])
        dark_mode_checkbox.stateChanged.connect(lambda: self.toggle_dark_mode())
        dark_mode_layout.addWidget(dark_mode_checkbox)
        dark_mode_layout.addStretch()
        layout.addLayout(dark_mode_layout)
        
        # Zoom Level
        zoom_layout = QHBoxLayout()
        zoom_label = QLabel('🔍 Zoom Level:')
        zoom_spinner = QSpinBox()
        zoom_spinner.setMinimum(50)
        zoom_spinner.setMaximum(200)
        zoom_spinner.setValue(self.settings['default_zoom'])
        zoom_spinner.setSuffix('%')
        zoom_spinner.valueChanged.connect(lambda val: self.change_zoom(val))
        zoom_layout.addWidget(zoom_label)
        zoom_layout.addWidget(zoom_spinner)
        zoom_layout.addStretch()
        layout.addLayout(zoom_layout)
        
        # Font Size
        font_layout = QHBoxLayout()
        font_label = QLabel('📝 Font Size:')
        font_spinner = QSpinBox()
        font_spinner.setMinimum(8)
        font_spinner.setMaximum(24)
        font_spinner.setValue(self.settings['font_size'])
        font_spinner.setSuffix('px')
        font_spinner.valueChanged.connect(lambda val: self.change_font_size(val))
        font_layout.addWidget(font_label)
        font_layout.addWidget(font_spinner)
        font_layout.addStretch()
        layout.addLayout(font_layout)
        
        # Auto-recover tabs
        recovery_layout = QHBoxLayout()
        recovery_checkbox = QCheckBox('↩️ Auto-Recover Tabs on Startup')
        recovery_checkbox.setChecked(self.settings['auto_recover_tabs'])
        recovery_checkbox.stateChanged.connect(lambda: self.toggle_recovery())
        recovery_layout.addWidget(recovery_checkbox)
        recovery_layout.addStretch()
        layout.addLayout(recovery_layout)
        
        # Clear History on Exit
        clear_layout = QHBoxLayout()
        clear_btn = QPushButton('🗑 Clear Browsing Data')
        clear_btn.clicked.connect(self.clear_all_data)
        clear_layout.addWidget(clear_btn)
        clear_layout.addStretch()
        layout.addLayout(clear_layout)
        
        # Reset to Default
        reset_layout = QHBoxLayout()
        reset_btn = QPushButton('🔄 Reset to Default Settings')
        reset_btn.clicked.connect(self.reset_settings)
        reset_layout.addWidget(reset_btn)
        reset_layout.addStretch()
        layout.addLayout(reset_layout)
        
        # About
        about_layout = QHBoxLayout()
        about_btn = QPushButton('ℹ️ About MyBrowser')
        about_btn.clicked.connect(lambda: self.show_message('MyBrowser v2.0 Enhanced Edition\n\nFeatures:\n✅ Dark Mode\n✅ Tab Recovery\n✅ Download Manager\n✅ Better Error Handling\n✅ Full Customization\n\nMade with ❤️ in Python'))
        about_layout.addWidget(about_btn)
        about_layout.addStretch()
        layout.addLayout(about_layout)
        
        layout.addStretch()
        
        close_btn = QPushButton('Close')
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def toggle_dark_mode(self):
        """Toggle dark mode"""
        self.settings['dark_mode'] = not self.settings['dark_mode']
        self.apply_theme()
        self.save_data()
    
    def change_zoom(self, value):
        """Change zoom level"""
        self.settings['default_zoom'] = value
        current_tab = self.tabs.currentWidget()
        if current_tab:
            current_tab.web_view.setZoomFactor(value / 100)
        self.save_data()
    
    def change_font_size(self, value):
        """Change font size"""
        self.settings['font_size'] = value
        self.save_data()
    
    def toggle_recovery(self):
        """Toggle tab recovery"""
        self.settings['auto_recover_tabs'] = not self.settings['auto_recover_tabs']
        self.save_data()
    
    def clear_all_data(self):
        """Clear all browsing data"""
        reply = QMessageBox.question(self, 'Clear Browsing Data', 
                                     'This will clear history, cookies, and cache.\nContinue?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.history = []
            self.downloads = []
            self.save_data()
            self.show_message('Browsing data cleared!')
    
    def reset_settings(self):
        """Reset to default settings"""
        reply = QMessageBox.question(self, 'Reset Settings', 
                                     'Reset all settings to defaults?\nContinue?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.settings = {
                'dark_mode': False,
                'default_zoom': 100,
                'font_size': 14,
                'home_page_url': 'home',
                'auto_recover_tabs': True
            }
            self.apply_theme()
            self.save_data()
            self.show_message('Settings reset to default!')
    
    def show_downloads(self):
        """Show downloads manager"""
        dialog = QDialog(self)
        dialog.setWindowTitle('Downloads')
        dialog.setGeometry(100, 100, 600, 400)
        
        layout = QVBoxLayout()
        
        label = QLabel('⬇ Download Manager')
        font = QFont()
        font.setBold(True)
        label.setFont(font)
        layout.addWidget(label)
        
        if not self.downloads:
            empty_label = QLabel('📭 No downloads yet!')
            layout.addWidget(empty_label)
        else:
            downloads_list = QListWidget()
            for download in reversed(self.downloads):
                item_text = f"{download['name']} - {download['size']} ({download['date']})"
                item = QListWidgetItem(item_text)
                downloads_list.addItem(item)
            layout.addWidget(downloads_list)
            
            # Clear downloads button
            clear_btn = QPushButton('🗑 Clear All Downloads')
            clear_btn.clicked.connect(self.clear_downloads)
            layout.addWidget(clear_btn)
        
        close_btn = QPushButton('Close')
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def clear_downloads(self):
        """Clear all downloads"""
        self.downloads = []
        self.save_data()
        self.show_message('Downloads cleared!')
    
    def manage_shortcuts(self):
        """Manage custom shortcuts"""
        dialog = QDialog(self)
        dialog.setWindowTitle('Manage Custom Shortcuts')
        dialog.setGeometry(100, 100, 600, 500)
        
        layout = QVBoxLayout()
        
        label = QLabel('⭐ Your Custom Shortcuts')
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        label.setFont(font)
        layout.addWidget(label)
        
        # Display current shortcuts
        shortcuts_list = QListWidget()
        for i, shortcut in enumerate(self.custom_shortcuts):
            item_text = f"{shortcut['icon']} {shortcut['name']} → {shortcut['url']}"
            item = QListWidgetItem(item_text)
            item.setData(1, i)
            shortcuts_list.addItem(item)
        
        layout.addWidget(shortcuts_list)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Add new shortcut button
        add_btn = QPushButton('➕ Add New Shortcut')
        add_btn.clicked.connect(lambda: self.add_new_shortcut(shortcuts_list, dialog))
        button_layout.addWidget(add_btn)
        
        # Delete selected button
        delete_btn = QPushButton('🗑 Delete Selected')
        delete_btn.clicked.connect(lambda: self.delete_shortcut(shortcuts_list, dialog))
        button_layout.addWidget(delete_btn)
        
        layout.addLayout(button_layout)
        
        close_btn = QPushButton('Close')
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def add_new_shortcut(self, shortcuts_list, parent_dialog):
        """Add a new custom shortcut"""
        dialog = QDialog(parent_dialog)
        dialog.setWindowTitle('Add New Shortcut')
        dialog.setGeometry(150, 150, 500, 300)
        
        layout = QVBoxLayout()
        
        # Name input
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel('📝 Shortcut Name:'))
        name_input = QLineEdit()
        name_input.setPlaceholderText('e.g., My Website')
        name_layout.addWidget(name_input)
        layout.addLayout(name_layout)
        
        # URL input
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel('🔗 Website URL:'))
        url_input = QLineEdit()
        url_input.setPlaceholderText('e.g., https://www.example.com')
        url_layout.addWidget(url_input)
        layout.addLayout(url_layout)
        
        # Icon/Emoji input
        icon_layout = QHBoxLayout()
        icon_layout.addWidget(QLabel('😊 Icon/Emoji:'))
        icon_input = QLineEdit()
        icon_input.setPlaceholderText('e.g., 🎨 or 🌟')
        icon_input.setMaximumWidth(100)
        icon_layout.addWidget(icon_input)
        icon_layout.addStretch()
        layout.addLayout(icon_layout)
        
        # Info text
        info_label = QLabel('✓ Fill in all fields and click Save')
        info_label.setStyleSheet('color: #666; font-size: 12px;')
        layout.addWidget(info_label)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton('✓ Save Shortcut')
        save_btn.clicked.connect(lambda: self.save_shortcut(
            name_input.text(), 
            url_input.text(), 
            icon_input.text() or '🌐',
            dialog,
            shortcuts_list
        ))
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton('✗ Cancel')
        cancel_btn.clicked.connect(dialog.close)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def save_shortcut(self, name, url, icon, dialog, shortcuts_list):
        """Save a new shortcut"""
        if not name or not url:
            self.show_message('❌ Please fill in all required fields!')
            return
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        shortcut = {
            'name': name,
            'url': url,
            'icon': icon
        }
        
        self.custom_shortcuts.append(shortcut)
        self.save_data()
        self.show_message(f'✓ Shortcut "{name}" added!')
        dialog.close()
        
        # Update the list
        item_text = f"{icon} {name} → {url}"
        item = QListWidgetItem(item_text)
        item.setData(1, len(self.custom_shortcuts) - 1)
        shortcuts_list.addItem(item)
    
    def delete_shortcut(self, shortcuts_list, dialog):
        """Delete selected shortcut"""
        selected_items = shortcuts_list.selectedItems()
        if not selected_items:
            self.show_message('⚠️ Please select a shortcut to delete!')
            return
        
        for item in selected_items:
            index = item.data(1)
            if 0 <= index < len(self.custom_shortcuts):
                deleted = self.custom_shortcuts.pop(index)
                self.show_message(f'✓ Shortcut "{deleted["name"]}" deleted!')
        
        self.save_data()
        shortcuts_list.clear()
        
        # Refresh the list
        for i, shortcut in enumerate(self.custom_shortcuts):
            item_text = f"{shortcut['icon']} {shortcut['name']} → {shortcut['url']}"
            item = QListWidgetItem(item_text)
            item.setData(1, i)
            shortcuts_list.addItem(item)
    
    def show_dev_tools(self):
        """Show developer tools"""
        dialog = QDialog(self)
        dialog.setWindowTitle('Developer Tools')
        dialog.setGeometry(100, 100, 600, 400)
        
        layout = QVBoxLayout()
        
        label = QLabel('🔧 Developer Tools')
        font = QFont()
        font.setBold(True)
        label.setFont(font)
        layout.addWidget(label)
        
        tools = [
            '📋 Elements Inspector',
            '🎨 Styles',
            '⚙ Console',
            '🔍 Debugger',
            '🚀 Performance',
            '📡 Network',
            '💾 Storage',
            '🔌 Application'
        ]
        
        for tool in tools:
            btn = QPushButton(tool)
            btn.clicked.connect(lambda checked, t=tool: self.show_message(f'{t} is a premium feature in this version!'))
            layout.addWidget(btn)
        
        close_btn = QPushButton('Close')
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def clear_cache(self):
        """Clear browser cache"""
        reply = QMessageBox.question(self, 'Clear Cache', 
                                     'Clear browser cache and temporary files?\nContinue?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.show_message('Cache cleared!')
    
    def show_home_page(self, tab):
        """Show home page"""
        # Generate custom shortcuts HTML
        custom_shortcuts_html = ""
        if self.custom_shortcuts:
            custom_shortcuts_html = '<div class="shortcuts-title">⭐ Your Custom Shortcuts</div><div class="shortcuts">'
            for shortcut in self.custom_shortcuts:
                custom_shortcuts_html += f'''
                    <a href="{shortcut['url']}" class="shortcut">
                        <div class="shortcut-icon">{shortcut['icon']}</div>
                        <div class="shortcut-name">{shortcut['name']}</div>
                    </a>
                '''
            custom_shortcuts_html += '</div>'
        
        html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    margin: 0;
                    padding: 20px;
                    color: white;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 50px auto;
                }}
                h1 {{
                    font-size: 48px;
                    margin: 0 0 10px 0;
                    text-align: center;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                }}
                .subtitle {{
                    text-align: center;
                    opacity: 0.9;
                    margin-bottom: 30px;
                }}
                .search-box {{
                    text-align: center;
                    margin: 30px 0;
                }}
                input {{
                    width: 100%;
                    max-width: 600px;
                    padding: 12px;
                    font-size: 16px;
                    border: none;
                    border-radius: 24px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.2);
                }}
                .shortcuts-title {{
                    font-size: 20px;
                    margin: 40px 0 20px 0;
                    font-weight: bold;
                    text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
                }}
                .shortcuts {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                    gap: 15px;
                    margin-bottom: 40px;
                }}
                a.shortcut {{
                    background: rgba(255,255,255,0.1);
                    padding: 20px;
                    border-radius: 12px;
                    cursor: pointer;
                    transition: all 0.3s;
                    text-decoration: none;
                    color: white;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    min-height: 130px;
                    backdrop-filter: blur(5px);
                    border: 1px solid rgba(255,255,255,0.2);
                }}
                a.shortcut:hover {{
                    background: rgba(255,255,255,0.2);
                    transform: translateY(-5px);
                    box-shadow: 0 8px 15px rgba(0,0,0,0.2);
                }}
                .shortcut-icon {{
                    font-size: 36px;
                    margin-bottom: 10px;
                }}
                .shortcut-name {{
                    font-size: 12px;
                    text-align: center;
                    word-wrap: break-word;
                    font-weight: 500;
                }}
                footer {{
                    text-align: center;
                    margin-top: 50px;
                    opacity: 0.8;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>MyBrowser</h1>
                <p class="subtitle">Fast • Secure • Simple</p>
                
                <div class="search-box">
                    <input type="text" placeholder="Search or enter website URL" onkeypress="if(event.key=='Enter'){{window.location.href='https://www.google.com/search?q='+encodeURIComponent(this.value);}}">
                </div>
                
                {custom_shortcuts_html}
                
                <div class="shortcuts-title">🌐 Quick Links</div>
                <div class="shortcuts">
                    <a href="https://www.google.com" class="shortcut">
                        <div class="shortcut-icon">🔍</div>
                        <div class="shortcut-name">Google</div>
                    </a>
                    <a href="https://www.gmail.com" class="shortcut">
                        <div class="shortcut-icon">📧</div>
                        <div class="shortcut-name">Gmail</div>
                    </a>
                    <a href="https://www.youtube.com" class="shortcut">
                        <div class="shortcut-icon">📺</div>
                        <div class="shortcut-name">YouTube</div>
                    </a>
                    <a href="https://www.facebook.com" class="shortcut">
                        <div class="shortcut-icon">📘</div>
                        <div class="shortcut-name">Facebook</div>
                    </a>
                    <a href="https://www.instagram.com" class="shortcut">
                        <div class="shortcut-icon">📷</div>
                        <div class="shortcut-name">Instagram</div>
                    </a>
                    <a href="https://www.twitter.com" class="shortcut">
                        <div class="shortcut-icon">𝕏</div>
                        <div class="shortcut-name">Twitter</div>
                    </a>
                    <a href="https://www.linkedin.com" class="shortcut">
                        <div class="shortcut-icon">💼</div>
                        <div class="shortcut-name">LinkedIn</div>
                    </a>
                    <a href="https://www.reddit.com" class="shortcut">
                        <div class="shortcut-icon">🔴</div>
                        <div class="shortcut-name">Reddit</div>
                    </a>
                    <a href="https://www.github.com" class="shortcut">
                        <div class="shortcut-icon">🐙</div>
                        <div class="shortcut-name">GitHub</div>
                    </a>
                    <a href="https://www.stackoverflow.com" class="shortcut">
                        <div class="shortcut-icon">💻</div>
                        <div class="shortcut-name">Stack Overflow</div>
                    </a>
                    <a href="https://www.wikipedia.org" class="shortcut">
                        <div class="shortcut-icon">📖</div>
                        <div class="shortcut-name">Wikipedia</div>
                    </a>
                    <a href="https://www.amazon.com" class="shortcut">
                        <div class="shortcut-icon">🛒</div>
                        <div class="shortcut-name">Amazon</div>
                    </a>
                    <a href="https://www.netflix.com" class="shortcut">
                        <div class="shortcut-icon">🎬</div>
                        <div class="shortcut-name">Netflix</div>
                    </a>
                    <a href="https://www.discord.com" class="shortcut">
                        <div class="shortcut-icon">💬</div>
                        <div class="shortcut-name">Discord</div>
                    </a>
                    <a href="https://www.twitch.tv" class="shortcut">
                        <div class="shortcut-icon">🎮</div>
                        <div class="shortcut-name">Twitch</div>
                    </a>
                    <a href="https://www.spotify.com" class="shortcut">
                        <div class="shortcut-icon">🎵</div>
                        <div class="shortcut-name">Spotify</div>
                    </a>
                    <a href="https://www.map.google.com" class="shortcut">
                        <div class="shortcut-icon">🗺️</div>
                        <div class="shortcut-name">Google Maps</div>
                    </a>
                    <a href="https://www.drive.google.com" class="shortcut">
                        <div class="shortcut-icon">☁️</div>
                        <div class="shortcut-name">Google Drive</div>
                    </a>
                    <a href="https://www.canva.com" class="shortcut">
                        <div class="shortcut-icon">🎨</div>
                        <div class="shortcut-name">Canva</div>
                    </a>
                    <a href="https://www.figma.com" class="shortcut">
                        <div class="shortcut-icon">🎭</div>
                        <div class="shortcut-name">Figma</div>
                    </a>
                </div>
                
                <footer>
                    <p>Made with ❤️ in Python | MyBrowser v2.0 Enhanced Edition</p>
                </footer>
            </div>
        </body>
        </html>
        """
        tab.load_html(html)
    
    def save_data(self):
        """Save bookmarks and history to file"""
        data = {
            'bookmarks': self.bookmarks,
            'history': self.history,
            'downloads': self.downloads,
            'custom_shortcuts': self.custom_shortcuts,
            'settings': self.settings,
            'open_tabs': self.get_open_tabs()
        }
        try:
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
        except:
            pass
    
    def load_data(self):
        """Load bookmarks and history from file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.bookmarks = data.get('bookmarks', [])
                    self.history = data.get('history', [])
                    self.downloads = data.get('downloads', [])
                    self.custom_shortcuts = data.get('custom_shortcuts', [])
                    self.settings = data.get('settings', self.settings)
                    self.dark_mode = self.settings.get('dark_mode', False)
            except:
                pass
    
    def get_open_tabs(self):
        """Get list of open tab URLs"""
        tabs = []
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if tab and hasattr(tab, 'url') and tab.url:
                tabs.append(tab.url)
        return tabs
    
    def recover_tabs(self):
        """Recover tabs from last session"""
        if self.settings.get('auto_recover_tabs', True) and os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    open_tabs = data.get('open_tabs', [])
                    if open_tabs:
                        # Remove the default first tab
                        self.tabs.removeTab(0)
                        # Restore saved tabs
                        for url in open_tabs:
                            self.add_tab(url)
            except:
                pass
    
    def show_message(self, message):
        """Show a message dialog"""
        QMessageBox.information(self, 'MyBrowser', message)
    
    def closeEvent(self, event):
        """Handle window close event"""
        self.save_data()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    browser = Browser()
    sys.exit(app.exec())
