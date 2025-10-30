"""
Command Palette for RAGGITY ZYZTEM

Quick launcher for common actions, activated with Ctrl+K.
Inspired by VS Code's command palette.
"""

import customtkinter as ctk
from typing import Callable, List, Dict, Any
from .theme import (
    DARK_BG, CARD_BG, ACCENT, TEXT, TEXT_SECONDARY,
    body, small, heading
)


class CommandPalette(ctk.CTkToplevel):
    """
    Command palette window with fuzzy search.
    
    Usage:
        palette = CommandPalette(parent, commands)
        palette.show()
    """
    
    def __init__(self, parent, commands: List[Dict[str, Any]]):
        """
        Initialize command palette.
        
        Args:
            parent: Parent window
            commands: List of command dictionaries with:
                - name: Display name
                - action: Callable to execute
                - description: Optional description
                - category: Optional category
        """
        super().__init__(parent)
        
        self.parent_window = parent
        self.commands = commands
        self.filtered_commands = commands
        self.selected_index = 0
        
        # Window setup
        self.title("Command Palette")
        self.geometry("600x400")
        self.resizable(False, False)
        
        # Make it modal-ish
        self.transient(parent)
        self.grab_set()
        
        # Style
        self.configure(fg_color=DARK_BG)
        
        # Center on parent
        self.center_on_parent()
        
        # Create UI
        self.create_widgets()
        
        # Bind keys
        self.bind("<Escape>", lambda e: self.close())
        self.bind("<Return>", lambda e: self.execute_selected())
        self.bind("<Up>", lambda e: self.move_selection(-1))
        self.bind("<Down>", lambda e: self.move_selection(1))
        
        # Focus search
        self.search_entry.focus_set()
    
    def center_on_parent(self):
        """Center the palette on the parent window"""
        self.update_idletasks()
        
        # Get parent geometry
        parent_x = self.parent_window.winfo_x()
        parent_y = self.parent_window.winfo_y()
        parent_w = self.parent_window.winfo_width()
        parent_h = self.parent_window.winfo_height()
        
        # Calculate center position
        x = parent_x + (parent_w - 600) // 2
        y = parent_y + (parent_h - 400) // 2
        
        self.geometry(f"+{x}+{y}")
    
    def create_widgets(self):
        """Create palette UI"""
        # Title
        title_label = ctk.CTkLabel(
            self,
            text="⚡ Command Palette",
            font=heading(),
            text_color=ACCENT
        )
        title_label.pack(pady=(20, 10))
        
        # Search box
        self.search_entry = ctk.CTkEntry(
            self,
            placeholder_text="Type to search commands...",
            height=40,
            font=body()
        )
        self.search_entry.pack(padx=20, pady=10, fill="x")
        self.search_entry.bind("<KeyRelease>", self.on_search)
        
        # Hint
        hint = ctk.CTkLabel(
            self,
            text="↑↓ Navigate  •  Enter Execute  •  Esc Close",
            font=small(),
            text_color=TEXT_SECONDARY
        )
        hint.pack(pady=5)
        
        # Commands frame
        commands_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=CARD_BG,
            corner_radius=8
        )
        commands_frame.pack(padx=20, pady=10, fill="both", expand=True)
        
        self.commands_container = commands_frame
        
        # Populate initial commands
        self.update_command_list()
    
    def on_search(self, event=None):
        """Handle search input"""
        query = self.search_entry.get().lower().strip()
        
        if not query:
            self.filtered_commands = self.commands
        else:
            # Simple fuzzy search
            self.filtered_commands = [
                cmd for cmd in self.commands
                if query in cmd['name'].lower() or 
                   query in cmd.get('description', '').lower() or
                   query in cmd.get('category', '').lower()
            ]
        
        self.selected_index = 0
        self.update_command_list()
    
    def update_command_list(self):
        """Update the displayed command list"""
        # Clear existing
        for widget in self.commands_container.winfo_children():
            widget.destroy()
        
        # Show filtered commands
        if not self.filtered_commands:
            no_results = ctk.CTkLabel(
                self.commands_container,
                text="No commands found",
                font=body(),
                text_color=TEXT_SECONDARY
            )
            no_results.pack(pady=20)
            return
        
        for idx, cmd in enumerate(self.filtered_commands):
            self.create_command_item(idx, cmd)
    
    def create_command_item(self, idx: int, cmd: Dict[str, Any]):
        """Create a command list item with category grouping"""
        is_selected = idx == self.selected_index
        
        # Show category header if this is first item in category
        category = cmd.get('category', '')
        if idx == 0 or (idx > 0 and self.filtered_commands[idx-1].get('category') != category):
            if category:
                category_header = ctk.CTkLabel(
                    self.commands_container,
                    text=category.upper(),
                    font=small(),
                    text_color=TEXT_SECONDARY,
                    anchor="w"
                )
                category_header.pack(fill="x", padx=10, pady=(10, 5) if idx > 0 else (0, 5))
        
        # Command frame
        frame = ctk.CTkFrame(
            self.commands_container,
            fg_color=ACCENT if is_selected else "transparent",
            corner_radius=6
        )
        frame.pack(fill="x", padx=5, pady=2)
        
        # Make clickable
        frame.bind("<Button-1>", lambda e, i=idx: self.select_and_execute(i))
        
        # Command name and description
        text_container = ctk.CTkFrame(frame, fg_color="transparent")
        text_container.pack(side="left", fill="both", expand=True, padx=10, pady=8)
        text_container.bind("<Button-1>", lambda e, i=idx: self.select_and_execute(i))
        
        # Command name
        name_label = ctk.CTkLabel(
            text_container,
            text=cmd['name'],
            font=body(),
            text_color="#000000" if is_selected else TEXT,
            anchor="w"
        )
        name_label.pack(anchor="w")
        name_label.bind("<Button-1>", lambda e, i=idx: self.select_and_execute(i))
        
        # Description (if present)
        description = cmd.get('description', '')
        if description:
            desc_label = ctk.CTkLabel(
                text_container,
                text=description,
                font=small(),
                text_color="#333333" if is_selected else TEXT_SECONDARY,
                anchor="w"
            )
            desc_label.pack(anchor="w")
            desc_label.bind("<Button-1>", lambda e, i=idx: self.select_and_execute(i))
    
    def move_selection(self, delta: int):
        """Move selection up or down"""
        if not self.filtered_commands:
            return
        
        self.selected_index = (self.selected_index + delta) % len(self.filtered_commands)
        self.update_command_list()
    
    def select_and_execute(self, index: int):
        """Select item by index and execute"""
        self.selected_index = index
        self.execute_selected()
    
    def execute_selected(self):
        """Execute the selected command"""
        if not self.filtered_commands or self.selected_index >= len(self.filtered_commands):
            return
        
        cmd = self.filtered_commands[self.selected_index]
        action = cmd.get('action')
        
        if action and callable(action):
            self.close()
            # Execute after closing to avoid modal issues
            self.parent_window.after(100, action)
    
    def close(self):
        """Close the palette"""
        self.grab_release()
        self.destroy()
    
    def show(self):
        """Show the palette (for API consistency)"""
        pass  # Already shown in __init__

