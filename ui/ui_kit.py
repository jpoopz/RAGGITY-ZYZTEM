"""
UI component primitives for consistent styling.

Provides reusable components with design token integration.
"""

import customtkinter as ctk
from .tokens import COLOR, SPACE, RADIUS, FONT


class Card(ctk.CTkFrame):
    """
    Card component with consistent styling.
    
    Usage:
        card = Card(parent)
        card.pack(padx=20, pady=10)
    """
    
    def __init__(self, parent, **kwargs):
        # Apply defaults from tokens
        defaults = {
            "fg_color": COLOR["card"],
            "corner_radius": RADIUS["lg"],
            "border_width": 1,
            "border_color": COLOR["border"]
        }
        
        # Override with user kwargs
        defaults.update(kwargs)
        
        super().__init__(parent, **defaults)


class HStack(ctk.CTkFrame):
    """
    Horizontal stack container.
    
    Children are packed side-by-side with consistent spacing.
    
    Usage:
        stack = HStack(parent, spacing="md")
        ctk.CTkLabel(stack, text="Left").pack(side="left")
        ctk.CTkLabel(stack, text="Right").pack(side="left")
    """
    
    def __init__(self, parent, spacing: str = "md", **kwargs):
        defaults = {
            "fg_color": "transparent"
        }
        defaults.update(kwargs)
        
        super().__init__(parent, **defaults)
        self.spacing = SPACE.get(spacing, 12)
    
    def add(self, widget, **pack_kwargs):
        """Add widget to stack with spacing"""
        defaults = {"side": "left", "padx": (0, self.spacing)}
        defaults.update(pack_kwargs)
        widget.pack(**defaults)
        return widget


class VStack(ctk.CTkFrame):
    """
    Vertical stack container.
    
    Children are packed top-to-bottom with consistent spacing.
    
    Usage:
        stack = VStack(parent, spacing="lg")
        ctk.CTkLabel(stack, text="Top").pack()
        ctk.CTkLabel(stack, text="Bottom").pack()
    """
    
    def __init__(self, parent, spacing: str = "md", **kwargs):
        defaults = {
            "fg_color": "transparent"
        }
        defaults.update(kwargs)
        
        super().__init__(parent, **defaults)
        self.spacing = SPACE.get(spacing, 12)
    
    def add(self, widget, **pack_kwargs):
        """Add widget to stack with spacing"""
        defaults = {"pady": (0, self.spacing)}
        defaults.update(pack_kwargs)
        widget.pack(**defaults)
        return widget


class Hairline(ctk.CTkFrame):
    """
    1px separator line.
    
    Usage:
        Hairline(parent).pack(fill="x", pady=10)
    """
    
    def __init__(self, parent, orientation: str = "horizontal", **kwargs):
        defaults = {
            "fg_color": COLOR["border"],
            "height": 1 if orientation == "horizontal" else None,
            "width": 1 if orientation == "vertical" else None
        }
        defaults.update(kwargs)
        
        super().__init__(parent, **defaults)


class DensityManager:
    """
    Global density manager for UI spacing.
    
    Allows switching between Cozy, Comfortable, and Compact layouts.
    """
    
    _current_density = "Comfortable"
    _callbacks = []
    
    @classmethod
    def set(cls, density: str):
        """
        Set global density mode.
        
        Args:
            density: One of "Cozy", "Comfortable", "Compact"
        """
        if density not in ["Cozy", "Comfortable", "Compact"]:
            return
        
        cls._current_density = density
        
        # Notify all registered callbacks
        for callback in cls._callbacks:
            try:
                callback(density)
            except Exception:
                pass
    
    @classmethod
    def get(cls) -> str:
        """Get current density mode"""
        return cls._current_density
    
    @classmethod
    def register_callback(cls, callback):
        """Register callback to be notified of density changes"""
        if callback not in cls._callbacks:
            cls._callbacks.append(callback)
    
    @classmethod
    def get_spacing(cls, key: str) -> int:
        """Get spacing adjusted for current density"""
        from .tokens import get_spacing
        return get_spacing(key, cls._current_density)


class Section(ctk.CTkFrame):
    """
    Collapsible section with header.
    
    Usage:
        section = Section(parent, title="Advanced Options")
        # Add content to section.content_frame
    """
    
    def __init__(self, parent, title: str, collapsed: bool = False, **kwargs):
        defaults = {
            "fg_color": "transparent"
        }
        defaults.update(kwargs)
        
        super().__init__(parent, **defaults)
        
        self.collapsed = collapsed
        
        # Header button
        self.header_btn = ctk.CTkButton(
            self,
            text=f"{'▶' if collapsed else '▼'} {title}",
            command=self.toggle,
            fg_color="transparent",
            hover_color=COLOR["bg/2"],
            anchor="w",
            font=FONT["h3"]
        )
        self.header_btn.pack(fill="x", pady=(0, SPACE["sm"]))
        
        # Content frame
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        if not collapsed:
            self.content_frame.pack(fill="both", expand=True, padx=SPACE["md"])
    
    def toggle(self):
        """Toggle section visibility"""
        self.collapsed = not self.collapsed
        
        if self.collapsed:
            self.content_frame.pack_forget()
            # Update header
            text = self.header_btn.cget("text")
            self.header_btn.configure(text=text.replace("▼", "▶"))
        else:
            self.content_frame.pack(fill="both", expand=True, padx=SPACE["md"])
            # Update header
            text = self.header_btn.cget("text")
            self.header_btn.configure(text=text.replace("▶", "▼"))


