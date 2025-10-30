"""
Toast Notification System

Lightweight transient notifications for the UI.
Shows small labels that auto-fade after a delay.
"""

import customtkinter as ctk
from typing import Literal

# Color mapping for toast types
KIND_COLOR = {
    "info": "#4da3ff",
    "success": "#2ecc71",
    "warn": "#f1c40f",
    "error": "#e74c3c",
}

KIND_TEXT_COLOR = {
    "info": "#ffffff",
    "success": "#ffffff",
    "warn": "#000000",
    "error": "#ffffff",
}


class ToastManager:
    """
    Manages transient toast notifications in the UI.
    
    Usage:
        toast = ToastManager(root_window)
        toast.show("Operation complete", "success")
        toast.show("Error occurred", "error", ms=3000)
    """
    
    def __init__(self, root):
        """
        Initialize toast manager.
        
        Args:
            root: Root CTk window or frame
        """
        self.root = root
        self.active_toasts = []
        self.y_offset = 20  # Initial offset from bottom
    
    def show(self, text: str, kind: Literal["info", "success", "warn", "error"] = "info", ms: int = 2200):
        """
        Show a toast notification.
        
        Args:
            text: Message to display
            kind: Toast type (info, success, warn, error)
            ms: Duration in milliseconds before auto-dismiss
        """
        # Get colors
        bg_color = KIND_COLOR.get(kind, KIND_COLOR["info"])
        text_color = KIND_TEXT_COLOR.get(kind, "#ffffff")
        
        # Create toast label
        toast = ctk.CTkLabel(
            self.root,
            text=f"  {text}  ",
            fg_color=bg_color,
            text_color=text_color,
            corner_radius=8,
            font=("Segoe UI", 12),
            padx=15,
            pady=8
        )
        
        # Calculate vertical position (stack toasts)
        y_pos = -self.y_offset
        for _ in self.active_toasts:
            y_pos -= 50  # Stack with 50px spacing
        
        # Position at bottom-right
        toast.place(relx=1.0, rely=1.0, x=-20, y=y_pos, anchor="se")
        
        # Track active toast
        self.active_toasts.append(toast)
        
        # Schedule removal
        def remove_toast():
            try:
                toast.destroy()
                if toast in self.active_toasts:
                    self.active_toasts.remove(toast)
                # Reposition remaining toasts
                self._reposition_toasts()
            except Exception:
                pass
        
        self.root.after(ms, remove_toast)
    
    def _reposition_toasts(self):
        """Reposition remaining toasts after one is removed"""
        y_pos = -self.y_offset
        for toast in self.active_toasts:
            try:
                toast.place(relx=1.0, rely=1.0, x=-20, y=y_pos, anchor="se")
                y_pos -= 50
            except Exception:
                pass
    
    def clear_all(self):
        """Clear all active toasts"""
        for toast in self.active_toasts[:]:
            try:
                toast.destroy()
            except Exception:
                pass
        self.active_toasts.clear()

