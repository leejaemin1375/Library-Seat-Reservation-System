import tkinter as tk
from tkinter import messagebox
import json
import os

DATA_FILE = "users.json"

def load_users():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_users(users):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=4)
    except IOError:
        messagebox.showerror("파일 오류", "사용자 정보를 저장하는 중 오류가 발생했습니다.")

class LoginPage(tk.Frame):
    def __init__(self, master, on_login_success):
        super().__init__(master)
        self.on_login_success = on_login_success
        self.create_widgets()

    def create_widgets(self):
        title_label = tk.Label(self, text="로그인 시스템", font=("Arial", 14, "bold"))
        title_label.pack(pady=15)

        username_frame = tk.Frame(self)
        username_frame.pack(pady=5)
        tk.Label(username_frame, text="아이디: ", width=10, anchor="w").pack(side="left")
        self.username_entry = tk.Entry(username_frame)
        self.username_entry.pack(side="left")

        password_frame = tk.Frame(self)
        password_frame.pack(pady=5)
        tk.Label(password_frame, text="비밀번호: ", width=10, anchor="w").pack(side="left")
        self.password_entry = tk.Entry(password_frame, show="*")
        self.password_entry.pack(side="left")

        button_frame = tk.Frame(self)
        button_frame.pack(pady=20)

        tk.Button(button_frame, text="로그인", command=self.login, width=10, bg="#4CAF50", fg="white").pack(side="left", padx=10)
        tk.Button(button_frame, text="회원가입", command=self.open_signup_window, width=10, bg="#2196F3", fg="white").pack(side="left", padx=10)

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showwarning("입력 오류", "아이디와 비밀번호를 모두 입력해주세요.")
            return
            
        users = load_users()
        
        if username in users and users[username] == password:
            messagebox.showinfo("로그인 성공", f"환영합니다, {username}님!")
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)
            self.on_login_success(username)
        else:
            messagebox.showerror("로그인 실패", "아이디 또는 비밀번호가 잘못되었습니다.")

    def open_signup_window(self):
        def register_user():
            new_username = signup_username_entry.get().strip()
            new_password = signup_password_entry.get().strip()
            
            if not new_username or not new_password:
                messagebox.showwarning("입력 오류", "회원가입할 아이디와 비밀번호를 입력해주세요.", parent=signup_window)
                return
                
            users = load_users()
            
            if new_username in users:
                messagebox.showerror("가입 실패", "이미 존재하는 아이디입니다.", parent=signup_window)
            else:
                users[new_username] = new_password
                save_users(users)
                messagebox.showinfo("가입 성공", f"'{new_username}'님, 회원가입이 완료되었습니다!", parent=signup_window)
                signup_window.destroy()

        signup_window = tk.Toplevel(self)
        signup_window.title("회원가입")
        signup_window.geometry("320x220")
        signup_window.resizable(False, False)
        signup_window.grab_set()

        tk.Label(signup_window, text="새로운 계정 만들기", font=("Arial", 12, "bold")).pack(pady=15)

        su_username_frame = tk.Frame(signup_window)
        su_username_frame.pack(pady=5)
        tk.Label(su_username_frame, text="새 아이디: ", width=10, anchor="w").pack(side="left")
        signup_username_entry = tk.Entry(su_username_frame)
        signup_username_entry.pack(side="left")

        su_password_frame = tk.Frame(signup_window)
        su_password_frame.pack(pady=5)
        tk.Label(su_password_frame, text="비밀번호: ", width=10, anchor="w").pack(side="left")
        signup_password_entry = tk.Entry(su_password_frame, show="*")
        signup_password_entry.pack(side="left")

        su_button_frame = tk.Frame(signup_window)
        su_button_frame.pack(pady=15)
        tk.Button(su_button_frame, text="가입 완료", command=register_user, width=12, bg="#2196F3", fg="white").pack()