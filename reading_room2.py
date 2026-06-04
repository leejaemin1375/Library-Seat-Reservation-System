import tkinter as tk
import tkinter.messagebox as msgbox
import json
import os
import threading
from datetime import datetime, timedelta

ROOMS_FILE = "reading_rooms.json"
_lock = threading.RLock()  # 동시 접근 방지

# 열람실 기본 정보
ROOMS = [
    {"name": "열람실1", "total": 20},
    {"name": "열람실2", "total": 30},
    {"name": "열람실3", "total": 40},
]

# 좌석 상태별 색상
STATUS_COLORS = {
    0: {"bg": "#4CAF50", "fg": "white"},  # 배정가능 - 초록
    1: {"bg": "#9C27B0", "fg": "white"},  # 사용중   - 보라
    2: {"bg": "#F44336", "fg": "white"},  # 배정불가 - 빨강
}

# ── JSON 불러오기 / 저장 ──────────────────────────────
def load_rooms():
    with _lock:
        if os.path.exists(ROOMS_FILE):
            with open(ROOMS_FILE, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    pass
        # 파일 없거나 깨진 경우 기본값 생성
        default = {r["name"]: {"total": r["total"], "reservations": {}} for r in ROOMS}
        save_rooms(default)
        return default

def save_rooms(data):
    with _lock:
        with open(ROOMS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

# ── 좌석 상태 판단 ────────────────────────────────────
def get_seat_status(reservations, seat_num):
    seat_key = str(seat_num)
    if seat_key not in reservations:
        return 0  # 배정가능
    end_dt = datetime.strptime(reservations[seat_key]["end_time"], "%Y-%m-%d %H:%M")
    if datetime.now() < end_dt:
        return 1  # 사용중
    else:
        return 0  # 종료 시간 지남 → 배정가능


class ReadingRoomPage(tk.Frame):
    def __init__(self, master, user, on_back):
        super().__init__(master)
        self.user = user
        self.on_back = on_back
        self.selected_room = None
        self.selected_seat = None
        self.is_moving = False
        self.moving_info = None
        self.show_room_list()

    def _clear(self):
        for widget in self.winfo_children():
            widget.destroy()

    # ── 열람실 목록 화면 ──────────────────────────────
    def show_room_list(self):
        self._clear()
        rooms_data = load_rooms()

        top_frame = tk.Frame(self)
        top_frame.pack(fill="x", padx=15, pady=10)

        tk.Label(top_frame, text="열람실 예약",
                 font=("Arial", 14, "bold")).pack(side="left", pady=15)

        right_frame = tk.Frame(top_frame)
        right_frame.pack(side="right")
        tk.Label(right_frame, text=f"{self.user}님",
                 font=("Arial", 10, "bold")).pack(anchor="e")
        tk.Button(right_frame, text="내 예약", width=10,
                  command=self.show_my_reservation).pack(anchor="e", pady=3)
        
        if self.is_moving:
            tk.Label(self, text="이동할 좌석을 선택하세요",
                    font=("Arial", 10), fg="red").pack()

        tk.Label(self, text="열람좌석",
                 font=("Arial", 10, "bold"), anchor="w").pack(fill="x", padx=20)

        for room in ROOMS:
            # 현재 사용 중인 좌석 수 계산
            reservations = rooms_data.get(room["name"], {}).get("reservations", {})
            used = sum(1 for s in reservations.values()
                       if datetime.now() < datetime.strptime(s["end_time"], "%Y-%m-%d %H:%M"))
            self._make_room_card(room, used)

        tk.Button(self, text="뒤로", width=15,
                  command=lambda: self.on_back(self.user)).pack(pady=10)

    def _make_room_card(self, room, used):
        card = tk.Frame(self, relief="solid", bd=1, padx=10, pady=8)
        card.pack(fill="x", padx=20, pady=4)

        # 열람실 이름
        tk.Label(card, text=room["name"],
                 font=("Arial", 11, "bold"), anchor="w").pack(fill="x")

        # 사용 / 전체 숫자
        count_frame = tk.Frame(card)
        count_frame.pack(fill="x")
        tk.Label(count_frame, text=f"{used} / {room['total']} 사용 중",
                 font=("Arial", 9), fg="#555").pack(side="left")

        # 카드 클릭 시 좌석 화면으로 이동
        for widget in [card] + card.winfo_children():
            widget.bind("<Button-1>",
                        lambda e, r=room: self.show_seat_map(r))

    # ── 유저 예약 찾기 ──────────────────────────
    def find_my_reservation(self, rooms_data):
        for room_name, room_data in rooms_data.items():
            for seat_key, info in room_data["reservations"].items():
                if info["user"] == self.user:
                    end_dt = datetime.strptime(info["end_time"], "%Y-%m-%d %H:%M")
                    if datetime.now() < end_dt:
                        return room_name, seat_key, info
        return None, None, None  # 예약 없음

    # ── 내 예약 정보 화면 ─────────────────────────────
    def show_my_reservation(self):
        self._clear()
        rooms_data = load_rooms()

        tk.Label(self, text="내 예약 정보",
                 font=("Arial", 14, "bold")).pack(pady=15)

        room_name, seat_key, info = self.find_my_reservation(rooms_data)

        if room_name is None:
            tk.Label(self, text="현재 예약된 좌석이 없습니다.",
                     font=("Arial", 11), fg="#555").pack(pady=30)
        else:
            end_dt = datetime.strptime(info["end_time"], "%Y-%m-%d %H:%M")
            card = tk.Frame(self, relief="solid", bd=1, padx=15, pady=10)
            card.pack(fill="x", padx=20, pady=5)
            tk.Label(card, text=room_name,
                     font=("Arial", 11, "bold"), anchor="w").pack(fill="x")
            tk.Label(card, text=f"좌석 번호: {seat_key}번",
                     font=("Arial", 10), anchor="w").pack(fill="x")
            tk.Label(card, text=f"종료 시간: {end_dt.strftime('%H:%M')}",
                     font=("Arial", 10), fg="#9C27B0", anchor="w").pack(fill="x")

            tk.Button(self, text="시간 연장",
                      command=lambda: self.extend_time(room_name, seat_key)).pack(pady=5)
            tk.Button(self, text="자리 이동",
                      command=lambda: self.start_move(room_name, seat_key, info["end_time"])).pack(pady=5)

        tk.Button(self, text="뒤로", width=15,
                  command=self.show_room_list).pack(pady=10)
        
    # 자리 이동    
    def move_seat(self):
        rooms_data = load_rooms()

        # 기존 좌석 삭제
        old_room = self.moving_info["room"]
        old_seat = self.moving_info["seat"]
        del rooms_data[old_room]["reservations"][old_seat]

        # 새 좌석에 기존 종료시간으로 저장
        new_room = self.selected_room["name"]
        new_seat = str(self.selected_seat)
        rooms_data[new_room]["reservations"][new_seat] = {
            "user": self.user,
            "end_time": self.moving_info["end_time_raw"]  # 원본 시간 문자열
        }
        save_rooms(rooms_data)

        self.is_moving = False
        self.moving_info = None

        msgbox.showinfo("이동 완료", f"{new_room} {new_seat}번 좌석으로 이동했습니다!")
        self.show_my_reservation()

    # 자리 이동 플래그 변경
    def start_move(self, room_name, seat_key, end_time_raw):
        self.is_moving = True
        self.moving_info = {
            "room": room_name,
            "seat": seat_key,
            "end_time_raw": end_time_raw  # 원본 시간 문자열 저장
        }
        self.show_room_list()

    # 시간 연장 함수
    def extend_time(self, room_name, seat_key):
        rooms_data = load_rooms()
        end_dt = datetime.strptime(
            rooms_data[room_name]["reservations"][seat_key]["end_time"],
            "%Y-%m-%d %H:%M")
        
        new_end_dt = end_dt + timedelta(hours=1)
        rooms_data[room_name]["reservations"][seat_key]["end_time"] = \
            new_end_dt.strftime("%Y-%m-%d %H:%M")
        
        save_rooms(rooms_data)
        msgbox.showinfo("연장 완료",
                        f"연장되었습니다!\n종료 시간: {new_end_dt.strftime('%H:%M')}")
        self.show_my_reservation()

    # ── 좌석 배치 화면 ───────────────────────────────
    def show_seat_map(self, room):
        self._clear()
        self.selected_room = room
        self.selected_seat = None

        rooms_data = load_rooms()
        reservations = rooms_data.get(room["name"], {}).get("reservations", {})

        tk.Label(self, text=room["name"],
                 font=("Arial", 13, "bold")).pack(pady=10)

        # 스크롤 가능한 좌석 영역
        container = tk.Frame(self)
        container.pack(fill="both", expand=True, padx=10)

        canvas = tk.Canvas(container)
        scrollbar = tk.Scrollbar(container, orient="vertical",
                                 command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        seat_frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=seat_frame, anchor="nw")

        # 좌석 버튼 생성 (8열 그리드)
        cols = 10
        for i in range(1, room["total"] + 1):
            status = get_seat_status(reservations, i)
            row, col = divmod(i - 1, cols)
            color = STATUS_COLORS[status]

            # 사용중이면 종료 시간 표시
            seat_key = str(i)
            if status == 1:
                end_time = datetime.strptime(
                    reservations[seat_key]["end_time"], "%Y-%m-%d %H:%M")
                tooltip = end_time.strftime("%H:%M")
            else:
                tooltip = str(i)

            tk.Button(seat_frame,
                      text=tooltip, width=3, height=1,
                      bg=color["bg"], fg=color["fg"],
                      font=("Arial", 9, "bold"), relief="flat",
                      command=lambda s=i, st=status: self.select_seat(s, st)
                      ).grid(row=row, column=col, padx=2, pady=2)

        seat_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

        # 범례
        legend_frame = tk.Frame(self)
        legend_frame.pack(pady=5)
        for text, color in [("배정가능", "#4CAF50"),
                            ("사용중",   "#9C27B0"),
                            ("배정불가", "#F44336")]:
            tk.Label(legend_frame, bg=color, width=2,
                     relief="flat").pack(side="left", padx=2)
            tk.Label(legend_frame, text=text,
                     font=("Arial", 8)).pack(side="left", padx=(0, 10))

        tk.Button(self, text="뒤로", width=15,
                  command=self.show_room_list).pack(pady=5)

    # ── 좌석 선택 및 예약 ────────────────────────────
    def select_seat(self, seat_num, status):
        if status != 0:
            msgbox.showwarning("선택 불가",
                               "이미 사용 중이거나 배정 불가한 좌석입니다.")
            return
        self.selected_seat = seat_num
        answer = msgbox.askyesno(
            "예약 확인",
            f"{self.selected_room['name']}\n{seat_num}번 좌석을 예약하시겠습니까?")
        if answer:
            if self.is_moving:
                self.move_seat()
            else:
                self.reserve()

    def reserve(self):
        rooms_data = load_rooms()
        room_name = self.selected_room["name"]
        seat_key = str(self.selected_seat)

        # 이미 예약이 있는지 확인
        r_name, s_key, existing = self.find_my_reservation(rooms_data)
        if r_name is not None:
            msgbox.showwarning("예약 불가", "이미 예약된 좌석이 있습니다.")
            return

        # 현재 시간 + 3시간 계산
        end_dt = datetime.now() + timedelta(hours=3)
        end_str = end_dt.strftime("%Y-%m-%d %H:%M")

        # JSON에 저장
        rooms_data[room_name]["reservations"][seat_key] = {
            "user": self.user,
            "end_time": end_str
        }
        save_rooms(rooms_data)

        msgbox.showinfo("예약 완료",
                        f"예약이 완료되었습니다!\n종료 시간: {end_dt.strftime('%H:%M')}")
        self.show_seat_map(self.selected_room)

        tk.Button(self, text="메인 화면으로 돌아가기",
                  width=18, bg="#2196F3", fg="white",
                  command=self.show_room_list).pack(pady=10)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("열람실 예약")
    root.geometry("400x500")
    ReadingRoomPage(root, user="테스트2", on_back=lambda u: None).pack(fill="both", expand=True) # 메인 페이지로 연결 필요
    root.mainloop()
