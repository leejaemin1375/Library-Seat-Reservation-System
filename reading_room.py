import tkinter as tk
import tkinter.messagebox as msgbox
import json
import os
import threading
from datetime import datetime, timedelta

ROOMS_FILE = "reading_rooms.json"
_lock = threading.RLock()

ROOMS = [
    {"name": "열람실1", "total": 20},
    {"name": "열람실2", "total": 30},
    {"name": "열람실3", "total": 40},
]

STATUS_COLORS = {
    0: {"bg": "#4CAF50", "fg": "white"},
    1: {"bg": "#9C27B0", "fg": "white"},
    2: {"bg": "#F44336", "fg": "white"},
}

def load_rooms():
    with _lock:
        if os.path.exists(ROOMS_FILE):
            with open(ROOMS_FILE, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    pass
        default = {r["name"]: {"total": r["total"], "reservations": {}} for r in ROOMS}
        save_rooms(default)
        return default

def save_rooms(data):
    with _lock:
        try:
            with open(ROOMS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except IOError:
            msgbox.showerror("파일 오류", "열람실 데이터를 저장하는 중 에러가 발생했습니다.")

def get_seat_status(reservations, seat_num):
    seat_key = str(seat_num)
    if seat_key not in reservations:
        return 0
    try:
        end_dt = datetime.strptime(reservations[seat_key]["end_time"], "%Y-%m-%d %H:%M")
        return 1 if datetime.now() < end_dt else 0
    except (ValueError, KeyError):
        return 0

class ReadingRoomPage(tk.Frame):
    def __init__(self, master, user, on_back):
        super().__init__(master)
        self.user = user
        self.on_back = on_back
        self.selected_room = None
        self.selected_seat = None
        self.show_room_list()

    def _clear(self):
        for widget in self.winfo_children():
            widget.destroy()

    def show_room_list(self):
        self._clear()
        rooms_data = load_rooms()

        top_frame = tk.Frame(self)
        top_frame.pack(fill="x", padx=15, pady=10)
        tk.Label(top_frame, text="열람실 좌석 선택", font=("맑은 고딕", 14, "bold")).pack(side="left", pady=15)

        for room in ROOMS:
            reservations = rooms_data.get(room["name"], {}).get("reservations", {})
            used = sum(1 for s in reservations.values() if datetime.now() < datetime.strptime(s["end_time"], "%Y-%m-%d %H:%M"))
            self._make_room_card(room, used)

        # 요구사항 4: 모든 서브 메인 하단에 뒤로가기 버튼 명시
        tk.Button(self, text="메인 마이페이지로 이동", font=("맑은 고딕", 10), width=22, 
                  command=lambda: self.on_back(self.user)).pack(pady=20)

    def _make_room_card(self, room, used):
        card = tk.Frame(self, relief="solid", bd=1, padx=10, pady=8)
        card.pack(fill="x", padx=20, pady=4)
        tk.Label(card, text=room["name"], font=("맑은 고딕", 11, "bold"), anchor="w").pack(fill="x")
        
        count_frame = tk.Frame(card)
        count_frame.pack(fill="x")
        tk.Label(count_frame, text=f"{used} / {room['total']} 사용 중", font=("맑은 고딕", 9), fg="#555").pack(side="left")

        for widget in [card] + card.winfo_children():
            widget.bind("<Button-1>", lambda e, r=room: self.show_seat_map(r))

    def show_seat_map(self, room):
        self._clear()
        self.selected_room = room
        rooms_data = load_rooms()
        reservations = rooms_data.get(room["name"], {}).get("reservations", {})

        tk.Label(self, text=room["name"], font=("맑은 고딕", 13, "bold")).pack(pady=10)

        container = tk.Frame(self)
        container.pack(fill="both", expand=True, padx=10)

        canvas = tk.Canvas(container)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        seat_frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=seat_frame, anchor="nw")

        cols = 5
        for i in range(1, room["total"] + 1):
            status = get_seat_status(reservations, i)
            row, col = divmod(i - 1, cols)
            color = STATUS_COLORS[status]
            seat_key = str(i)
            tooltip = reservations[seat_key]["end_time"].split()[-1] if status == 1 else str(i)

            tk.Button(seat_frame, text=tooltip, width=5, height=1, bg=color["bg"], fg=color["fg"],
                      font=("Arial", 9, "bold"), relief="flat",
                      command=lambda s=i, st=status: self.select_seat(s, st)).grid(row=row, column=col, padx=4, pady=4)

        seat_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

        # 요구사항 4: 좌석 선택 맵 하단에 뒤로가기 배치
        tk.Button(self, text="이전 (열람실 목록)", font=("맑은 고딕", 10), command=self.show_room_list).pack(pady=10)

    def select_seat(self, seat_num, status):
        if status != 0:
            msgbox.showwarning("선택 불가", "이미 예약된 좌석입니다.")
            return
        if msgbox.askyesno("예약 확인", f"{self.selected_room['name']} {seat_num}번 좌석을 예약하시겠습니까?"):
            self.reserve(seat_num)

    def reserve(self, seat_num):
        rooms_data = load_rooms()
        room_name = self.selected_room["name"]
        seat_key = str(seat_num)

        for r_n, r_i in rooms_data.items():
            for s_k, s_i in r_i["reservations"].items():
                if s_i.get("user") == self.user:
                    msgbox.showwarning("예약 불가", "이미 이용 중인 열람실 좌석이 존재합니다.")
                    return

        end_dt = datetime.now() + timedelta(hours=3)
        rooms_data[room_name]["reservations"][seat_key] = {"user": self.user, "end_time": end_dt.strftime("%Y-%m-%d %H:%M")}
        save_rooms(rooms_data)

        msgbox.showinfo("예약 완료", f"성공적으로 예약되었습니다.\n종료 시간: {end_dt.strftime('%H:%M')}")
        self.show_room_list()