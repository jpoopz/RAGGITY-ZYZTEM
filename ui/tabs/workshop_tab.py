"""
Garment Workshop Tab - Create, preview, and export garments
No CLO connection required until export.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import sys
import threading
from PIL import Image, ImageTk

# Add parent to path
BASE_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from modules.garment_generator import (
    generate_garment, 
    list_generated_garments, 
    delete_garment,
    get_fabric_presets,
    STYLE_TEMPLATES
)
from modules.render_engine import render_preview, clear_preview_cache
from modules.project_manager import open_in_clo, get_settings, update_setting

from ui.theme import (
    Card, heading, subheading, body, StatusLabel,
    ACCENT, TEXT, TEXT_SECONDARY, CARD_BG, STATUS_OK, STATUS_ERROR
)


class WorkshopTab(ctk.CTkFrame):
    """Garment Workshop - Design and export garments"""
    
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.current_preview_path = None
        self.current_garment_meta = None
        
        # Create layout
        self.create_ui()
        
        # Load existing garments
        self.refresh_garments_list()
    
    def create_ui(self):
        """Create the workshop interface"""
        
        # Main container with scrolling
        main_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        main_scroll.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header = ctk.CTkFrame(main_scroll, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        
        title = ctk.CTkLabel(header, text="🎨 Garment Workshop", **heading())
        title.pack(side="left")
        
        subtitle = ctk.CTkLabel(
            header, 
            text="Design garments without CLO — export when ready",
            **body(TEXT_SECONDARY)
        )
        subtitle.pack(side="left", padx=(10, 0))
        
        # Two-column layout
        columns = ctk.CTkFrame(main_scroll, fg_color="transparent")
        columns.pack(fill="both", expand=True)
        
        # Left column - Create new garment
        left_col = ctk.CTkFrame(columns, fg_color="transparent")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        self.create_design_panel(left_col)
        
        # Right column - Preview and library
        right_col = ctk.CTkFrame(columns, fg_color="transparent")
        right_col.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        self.create_preview_panel(right_col)
        self.create_library_panel(right_col)
    
    def create_design_panel(self, parent):
        """Create the garment design panel"""
        
        card = Card(parent, title="Create New Garment")
        card.pack(fill="x", pady=(0, 20))
        
        # Garment name
        name_label = ctk.CTkLabel(card, text="Garment Name", **body())
        name_label.pack(anchor="w", pady=(10, 5))
        
        self.name_entry = ctk.CTkEntry(
            card, 
            placeholder_text="e.g., Summer Dress",
            height=40
        )
        self.name_entry.pack(fill="x", pady=(0, 15))
        
        # Garment type
        type_label = ctk.CTkLabel(card, text="Garment Type", **body())
        type_label.pack(anchor="w", pady=(0, 5))
        
        self.type_var = tk.StringVar(value="tshirt")
        type_options = list(STYLE_TEMPLATES.keys())
        self.type_dropdown = ctk.CTkOptionMenu(
            card,
            variable=self.type_var,
            values=type_options,
            height=40
        )
        self.type_dropdown.pack(fill="x", pady=(0, 15))
        
        # Fabric
        fabric_label = ctk.CTkLabel(card, text="Fabric", **body())
        fabric_label.pack(anchor="w", pady=(0, 5))
        
        fabrics = list(get_fabric_presets().keys())
        self.fabric_var = tk.StringVar(value="cotton")
        self.fabric_dropdown = ctk.CTkOptionMenu(
            card,
            variable=self.fabric_var,
            values=fabrics,
            height=40
        )
        self.fabric_dropdown.pack(fill="x", pady=(0, 15))
        
        # Color (optional)
        color_label = ctk.CTkLabel(card, text="Color (optional)", **body())
        color_label.pack(anchor="w", pady=(0, 5))
        
        self.color_entry = ctk.CTkEntry(
            card,
            placeholder_text="#RRGGBB or leave blank for fabric default",
            height=40
        )
        self.color_entry.pack(fill="x", pady=(0, 15))
        
        # Notes
        notes_label = ctk.CTkLabel(card, text="Notes (optional)", **body())
        notes_label.pack(anchor="w", pady=(0, 5))
        
        self.notes_entry = ctk.CTkTextbox(card, height=80)
        self.notes_entry.pack(fill="x", pady=(0, 15))
        
        # Action buttons
        button_frame = ctk.CTkFrame(card, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))
        
        self.generate_btn = ctk.CTkButton(
            button_frame,
            text="🎨 Generate Garment",
            command=self.on_generate,
            height=45,
            font=("Segoe UI", 14, "bold"),
            fg_color=ACCENT
        )
        self.generate_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.preview_btn = ctk.CTkButton(
            button_frame,
            text="👁️ Preview",
            command=self.on_preview,
            height=45,
            state="disabled"
        )
        self.preview_btn.pack(side="left", fill="x", expand=True, padx=(5, 0))
        
        # Status label
        self.status_label = StatusLabel(card)
        self.status_label.pack(fill="x", pady=(10, 0))
    
    def create_preview_panel(self, parent):
        """Create the preview panel"""
        
        card = Card(parent, title="Preview")
        card.pack(fill="both", expand=True, pady=(0, 20))
        
        # Preview image container
        self.preview_container = ctk.CTkFrame(card, fg_color="#F0F0F0", height=400)
        self.preview_container.pack(fill="both", expand=True, pady=10)
        self.preview_container.pack_propagate(False)
        
        # Placeholder label
        self.preview_label = ctk.CTkLabel(
            self.preview_container,
            text="Generate a garment to see preview",
            text_color="#999999"
        )
        self.preview_label.pack(expand=True)
        
        # Export button
        self.export_btn = ctk.CTkButton(
            card,
            text="📤 Export to CLO",
            command=self.on_export_to_clo,
            height=40,
            state="disabled"
        )
        self.export_btn.pack(fill="x", pady=(10, 0))
    
    def create_library_panel(self, parent):
        """Create the garment library panel"""
        
        card = Card(parent, title="Your Garments")
        card.pack(fill="both", expand=True)
        
        # Toolbar
        toolbar = ctk.CTkFrame(card, fg_color="transparent")
        toolbar.pack(fill="x", pady=(10, 10))
        
        refresh_btn = ctk.CTkButton(
            toolbar,
            text="🔄 Refresh",
            command=self.refresh_garments_list,
            width=100,
            height=30
        )
        refresh_btn.pack(side="left")
        
        clear_btn = ctk.CTkButton(
            toolbar,
            text="🗑️ Clear Previews",
            command=self.on_clear_previews,
            width=120,
            height=30,
            fg_color="#E74C3C"
        )
        clear_btn.pack(side="right")
        
        # Garments list
        self.garments_frame = ctk.CTkScrollableFrame(card, height=300)
        self.garments_frame.pack(fill="both", expand=True)
    
    def on_generate(self):
        """Handle generate button click"""
        
        # Validate inputs
        name = self.name_entry.get().strip()
        if not name:
            self.status_label.set_error("Please enter a garment name")
            return
        
        garment_type = self.type_var.get()
        fabric = self.fabric_var.get()
        color = self.color_entry.get().strip() or None
        notes = self.notes_entry.get("1.0", "end").strip() or None
        
        # Disable button during generation
        self.generate_btn.configure(state="disabled", text="Generating...")
        self.status_label.set_info("Generating garment...")
        
        def generate_thread():
            try:
                # Generate garment
                result = generate_garment(
                    name=name,
                    fabric=fabric,
                    style=garment_type,
                    color=color,
                    notes=notes
                )
                
                # Update UI on main thread
                self.after(0, lambda: self.on_generate_complete(result))
                
            except Exception as e:
                self.after(0, lambda: self.on_generate_error(str(e)))
        
        # Run in background thread
        threading.Thread(target=generate_thread, daemon=True).start()
    
    def on_generate_complete(self, result):
        """Handle generation completion"""
        
        self.generate_btn.configure(state="normal", text="🎨 Generate Garment")
        
        if result.get("success"):
            self.status_label.set_success(f"✓ Generated: {result['name']}")
            self.current_garment_meta = result["metadata"]
            self.preview_btn.configure(state="normal")
            
            # Auto-generate preview
            self.on_preview()
            
            # Refresh library
            self.refresh_garments_list()
            
            # Show toast
            if hasattr(self.app, 'toast'):
                self.app.toast.show(f"Garment created: {result['name']}", "success")
        else:
            error = result.get("error", "Unknown error")
            self.status_label.set_error(f"✗ Error: {error}")
            if hasattr(self.app, 'toast'):
                self.app.toast.show(f"Generation failed: {error}", "error")
    
    def on_generate_error(self, error):
        """Handle generation error"""
        
        self.generate_btn.configure(state="normal", text="🎨 Generate Garment")
        self.status_label.set_error(f"✗ Error: {error}")
        if hasattr(self.app, 'toast'):
            self.app.toast.show(f"Generation failed: {error}", "error")
    
    def on_preview(self):
        """Generate and display preview"""
        
        if not self.current_garment_meta:
            return
        
        self.preview_btn.configure(state="disabled", text="Rendering...")
        
        def preview_thread():
            try:
                # Render preview
                preview_path = render_preview(self.current_garment_meta)
                
                # Update UI on main thread
                self.after(0, lambda: self.display_preview(preview_path))
                
            except Exception as e:
                self.after(0, lambda: self.on_preview_error(str(e)))
        
        threading.Thread(target=preview_thread, daemon=True).start()
    
    def display_preview(self, preview_path):
        """Display the preview image"""
        
        self.preview_btn.configure(state="normal", text="👁️ Preview")
        self.current_preview_path = preview_path
        
        try:
            # Load and display image
            img = Image.open(preview_path)
            img.thumbnail((380, 380), Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(img)
            
            # Clear previous preview
            for widget in self.preview_container.winfo_children():
                widget.destroy()
            
            # Display new preview
            img_label = tk.Label(self.preview_container, image=photo, bg="#F0F0F0")
            img_label.image = photo  # Keep reference
            img_label.pack(expand=True)
            
            # Enable export button
            self.export_btn.configure(state="normal")
            
        except Exception as e:
            self.on_preview_error(str(e))
    
    def on_preview_error(self, error):
        """Handle preview error"""
        
        self.preview_btn.configure(state="normal", text="👁️ Preview")
        if hasattr(self.app, 'toast'):
            self.app.toast.show(f"Preview failed: {error}", "error")
    
    def on_export_to_clo(self):
        """Export garment to CLO 3D"""
        
        if not self.current_garment_meta:
            return
        
        export_path = self.current_garment_meta.get("export_path")
        if not export_path:
            messagebox.showerror("Error", "No export path found")
            return
        
        # Open in CLO
        result = open_in_clo(export_path)
        
        if result.get("success"):
            messagebox.showinfo("Success", result["message"])
            if hasattr(self.app, 'toast'):
                self.app.toast.show("Opened in CLO 3D", "success")
        else:
            error = result.get("error", "Unknown error")
            hint = result.get("hint", "")
            msg = f"{error}\n\n{hint}" if hint else error
            messagebox.showerror("Error", msg)
    
    def refresh_garments_list(self):
        """Refresh the garments library"""
        
        # Clear existing items
        for widget in self.garments_frame.winfo_children():
            widget.destroy()
        
        # Load garments
        garments = list_generated_garments()
        
        if not garments:
            no_items = ctk.CTkLabel(
                self.garments_frame,
                text="No garments yet. Create one above!",
                text_color="#999999"
            )
            no_items.pack(pady=20)
            return
        
        # Display garments
        for garment in garments:
            self.create_garment_item(garment)
    
    def create_garment_item(self, garment):
        """Create a garment list item"""
        
        item = ctk.CTkFrame(self.garments_frame, fg_color=CARD_BG, corner_radius=8)
        item.pack(fill="x", pady=5, padx=5)
        
        # Info section
        info_frame = ctk.CTkFrame(item, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        name_label = ctk.CTkLabel(
            info_frame,
            text=garment["name"],
            font=("Segoe UI", 14, "bold"),
            anchor="w"
        )
        name_label.pack(anchor="w")
        
        details = f"{garment['fabric'].title()} • {garment['style'].title()}"
        details_label = ctk.CTkLabel(
            info_frame,
            text=details,
            text_color=TEXT_SECONDARY,
            font=("Segoe UI", 11),
            anchor="w"
        )
        details_label.pack(anchor="w")
        
        # Buttons
        btn_frame = ctk.CTkFrame(item, fg_color="transparent")
        btn_frame.pack(side="right", padx=10)
        
        open_btn = ctk.CTkButton(
            btn_frame,
            text="Open",
            command=lambda g=garment: self.on_open_garment(g),
            width=80,
            height=30
        )
        open_btn.pack(side="left", padx=2)
        
        delete_btn = ctk.CTkButton(
            btn_frame,
            text="Delete",
            command=lambda g=garment: self.on_delete_garment(g),
            width=80,
            height=30,
            fg_color="#E74C3C"
        )
        delete_btn.pack(side="left", padx=2)
    
    def on_open_garment(self, garment):
        """Open a garment in CLO"""
        
        result = open_in_clo(garment["export_path"])
        
        if result.get("success"):
            if hasattr(self.app, 'toast'):
                self.app.toast.show(f"Opened {garment['name']} in CLO", "success")
        else:
            messagebox.showerror("Error", result.get("error", "Failed to open"))
    
    def on_delete_garment(self, garment):
        """Delete a garment"""
        
        if not messagebox.askyesno("Confirm Delete", f"Delete {garment['name']}?"):
            return
        
        result = delete_garment(garment["garment_id"])
        
        if result.get("success"):
            self.refresh_garments_list()
            if hasattr(self.app, 'toast'):
                self.app.toast.show(f"Deleted {garment['name']}", "success")
        else:
            messagebox.showerror("Error", result.get("error", "Failed to delete"))
    
    def on_clear_previews(self):
        """Clear all cached previews"""
        
        if not messagebox.askyesno("Confirm", "Clear all preview images?"):
            return
        
        try:
            clear_preview_cache()
            if hasattr(self.app, 'toast'):
                self.app.toast.show("Preview cache cleared", "success")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear cache: {e}")

