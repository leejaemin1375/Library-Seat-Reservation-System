import tkinter as tk
from tkinter import messagebox
import json
import os

# 회원 정보가 저장될 파일 이름
DATA_FILE = "users.json"

# 파일에서 기존 사용자 정보를 불러오는 함수
def load_users():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {} # 파일이 비어있거나 깨진 경우 빈 딕셔너리 반환
    return {}

# 파일에 사용자 정보를 저장하는 함수
def save_users(users):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

# [로그인 기능]
def login():
    username = username_entry.get().strip()
    password = password_entry.get().strip()
    
    if not username or not password:
        messagebox.showwarning("입력 오류", "아이디와 비밀번호를 모두 입력해주세요.")
        return
        
    users = load_users()
    
    # 아이디 존재 여부 및 비밀번호 일치 확인
    if username in users and users[username] == password:
        messagebox.showinfo("로그인 성공", f"환영합니다, {username}님!")
        # 로그인 성공 후 입력창 비우기
        username_entry.delete(0, tk.END)
        password_entry.delete(0, tk.END)
    else:
        messagebox.showerror("로그인 실패", "아이디 또는 비밀번호가 잘못되었습니다.")


# [회원가입 창 띄우기 및 가입 기능]
def open_signup_window():
    # 실제 가입 처리를 하는 내부 함수
    def register_user():
        new_username = signup_username_entry.get().strip()
        new_password = signup_password_entry.get().strip()
        
        if not new_username or not new_password:
            messagebox.showwarning("입력 오류", "회원가입할 아이디와 비밀번호를 입력해주세요.", parent=signup_window)
            return
            
        users = load_users()
        
        # 중복 아이디 체크
        if new_username in users:
            messagebox.showerror("가입 실패", "이미 존재하는 아이디입니다.", parent=signup_window)
        else:
            users[new_username] = new_password # 정보 추가
            save_users(users)                  # 파일에 저장
            messagebox.showinfo("가입 성공", f"'{new_username}'님, 회원가입이 완료되었습니다!\n이제 로그인할 수 있습니다.", parent=signup_window)
            signup_window.destroy()  # 가입 성공 시 회원가입 창 닫기

    # --- 새 창(Toplevel) 생성 ---
    signup_window = tk.Toplevel(root)
    signup_window.title("회원가입")
    signup_window.geometry("320x220")
    signup_window.resizable(False, False)
    
    # 메인 창 위에 고정 (가입 창을 닫기 전까지 메인 창 클릭 불가하게 만듦)
    signup_window.grab_set()

    # 상단 안내 레이블
    su_title_label = tk.Label(signup_window, text="새로운 계정 만들기", font=("Arial", 12, "bold"))
    su_title_label.pack(pady=15)

    # 아이디 입력 구역
    su_username_frame = tk.Frame(signup_window)
    su_username_frame.pack(pady=5)
    
    su_username_label = tk.Label(su_username_frame, text="새 아이디: ", width=10, anchor="w")
    su_username_label.pack(side="left")
    
    signup_username_entry = tk.Entry(su_username_frame)
    signup_username_entry.pack(side="left")

    # 비밀번호 입력 구역
    su_password_frame = tk.Frame(signup_window)
    su_password_frame.pack(pady=5)
    
    su_password_label = tk.Label(su_password_frame, text="비밀번호: ", width=10, anchor="w")
    su_password_label.pack(side="left")
    
    signup_password_entry = tk.Entry(su_password_frame, show="*")
    signup_password_entry.pack(side="left")

    # 가입 완료 버튼 구역
    su_button_frame = tk.Frame(signup_window)
    su_button_frame.pack(pady=15)
    
    submit_button = tk.Button(su_button_frame, text="가입 완료", command=register_user, width=12, bg="#2196F3", fg="white")
    submit_button.pack()


# ==================== 메인 로그인 윈도우 창 설정 ====================
root = tk.Tk()
root.title("회원 관리 시스템")
root.geometry("320x240")
root.resizable(False, False)

# 상단 안내 레이블
title_label = tk.Label(root, text="로그인 시스템", font=("Arial", 14, "bold"))
title_label.pack(pady=15)

# --- 아이디 입력 구역 ---
username_frame = tk.Frame(root)
username_frame.pack(pady=5)

username_label = tk.Label(username_frame, text="아이디: ", width=10, anchor="w")
username_label.pack(side="left")

username_entry = tk.Entry(username_frame)
username_entry.pack(side="left")

# --- 비밀번호 입력 구역 ---
password_frame = tk.Frame(root)
password_frame.pack(pady=5)

password_label = tk.Label(password_frame, text="비밀번호: ", width=10, anchor="w")
password_label.pack(side="left")

password_entry = tk.Entry(password_frame, show="*")
password_entry.pack(side="left")

# --- 버튼 구역 ---
button_frame = tk.Frame(root)
button_frame.pack(pady=20)

# 로그인 버튼
login_button = tk.Button(button_frame, text="로그인", command=login, width=10, bg="#4CAF50", fg="white")
login_button.pack(side="left", padx=10)

# 회원가입 버튼 (누르면 open_signup_window 함수 실행)
signup_button = tk.Button(button_frame, text="회원가입", command=open_signup_window, width=10, bg="#2196F3", fg="white")
signup_button.pack(side="left", padx=10)

# 이벤트 루프 시작
root.mainloop()