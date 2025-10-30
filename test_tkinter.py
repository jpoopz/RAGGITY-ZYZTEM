"""
Test Tkinter with correct Tcl/Tk paths
"""
import os
import sys

# Set paths explicitly
tcl_path = r"C:\Users\Julian Poopat\AppData\Local\Programs\Python\Python314\tcl\tcl8.6"
tk_path = r"C:\Users\Julian Poopat\AppData\Local\Programs\Python\Python314\tcl\tk8.6"

os.environ["TCL_LIBRARY"] = tcl_path
os.environ["TK_LIBRARY"] = tk_path

print(f"TCL_LIBRARY = {os.environ['TCL_LIBRARY']}")
print(f"TK_LIBRARY = {os.environ['TK_LIBRARY']}")

try:
    import tkinter
    print("\n✓ Tkinter imported successfully")
    
    root = tkinter.Tk()
    root.withdraw()  # Hide window
    print("✓ Tk window created")
    root.destroy()
    print("\n✓✓✓ Tkinter test PASSED ✓✓✓")
    sys.exit(0)
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)




