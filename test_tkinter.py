import tkinter as tk

print("Attempting to create Tkinter root window...")
root = tk.Tk()
print("Tkinter root window created.")

root.title("Test Window")
root.geometry("200x100")

label = tk.Label(root, text="Hello Tkinter!")
label.pack(pady=20)

print("Starting Tkinter mainloop...")
root.mainloop()
print("Exited Tkinter mainloop.") 