import sys, os
import traceback
from ui import create_main_window

def log_uncaught_exceptions(ex_cls, ex, tb):
    with open("error.log", "w", encoding="utf-8") as f:
        traceback.print_exception(ex_cls, ex, tb, file=f)

sys.excepthook = log_uncaught_exceptions

# --- helper for bundled resources (icon path etc.) ---
def resource_path(*parts):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)

if __name__ == "__main__":
    root = create_main_window()  # make sure your ui.py returns root

    # --- set window/taskbar icon ---
    try:
        icon_path = resource_path("icons", "app.ico")
        root.iconbitmap(icon_path)
    except Exception as e:
        # silently ignore if icon fails (e.g. Linux/other OS)
        print("Icon load failed:", e)

    root.mainloop()
