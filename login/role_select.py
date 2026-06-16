"""Màn hình chọn vai trò Admin / User"""

import tkinter as tk
from login.theme import THEME, BG, CARD_BG, TEXT, SUBTEXT, HINT, SEP_CLR


class RoleSelectWindow:
    def __init__(self, on_role_selected):
        self.on_role_selected = on_role_selected
        self._build()

    def _build(self):
        self.root = tk.Tk()
        self.root.title("Berlin Rail – Chọn vai trò")
        self.root.geometry("400x380")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)
        self._center(self.root)

        hdr = tk.Frame(self.root, bg="#0F172A", height=80)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🚆  Berlin Rail Pathfinder",
                 font=("Arial", 16, "bold"),
                 bg="#0F172A", fg="white").pack(pady=(18, 4))
        tk.Label(hdr, text="Chọn vai trò để tiếp tục",
                 font=("Arial", 9),
                 bg="#0F172A", fg=HINT).pack()

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=28, pady=22)

        tk.Label(body, text="Bạn đăng nhập với tư cách:",
                 font=("Arial", 11, "bold"),
                 bg=BG, fg=TEXT).pack(pady=(0, 14))

        self._role_card(body, "admin",
                        icon="🔐",
                        label="Quản trị viên (Admin)",
                        desc="Tìm đường + cấu hình vùng cấm")
        tk.Frame(body, height=10, bg=BG).pack()
        self._role_card(body, "user",
                        icon="🚇",
                        label="Người dùng (User)",
                        desc="Tìm đường, xem bản đồ tuyến rail")

    def _role_card(self, parent, role, icon, label, desc):
        t = THEME[role]

        card = tk.Frame(parent, bg=CARD_BG,
                        highlightthickness=1,
                        highlightbackground=SEP_CLR)
        card.pack(fill="x")

        inner = tk.Frame(card, bg=CARD_BG)
        inner.pack(fill="x", padx=14, pady=10)

        tk.Label(inner, text=icon, font=("Arial", 20),
                 bg=CARD_BG).pack(side="left", padx=(0, 12))

        info = tk.Frame(inner, bg=CARD_BG)
        info.pack(side="left", fill="x", expand=True)
        tk.Label(info, text=label, font=("Arial", 11, "bold"),
                 bg=CARD_BG, fg=TEXT, anchor="w").pack(fill="x")
        tk.Label(info, text=desc, font=("Arial", 9),
                 bg=CARD_BG, fg=SUBTEXT, anchor="w").pack(fill="x")

        btn = tk.Button(inner, text="Chọn →",
                        font=("Arial", 9, "bold"),
                        bg=t["btn"], fg="white",
                        bd=0, cursor="hand2",
                        padx=10, pady=5,
                        command=lambda r=role: self._select(r))
        btn.pack(side="right")
        btn.bind("<Enter>", lambda e, b=btn, c=t["btn_hover"]: b.config(bg=c))
        btn.bind("<Leave>", lambda e, b=btn, c=t["btn"]:       b.config(bg=c))

        for w in [card, inner, info]:
            w.bind("<Enter>", lambda e, c=card: c.config(bg="#F8FAFC"))
            w.bind("<Leave>", lambda e, c=card: c.config(bg=CARD_BG))

    def _select(self, role):
        self.root.destroy()
        self.on_role_selected(role)

    @staticmethod
    def _center(win):
        win.update_idletasks()
        w, h = win.winfo_width(), win.winfo_height()
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def run(self):
        self.root.mainloop()
