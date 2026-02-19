import ttkbootstrap as tb
from gui import BallisticApp

def main():
    root = tb.Window(themename="flatly")
    BallisticApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
