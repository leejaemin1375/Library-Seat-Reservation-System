# reading_room.py 전체 수정본 (주요 변경 부위 주석 표시)
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
    0: {"bg": "#4CAF50", "fg": "white"},  # 배정가능
    1: {"bg": "#9C27B0", "fg": "white"},  # 사용중
    2: {"bg": "#F44336", "fg": "white"},  # 배정불가
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
    # [수정] target_room 매개변수 추가 (마이페이지에서 이동 버튼으로 직행할 때 사용)
    def __init__(self, master, user, on_back, target_room=None):
        super().__init__(master)
        self.user = user
        self.on_back = on_back
        self.selected_room = None
        self.selected_seat = None
        
        if hasattr(self.master, "resizable"):
            self.master.resizable(False, False)
            
        # 바로 이동으로 들어왔다면 해당 열람실 도면을 띄우고, 아니면 목록을 띄움
        if target_room:
            room_obj = next((r for r in ROOMS if r["name"] == target_room), None)
            if room_obj:
                self.show_seat_map(room_obj)
            else:
                self.show_room_list()
        else:
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

        tk.Label(self, text=f"🏛️ {room['name']} 실시간 도면 배치도", font=("맑은 고딕", 13, "bold")).pack(pady=10)

        container = tk.Frame(self)
        container.pack(fill="both", expand=True, padx=15)

        canvas = tk.Canvas(container, bg="#F5F5F5", highlightthickness=1, highlightbackground="#ccc")
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        if room["name"] == "열람실1":
            canvas.create_rectangle(25, 25, 435, 540, fill="white", outline="#333", width=2)
            canvas.create_rectangle(30, 30, 110, 460, fill="#fcfcfc", outline="#aaa")
            canvas.create_rectangle(350, 30, 430, 460, fill="#fcfcfc", outline="#aaa")
            canvas.create_rectangle(160, 80, 300, 380, fill="#EFEBE9", outline="#5D4037", width=2)
            canvas.create_text(230, 230, text="중앙 오픈형\n공유 대형 테이블", font=("맑은 고딕", 9, "bold"), fill="#5D4037", justify="center")

            canvas.create_rectangle(190, 535, 270, 545, fill="#F5F5F5", outline="#F5F5F5")
            canvas.create_line(190, 540, 225, 515, fill="#2196F3", width=3)
            canvas.create_text(230, 525, text="▲ ENTRANCE (출입구)", font=("맑은 고딕", 9, "bold"), fill="#2196F3")

            for i in range(1, room["total"] + 1):
                status = get_seat_status(reservations, i)
                color = STATUS_COLORS[status]
                tooltip = reservations[str(i)]["end_time"].split()[-1] if status == 1 else str(i)

                btn = tk.Button(canvas, text=tooltip, width=4, height=1, bg=color["bg"], fg=color["fg"],
                                font=("Arial", 9, "bold"), relief="flat",
                                command=lambda s=i, st=status: self.select_seat(s, st))

                if i <= 6:
                    canvas.create_window(70, i * 65 + 10, window=btn)
                elif i <= 12:
                    canvas.create_window(390, (i - 6) * 65 + 10, window=btn)
                else:
                    idx = i - 13
                    r, c = divmod(idx, 2)
                    pos_x = 190 if c == 0 else 270
                    pos_y = r * 70 + 120
                    canvas.create_window(pos_x, pos_y, window=btn)

        elif room["name"] == "열람실2":
            canvas.create_rectangle(25, 25, 435, 580, fill="white", outline="#333", width=2)
            canvas.create_rectangle(170, 230, 290, 290, fill="#ECEFF1", outline="#455A64", width=2)

            table_y_centers = [90, 190, 330, 430, 530]
            for ty in table_y_centers:
                canvas.create_rectangle(65, ty - 25, 395, ty + 25, fill="#F5F5F5", outline="#9E9E9E")
                canvas.create_line(65, ty, 395, ty, fill="#e0e0e0")

            canvas.create_rectangle(340, 575, 410, 585, fill="#F5F5F5", outline="#F5F5F5")
            canvas.create_line(340, 580, 375, 560, fill="#2196F3", width=3)
            canvas.create_text(375, 565, text="🚪 출입구 ⬇", font=("맑은 고딕", 9, "bold"), fill="#2196F3")

            for i in range(1, room["total"] + 1):
                status = get_seat_status(reservations, i)
                color = STATUS_COLORS[status]
                tooltip = reservations[str(i)]["end_time"].split()[-1] if status == 1 else str(i)

                btn = tk.Button(canvas, text=tooltip, width=4, height=1, bg=color["bg"], fg=color["fg"],
                                font=("Arial", 9, "bold"), relief="flat",
                                command=lambda s=i, st=status: self.select_seat(s, st))

                table_idx, seat_idx = divmod(i - 1, 6)
                r_in_t, c_in_t = divmod(seat_idx, 3)
                
                pos_x = c_in_t * 110 + 110
                pos_y = table_y_centers[table_idx] - 15 if r_in_t == 0 else table_y_centers[table_idx] + 15
                canvas.create_window(pos_x, pos_y, window=btn)

        else:
            canvas.create_rectangle(25, 25, 435, 600, fill="white", outline="#333", width=2)
            canvas.create_rectangle(32, 32, 428, 65, fill="#E3F2FD", outline="#1E88E5", width=1)
            canvas.create_text(230, 20, text="WINDOW LAPTOP ZONE (창가 노트북석)", font=("맑은 고딕", 8, "bold"), fill="#1E88E5")
            
            table_y_centers_r3 = [140, 230, 320, 410, 500]
            for ty in table_y_centers_r3:
                canvas.create_rectangle(75, ty - 22, 385, ty + 22, fill="#FFFDE7", outline="#FBC02D", width=1)
                canvas.create_line(75, ty, 385, ty, fill="#FFF9C4", dash=(2, 2))
            
            canvas.create_rectangle(190, 595, 270, 605, fill="#F5F5F5", outline="#F5F5F5")
            canvas.create_text(230, 590, text="▲ [정면 출입문]", font=("맑은 고딕", 9, "bold"), fill="#1E88E5")

            for i in range(1, room["total"] + 1):
                status = get_seat_status(reservations, i)
                color = STATUS_COLORS[status]
                tooltip = reservations[str(i)]["end_time"].split()[-1] if status == 1 else str(i)

                btn = tk.Button(canvas, text=tooltip, width=4, height=1, bg=color["bg"], fg=color["fg"],
                                font=("Arial", 9, "bold"), relief="flat",
                                command=lambda s=i, st=status: self.select_seat(s, st))

                if i <= 10: 
                    pos_x = (i - 1) * 38 + 53
                    pos_y = 48
                    canvas.create_window(pos_x, pos_y, window=btn)
                else:      
                    inner_idx = i - 11
                    table_idx, seat_idx = divmod(inner_idx, 6)
                    r_in_t, c_in_t = divmod(seat_idx, 3)
                    
                    pos_x = c_in_t * 100 + 115
                    pos_y = table_y_centers_r3[table_idx] - 11 if r_in_t == 0 else table_y_centers_r3[table_idx] + 11
                    canvas.create_window(pos_x, pos_y, window=btn)

        canvas.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

        legend_frame = tk.Frame(self)
        legend_frame.pack(pady=8)
        for text, color in [("배정가능", "#4CAF50"), ("사용중", "#9C27B0")]:
            tk.Label(legend_frame, bg=color, width=2, relief="flat").pack(side="left", padx=2)
            tk.Label(legend_frame, text=text, font=("맑은 고딕", 8)).pack(side="left", padx=(0, 10))

        tk.Button(self, text="이전 (열람실 목록)", font=("맑은 고딕", 10), command=self.show_room_list).pack(pady=10)

    def select_seat(self, seat_num, status):
        if status != 0:
            msgbox.showwarning("선택 불가", "이미 예약된 좌석입니다.")
            return

        rooms_data = load_rooms()
        current_booking = None
        
        # [조건 2] 사용자가 이미 다른 곳에 예약되어 있는지 전수 탐색
        for r_n, r_i in rooms_data.items():
            for s_k, s_i in r_i["reservations"].items():
                if s_i.get("user") == self.user:
                    current_booking = (r_n, s_k, s_i["end_time"])
                    break

        # 이미 이용 중인 좌석이 있다면 '이동 확인 창'을 띄움
        if current_booking:
            if msgbox.askyesno("좌석 이동 확인", f"현재 {current_booking[0]} [{current_booking[1]}번] 좌석을 이용 중입니다.\n"
                                              f"선택하신 {self.selected_room['name']} [{seat_num}번] 좌석으로 이동하시겠습니까?"):
                self.move_seat(current_booking[0], current_booking[1], seat_num, current_booking[2])
        else:
            # 기존 신규 예약 절차
            if msgbox.askyesno("예약 확인", f"{self.selected_room['name']} {seat_num}번 좌석을 예약하시겠습니까?"):
                self.reserve(seat_num)

    # [추가] 실질적인 좌석 이동(기존 좌석 제거 -> 새 좌석 등록) 알고리즘 구현
    def move_seat(self, old_room, old_seat, new_seat, end_time):
        rooms_data = load_rooms()
        
        # 1. 기존 좌석 정보 삭제
        if old_room in rooms_data and old_seat in rooms_data[old_room]["reservations"]:
            del rooms_data[old_room]["reservations"][old_seat]
            
        # 2. 새로운 좌석으로 이용 시간 그대로 유지하여 등록
        new_room_name = self.selected_room["name"]
        rooms_data[new_room_name]["reservations"][str(new_seat)] = {
            "user": self.user,
            "end_time": end_time
        }
        
        save_rooms(rooms_data)
        msgbox.showinfo("이동 완료", f"성공적으로 좌석이 이동되었습니다!\n새 좌석: {new_room_name} [{new_seat}번]")
        
        # 마이페이지로 연동되어 리턴
        self.on_back(self.user)

    def reserve(self, seat_num):
        rooms_data = load_rooms()
        room_name = self.selected_room["name"]
        seat_key = str(seat_num)

        end_dt = datetime.now() + timedelta(hours=3)
        rooms_data[room_name]["reservations"][seat_key] = {"user": self.user, "end_time": end_dt.strftime("%Y-%m-%d %H:%M")}
        save_rooms(rooms_data)

        msgbox.showinfo("예약 완료", f"성공적으로 예약되었습니다.\n종료 시간: {end_dt.strftime('%H:%M')}")
        self.on_back(self.user)