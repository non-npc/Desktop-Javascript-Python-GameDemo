import os
import json
import time
from datetime import datetime

class GameState:
    """Class to represent the state of the game."""
    
    def __init__(self):
        # Player stats
        self.player = {
            "name": "Hero",
            "level": 1,
            "hp": 100,
            "max_hp": 100,
            "mp": 50,
            "max_mp": 50,
            "gold": 100,
            "exp": 0,
            "next_level_exp": 100,
            "position": {"x": 0, "y": 0, "map": "world_map"}
        }
        
        # Inventory
        self.inventory = [
            {"id": "healing_potion", "name": "Healing Potion", "quantity": 3, "type": "consumable"},
            {"id": "mana_potion", "name": "Mana Potion", "quantity": 2, "type": "consumable"},
            {"id": "bronze_sword", "name": "Bronze Sword", "quantity": 1, "type": "weapon"},
            {"id": "leather_armor", "name": "Leather Armor", "quantity": 1, "type": "armor"},
            {"id": "wooden_shield", "name": "Wooden Shield", "quantity": 1, "type": "shield"}
        ]
        
        # Quests
        self.quests = [
            {"id": "goblin_king", "name": "Defeat the Goblin King", "status": "active", "progress": 0, "max_progress": 1},
            {"id": "lost_artifact", "name": "Find the Lost Artifact", "status": "active", "progress": 0, "max_progress": 1}
        ]
        
        # Game progress
        self.progress = {
            "visited_locations": [],
            "completed_quests": [],
            "killed_enemies": {},
            "discovered_items": []
        }
        
        # Game settings
        self.settings = {
            "difficulty": "normal",
            "music_volume": 0.7,
            "sfx_volume": 0.8,
            "fullscreen": False
        }
        
        # Timestamp
        self.timestamp = time.time()
        self.playtime = 0  # in seconds
    
    def to_dict(self):
        """Convert the game state to a dictionary."""
        return {
            "player": self.player,
            "inventory": self.inventory,
            "quests": self.quests,
            "progress": self.progress,
            "settings": self.settings,
            "timestamp": self.timestamp,
            "playtime": self.playtime
        }
    
    def from_dict(self, data):
        """Load the game state from a dictionary."""
        self.player = data.get("player", self.player)
        self.inventory = data.get("inventory", self.inventory)
        self.quests = data.get("quests", self.quests)
        self.progress = data.get("progress", self.progress)
        self.settings = data.get("settings", self.settings)
        self.timestamp = data.get("timestamp", self.timestamp)
        self.playtime = data.get("playtime", self.playtime)


class GameStateManager:
    """Class to manage saving and loading game states."""
    
    def __init__(self):
        self.current_state = GameState()
        self.saves_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saves")
        
        # Create saves directory if it doesn't exist
        if not os.path.exists(self.saves_dir):
            os.makedirs(self.saves_dir)
    
    def new_game(self):
        """Start a new game with default state."""
        self.current_state = GameState()
        return self.current_state.to_dict()
    
    def save_game(self, slot_name=None):
        """Save the current game state to a file."""
        # Update timestamp
        self.current_state.timestamp = time.time()
        
        # Generate a filename if not provided
        if slot_name is None:
            timestamp = datetime.fromtimestamp(self.current_state.timestamp)
            slot_name = f"save_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        # Ensure the filename has a .json extension
        if not slot_name.endswith(".json"):
            slot_name += ".json"
        
        # Save the game state to a file
        save_path = os.path.join(self.saves_dir, slot_name)
        with open(save_path, "w") as f:
            json.dump(self.current_state.to_dict(), f, indent=2)
        
        return {
            "success": True,
            "message": f"Game saved to {slot_name}",
            "slot_name": slot_name,
            "timestamp": self.current_state.timestamp
        }
    
    def load_game(self, slot_name):
        """Load a game state from a file."""
        # Ensure the filename has a .json extension
        if not slot_name.endswith(".json"):
            slot_name += ".json"
        
        # Load the game state from a file
        save_path = os.path.join(self.saves_dir, slot_name)
        try:
            with open(save_path, "r") as f:
                data = json.load(f)
            
            self.current_state.from_dict(data)
            
            return {
                "success": True,
                "message": f"Game loaded from {slot_name}",
                "state": self.current_state.to_dict()
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to load game: {str(e)}"
            }
    
    def get_save_files(self):
        """Get a list of available save files."""
        save_files = []
        
        # Get all .json files in the saves directory
        for filename in os.listdir(self.saves_dir):
            if filename.endswith(".json"):
                save_path = os.path.join(self.saves_dir, filename)
                try:
                    # Get the file's modification time
                    mod_time = os.path.getmtime(save_path)
                    
                    # Try to read the player name and level from the save file
                    with open(save_path, "r") as f:
                        data = json.load(f)
                        player_name = data.get("player", {}).get("name", "Unknown")
                        player_level = data.get("player", {}).get("level", 0)
                        timestamp = data.get("timestamp", mod_time)
                    
                    # Add the save file to the list
                    save_files.append({
                        "filename": filename,
                        "player_name": player_name,
                        "player_level": player_level,
                        "timestamp": timestamp,
                        "date": datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                    })
                except:
                    # If there's an error reading the file, add it with minimal information
                    save_files.append({
                        "filename": filename,
                        "player_name": "Unknown",
                        "player_level": 0,
                        "timestamp": mod_time,
                        "date": datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M:%S")
                    })
        
        # Sort the save files by timestamp (newest first)
        save_files.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return save_files
    
    def delete_save(self, slot_name):
        """Delete a save file."""
        # Ensure the filename has a .json extension
        if not slot_name.endswith(".json"):
            slot_name += ".json"
        
        # Delete the save file
        save_path = os.path.join(self.saves_dir, slot_name)
        try:
            os.remove(save_path)
            return {
                "success": True,
                "message": f"Save file {slot_name} deleted"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to delete save file: {str(e)}"
            }
    
    def get_current_state(self):
        """Get the current game state."""
        return self.current_state.to_dict()
    
    def update_state(self, updates):
        """Update the current game state with the provided updates."""
        # Update player stats
        if "player" in updates:
            for key, value in updates["player"].items():
                if key in self.current_state.player:
                    self.current_state.player[key] = value
        
        # Update inventory
        if "inventory" in updates:
            self.current_state.inventory = updates["inventory"]
        
        # Update quests
        if "quests" in updates:
            self.current_state.quests = updates["quests"]
        
        # Update progress
        if "progress" in updates:
            for key, value in updates["progress"].items():
                if key in self.current_state.progress:
                    self.current_state.progress[key] = value
        
        # Update settings
        if "settings" in updates:
            for key, value in updates["settings"].items():
                if key in self.current_state.settings:
                    self.current_state.settings[key] = value
        
        # Update playtime
        if "playtime" in updates:
            self.current_state.playtime = updates["playtime"]
        
        return self.current_state.to_dict() 