import sys
import os
import shutil
import json
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSlot, QUrl, QDir, pyqtSignal
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtGui import QIcon

from game_state import GameStateManager

class Backend(QObject):
    """Backend class for handling JavaScript calls from the web page."""
    
    # Signal to send data to JavaScript
    stateChanged = pyqtSignal(str)
    
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.state_manager = GameStateManager()
    
    @pyqtSlot()
    def exit_app(self):
        """Exit the application when called from JavaScript."""
        print("Exit app called from JavaScript")
        QApplication.quit()
    
    @pyqtSlot(str)
    def start_game(self, character_name="Hero"):
        """Start the game when called from JavaScript."""
        print(f"Start game called from JavaScript with character name: {character_name}")
        
        # Start a new game
        game_state = self.state_manager.new_game()
        
        # Set the character name
        if character_name and character_name.strip():
            game_state["player"]["name"] = character_name.strip()
            self.state_manager.current_state.player["name"] = character_name.strip()
        
        # Emit the state to JavaScript
        self.stateChanged.emit(json.dumps(game_state))
        
        # Load the game.html file
        appdata_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "appdata")
        game_path = os.path.join(appdata_dir, "game.html")
        self.app.view.load(QUrl.fromLocalFile(game_path))
    
    @pyqtSlot()
    def return_to_menu(self):
        """Return to the main menu when called from JavaScript."""
        print("Return to menu called from JavaScript")
        # Load the index.html file
        appdata_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "appdata")
        menu_path = os.path.join(appdata_dir, "index.html")
        self.app.view.load(QUrl.fromLocalFile(menu_path))
    
    @pyqtSlot(result=str)
    def save_game(self):
        """Save the current game state."""
        print("Save game called from JavaScript")
        
        # Use the character name as the save file name
        character_name = self.state_manager.current_state.player["name"]
        slot_name = f"{character_name}_{int(self.state_manager.current_state.timestamp)}"
        
        result = self.state_manager.save_game(slot_name)
        return json.dumps(result)
    
    @pyqtSlot(str, result=str)
    def load_game(self, slot_name):
        """Load a game state."""
        print(f"Load game called from JavaScript with slot: {slot_name}")
        result = self.state_manager.load_game(slot_name)
        
        if result["success"]:
            # If the load was successful, emit the state to JavaScript
            self.stateChanged.emit(json.dumps(result["state"]))
            
            # Load the game.html file
            appdata_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "appdata")
            game_path = os.path.join(appdata_dir, "game.html")
            self.app.view.load(QUrl.fromLocalFile(game_path))
        
        return json.dumps(result)
    
    @pyqtSlot(result=str)
    def get_save_files(self):
        """Get a list of available save files."""
        print("Get save files called from JavaScript")
        save_files = self.state_manager.get_save_files()
        return json.dumps(save_files)
    
    @pyqtSlot(str, result=str)
    def delete_save(self, slot_name):
        """Delete a save file."""
        print(f"Delete save called from JavaScript with slot: {slot_name}")
        result = self.state_manager.delete_save(slot_name)
        return json.dumps(result)
    
    @pyqtSlot(result=str)
    def get_current_state(self):
        """Get the current game state."""
        print("Get current state called from JavaScript")
        state = self.state_manager.get_current_state()
        return json.dumps(state)
    
    @pyqtSlot(str, result=str)
    def update_state(self, updates_json):
        """Update the current game state."""
        print("Update state called from JavaScript")
        try:
            updates = json.loads(updates_json)
            state = self.state_manager.update_state(updates)
            return json.dumps({"success": True, "state": state})
        except Exception as e:
            return json.dumps({"success": False, "message": str(e)})
    
    @pyqtSlot()
    def load_game_screen(self):
        """Navigate to the load game screen."""
        print("Load game screen called from JavaScript")
        # Load the load_game.html file
        appdata_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "appdata")
        load_game_path = os.path.join(appdata_dir, "load_game.html")
        self.app.view.load(QUrl.fromLocalFile(load_game_path))


class GameApp:
    """Main application class for the RPG game."""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.view = QWebEngineView()
        
        # Set up the web view
        self.setup_web_view()
        
        # Set up the web channel for JS-Python communication
        self.setup_web_channel()
        
        # Load the HTML file
        self.load_html()
    
    def setup_web_view(self):
        """Configure the web view settings."""
        # Set window size to 1280x720
        self.view.resize(1280, 720)
        
        # Center the window on the screen
        screen_geometry = self.app.primaryScreen().geometry()
        x = (screen_geometry.width() - self.view.width()) // 2
        y = (screen_geometry.height() - self.view.height()) // 2
        self.view.move(x, y)
        
        # Set window title
        self.view.setWindowTitle("RPG Game")
        
        # Enable developer tools (F12)
        self.view.page().settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        self.view.page().settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        self.view.page().settings().setAttribute(QWebEngineSettings.WebAttribute.ErrorPageEnabled, True)
        
        # Connect to loadFinished signal to debug
        self.view.loadFinished.connect(self.on_load_finished)
    
    def on_load_finished(self, success):
        """Called when the page has finished loading."""
        if success:
            print("Page loaded successfully")
        else:
            print("Failed to load page")
    
    def setup_web_channel(self):
        """Set up the web channel for JS-Python communication."""
        # Create a web channel and backend object
        self.channel = QWebChannel()
        self.backend = Backend(self)
        
        # Register the backend object with the web channel
        self.channel.registerObject("backend", self.backend)
        
        # Set the web channel on the web page
        self.view.page().setWebChannel(self.channel)
    
    def load_html(self):
        """Load the HTML file from the AppData directory."""
        # Get the AppData directory path
        appdata_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "appdata")
        
        # Load the HTML file
        html_path = os.path.join(appdata_dir, "index.html")
        self.view.load(QUrl.fromLocalFile(html_path))
    
    def run(self):
        """Run the application."""
        self.view.show()
        return self.app.exec()


if __name__ == "__main__":
    app = GameApp()
    sys.exit(app.run())
