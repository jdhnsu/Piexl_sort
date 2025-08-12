# test_tk.py
import tkinter as tk
root = tk.Tk()
root.title("TK Test")
tk.Label(root, text="如果你能看到这个窗口，说明图形环境可用").pack(padx=20, pady=20)
root.mainloop()
