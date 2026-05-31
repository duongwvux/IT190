"""Màn hình đăng nhập / đăng ký"""

import tkinter as tk
from auth import login, register
from login.theme import THEME, BG, CARD_BG, TEXT, SUBTEXT, HINT, INPUT_BG, INPUT_BD, SEP_CLR, ERR_FG, OK_FG
from login.role_select import RoleSelectWindow


def make_icon_entry(parent, icon_text, show=None):
    """Trả về (frame_outer, entry_widget). Layout: [icon | sep | input]"""
    outer = tk.Frame(parent, bg=INPUT_BD, padx=1, pady=1)
    inner = tk.Frame(outer, bg=INPUT_BG)
    inner.pack(fill="x")

    tk.Label(inner, text=icon_text, width=3,
             font=("Arial", 12),
             bg=INPUT_BG, fg=SUBTEXT).pack(side="left")

    tk.Frame(inner, width=1, bg=INPUT_BD).pack(side="left", fill="y", pady=4)

    e = tk.Entry(inner, bg=INPUT_BG, fg=TEXT,
                 relief="flat", font=("Arial", 11),
                 show=show or "",
                 insertbackground=TEXT)
    e.pack(side="left", fill="x", expand=True, padx=8, pady=6)

    return outer, e


class LoginWindow:
    def __init__(self, on_login_success):
        self.on_login_success = on_login_success
        RoleSelectWindow(self._open_login).run()

    def _open_login(self, selected_role):
        self.selected_role = selected_role
        self.t = THEME[selected_role]
        self._build()
        self.root.mainloop()

    def _build(self):
        self.root = tk.Tk()
        lbl = "Admin" if self.selected_role == "admin" else "User"
        self.root.title(f"Berlin Rail – Đăng nhập ({lbl})")
        self.root.geometry("400x520")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)
        self._center(self.root)
        self._build_header()
        self._build_card()

    def _build_header(self):
        t = self.t
        hdr = tk.Frame(self.root, bg=t["header_bg"])
        hdr.pack(fill="x")

        badge_row = tk.Frame(hdr, bg=t["header_bg"])
        badge_row.pack(anchor="w", padx=20, pady=(16, 0))
        tk.Label(badge_row,
                 text=f"  {t['badge_lbl']}  ",
                 font=("Arial", 8, "bold"),
                 bg=t["badge_bg"], fg="white",
                 padx=6, pady=2).pack(side="left")

        tk.Label(hdr,
                 text=f"{t['icon']}  {t['title']}",
                 font=("Arial", 15, "bold"),
                 bg=t["header_bg"], fg="white").pack(anchor="w", padx=20, pady=(6, 2))
        tk.Label(hdr, text=t["subtitle"],
                 font=("Arial", 9),
                 bg=t["header_bg"], fg=HINT).pack(anchor="w", padx=20, pady=(0, 16))

    def _build_card(self):
        t = self.t
        card = tk.Frame(self.root, bg=CARD_BG,
                        highlightthickness=1,
                        highlightbackground=SEP_CLR)
        card.pack(padx=20, pady=16, fill="both", expand=True)

        tab_row = tk.Frame(card, bg=SEP_CLR)
        tab_row.pack(fill="x")

        self.tab_login_btn = tk.Button(
            tab_row, text="Đăng nhập",
            font=("Arial", 10, "bold"), bd=0, cursor="hand2",
            command=lambda: self._switch("login"))
        self.tab_login_btn.pack(side="left", fill="x", expand=True, ipady=9)

        self.tab_reg_btn = None
        if self.selected_role != "admin":
            self.tab_reg_btn = tk.Button(
                tab_row, text="Đăng ký",
                font=("Arial", 10, "bold"), bd=0, cursor="hand2",
                command=lambda: self._switch("register"))
            self.tab_reg_btn.pack(side="left", fill="x", expand=True, ipady=9)

        tk.Frame(card, height=2, bg=t["tab_active"]).pack(fill="x")

        self.content = tk.Frame(card, bg=CARD_BG)
        self.content.pack(padx=20, pady=16, fill="both", expand=True)

        self._build_login_form()
        if self.selected_role != "admin":
            self._build_register_form()
        self._switch("login")

    def _build_login_form(self):
        f = tk.Frame(self.content, bg=CARD_BG)
        self.frm_login = f

        self._lbl(f, "Tên đăng nhập")
        frm_u, self.inp_lu = make_icon_entry(f, "👤")
        frm_u.pack(fill="x", pady=(3, 10))

        self._lbl(f, "Mật khẩu")
        frm_p, self.inp_lp = make_icon_entry(f, "🔒", show="●")
        frm_p.pack(fill="x", pady=(3, 0))

        self.lbl_lerr = tk.Label(f, text="", fg=ERR_FG,
                                 bg=CARD_BG, font=("Arial", 9), anchor="w")
        self.lbl_lerr.pack(fill="x", pady=(6, 0))

        btn = tk.Button(f, text="Đăng nhập  →",
                        font=("Arial", 11, "bold"),
                        bg=self.t["btn"], fg="white",
                        bd=0, cursor="hand2", pady=9,
                        command=self._do_login)
        btn.pack(fill="x", pady=(10, 0))
        btn.bind("<Enter>", lambda e: btn.config(bg=self.t["btn_hover"]))
        btn.bind("<Leave>", lambda e: btn.config(bg=self.t["btn"]))
        self._back_btn(f)

    def _build_register_form(self):
        f = tk.Frame(self.content, bg=CARD_BG)
        self.frm_reg = f

        self._lbl(f, "Tên đăng nhập")
        frm_u, self.inp_ru = make_icon_entry(f, "👤")
        frm_u.pack(fill="x", pady=(3, 10))

        self._lbl(f, "Mật khẩu")
        frm_p, self.inp_rp = make_icon_entry(f, "🔒", show="●")
        frm_p.pack(fill="x", pady=(3, 10))

        self._lbl(f, "Xác nhận mật khẩu")
        frm_p2, self.inp_rp2 = make_icon_entry(f, "🔒", show="●")
        frm_p2.pack(fill="x", pady=(3, 0))

        self.lbl_rerr = tk.Label(f, text="", fg=ERR_FG,
                                 bg=CARD_BG, font=("Arial", 9), anchor="w")
        self.lbl_rerr.pack(fill="x", pady=(6, 0))
        self.lbl_rok = tk.Label(f, text="", fg=OK_FG,
                                bg=CARD_BG, font=("Arial", 9), anchor="w")
        self.lbl_rok.pack(fill="x")

        btn = tk.Button(f, text="Đăng ký  →",
                        font=("Arial", 11, "bold"),
                        bg=self.t["btn"], fg="white",
                        bd=0, cursor="hand2", pady=9,
                        command=self._do_register)
        btn.pack(fill="x", pady=(10, 0))
        btn.bind("<Enter>", lambda e: btn.config(bg=self.t["btn_hover"]))
        btn.bind("<Leave>", lambda e: btn.config(bg=self.t["btn"]))
        self._back_btn(f)

    def _switch(self, tab):
        t = self.t
        for w in self.content.winfo_children():
            w.pack_forget()
        if tab == "login" or self.selected_role == "admin":
            self.frm_login.pack(fill="both", expand=True)
            self.tab_login_btn.config(bg=CARD_BG, fg=t["tab_active"])
            if self.tab_reg_btn:
                self.tab_reg_btn.config(bg=SEP_CLR, fg=SUBTEXT)
        else:
            self.frm_reg.pack(fill="both", expand=True)
            self.tab_reg_btn.config(bg=CARD_BG, fg=t["tab_active"])
            self.tab_login_btn.config(bg=SEP_CLR, fg=SUBTEXT)

    def _do_login(self):
        u = self.inp_lu.get().strip()
        p = self.inp_lp.get()
        ok, role = login(u, p)
        if not ok:
            self.lbl_lerr.config(text="❌ Sai tài khoản hoặc mật khẩu")
            return
        if role != self.selected_role:
            self.lbl_lerr.config(
                text=f"⛔ Tài khoản này là [{role.upper()}],\n"
                     f"    không phải [{self.selected_role.upper()}].")
            return
        self.root.destroy()
        self.on_login_success(role)

    def _do_register(self):
        u  = self.inp_ru.get().strip()
        p1 = self.inp_rp.get()
        p2 = self.inp_rp2.get()
        self.lbl_rerr.config(text="")
        self.lbl_rok.config(text="")
        if not u:
            self.lbl_rerr.config(text="❌ Vui lòng nhập tên đăng nhập"); return
        if p1 != p2:
            self.lbl_rerr.config(text="❌ Mật khẩu xác nhận không khớp"); return
        if len(p1) < 3:
            self.lbl_rerr.config(text="❌ Mật khẩu tối thiểu 3 ký tự"); return
        ok, msg = register(u, p1, role=self.selected_role)
        if ok:
            self.lbl_rok.config(text=f"✅ {msg} – Hãy đăng nhập!")
        else:
            self.lbl_rerr.config(text=f"❌ {msg}")

    def _back_to_role(self):
        self.root.destroy()
        RoleSelectWindow(self._open_login).run()

    def _back_btn(self, parent):
        tk.Button(parent, text="← Chọn vai trò khác",
                  font=("Arial", 9), bd=0,
                  bg=CARD_BG, fg=HINT, cursor="hand2",
                  command=self._back_to_role).pack(pady=(12, 0))

    @staticmethod
    def _lbl(parent, text):
        tk.Label(parent, text=text,
                 font=("Arial", 10, "bold"),
                 bg=CARD_BG, fg=SUBTEXT, anchor="w").pack(fill="x")

    @staticmethod
    def _center(win):
        win.update_idletasks()
        w, h = win.winfo_width(), win.winfo_height()
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def run(self):
        pass  # mainloop chạy bên trong _open_login
