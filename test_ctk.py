import customtkinter as ctk

print("Testing CustomTkinter...")
print(f"Version: {ctk.__version__}")

try:
    app = ctk.CTk()
    app.geometry("500x400")
    app.title("Test")
    print("✓ Basic window created successfully")
    
    frame = ctk.CTkFrame(app)
    frame.pack(fill="both", expand=True)
    print("✓ Frame created successfully")
    
    label = ctk.CTkLabel(frame, text="Test Label")
    label.pack()
    print("✓ Label created successfully")
    
    print("\n✅ All widgets created without errors!")
    print("Closing test window...")
    app.destroy()
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
