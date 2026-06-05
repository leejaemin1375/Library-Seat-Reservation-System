import tkinter as tk
from tkinter import messagebox, simpledialog
from tkcalendar import DateEntry
from datetime import datetime
import json
import os
import threading
import login_2

# 스터디룸 예약 정보가 저장될 파일 및 동시성 제어 락 설정
STUDY_ROOMS_FILE = "study_rooms.json"
_lock = threading.RLock()

ROOMS = {
    1: {"name": "그룹스터디룸1", "capacity": 12, "min_people": 6, "checkin_code": "A101"},
    2: {"name": "그룹스터디룸2", "capacity": 10, "min_people": 5, "checkin_code": "A102"},
    3: {"name": "그룹스터디룸3", "capacity": 6, "min_people": 3, "checkin_code": "A103"},
    4: {"name": "그룹스터디룸4", "capacity": 6, "min_people": 3, "checkin_code": "A104"},
    5: {"name": "그룹스터디룸5", "capacity": 4, "min_people": 2, "checkin_code": "A105"},
    6: {"name": "그룹스터디룸6", "capacity": 4, "min_people": 2, "checkin_code": "A106"},
    7: {"name": "그룹스터디룸7", "capacity": 4, "min_people": 2, "checkin_code": "A107"},
    8: {"name": "그룹스터디룸8", "capacity": 4, "min_people": 2, "checkin_code": "A108"},
    9: {"name": "그룹스터디룸9", "capacity": 8, "min_people": 4, "checkin_code": "A109"},
    10: {"name": "그룹스터디룸10", "capacity": 8, "min_people": 4, "checkin_code": "A110"},
    11: {"name": "소회의실", "capacity": 20, "min_people": 10, "checkin_code": "B201"},
}

TIME_SLOTS = [f"{hour:02d}-{hour+1:02d}" for hour in range(9, 21)]
TEMP_LOCKS = []

# ── [추가] JSON 불러오기 / 저장 함수 ──────────────────────────────
def load_study_reservations():
    """파일에서 스터디룸 예약 리스트를 안전하게 불러옵니다."""
    with _lock:
        if os.path.exists(STUDY_ROOMS_FILE):
            with open(STUDY_ROOMS_FILE, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return []
        return []

def save_study_reservations(data):
    """스터디룸 예약 리스트를 파일에 안전하게 저장합니다."""
    with _lock:
        try:
            with open(STUDY_ROOMS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except IOError:
            messagebox.showerror("파일 오류", "스터디룸 데이터를 저장하는 중 에러가 발생했습니다.")

# 다른 모듈(main.py)에서 전역 리스트처럼 참조할 수 있도록 동적 프로퍼티(리스트 대행 변수) 구현
class ReservationsProxy(list):
    def __iter__(self):
        return iter(load_study_reservations())
    def __len__(self):
        return len(load_study_reservations())
    def append(self, item):
        current_data = load_study_reservations()
        current_data.append(item)
        save_study_reservations(current_data)
    def remove(self, item):
        current_data = load_study_reservations()
        if item in current_data:
            current_data.remove(item)
            save_study_reservations(current_data)
        else:
            # 주소값이 달라 비교가 안 될 경우를 대비한 값 기반 2차 삭제 처리
            for block in current_data:
                if (block["leader"] == item["leader"] and 
                    block["date"] == item["date"] and 
                    block["room_id"] == item["room_id"] and 
                    block["time_slot"] == item["time_slot"]):
                    current_data.remove(block)
                    save_study_reservations(current_data)
                    break

# 외부 main.py의 구조적 변경 없이 파일과 완벽 연동되도록 프록시 객체 배치
RESERVATIONS = ReservationsProxy()


class StudyRoomPage(tk.Frame):
    def __init__(self, master, user, on_back):
        super().__init__(master)
        self.user = user
        self.on_back = on_back
        self.selected_slots = []
        self.time_buttons = {}
        
        if hasattr(self.master, "resizable"):
            self.master.resizable(False, False)
            
        self.show_date_screen()

    def clear_screen(self):
        for widget in self.winfo_children():
            widget.destroy()

    def is_reserved(self, date, room_id, time_slot):
        return any(r["date"] == date and r["room_id"] == room_id and r["time_slot"] == time_slot for r in load_study_reservations())

    def is_locked(self, date, room_id, time_slot):
        return any(lock["date"] == date and lock["room_id"] == room_id and lock["time_slot"] == time_slot for lock in TEMP_LOCKS)

    def is_past_time(self, date_str, time_slot):
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            today = datetime.now().date()
            if target_date < today:
                return True
            if target_date == today:
                current_hour = datetime.now().hour
                start_hour = int(time_slot.split("-")[0])
                if start_hour <= current_hour:
                    return True
            return False
        except ValueError:
            return True

    def show_date_screen(self):
        self.clear_screen()
        self.selected_slots = []
        
        tk.Label(self, text="그룹 스터디룸 예약", font=("맑은 고딕", 18, "bold")).pack(pady=20)
        tk.Label(self, text="예약 희망 날짜를 조회해 주세요.", font=("맑은 고딕", 11)).pack(pady=5)
        
        frame = tk.Frame(self)
        frame.pack(pady=30)
        
        date_entry = DateEntry(frame, width=18, font=("맑은 고딕", 12), date_pattern="yyyy-mm-dd", mindate=datetime.today().date())
        date_entry.pack(side="left", padx=10)
        
        tk.Button(frame, text="예약 가능 조회", font=("맑은 고딕", 10, "bold"), bg="#2196F3", fg="white",
                  command=lambda: self.show_room_screen(date_entry.get().strip())).pack(side="left")
        
        tk.Button(self, text="메인 마이페이지로 돌아가기", font=("맑은 고딕", 10), command=self.on_back).pack(pady=20)

    def show_room_screen(self, date):
        self.clear_screen()
        self.selected_slots = []
        
        tk.Label(self, text=f"📅 {date} 스터디룸 선택", font=("맑은 고딕", 16, "bold")).pack(pady=15)

        canvas_frame = tk.Frame(self)
        canvas_frame.pack(fill="both", expand=True, padx=20)
        
        canvas = tk.Canvas(canvas_frame)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        room_grid = tk.Frame(canvas)
        canvas.create_window((0, 0), window=room_grid, anchor="nw")

        for room_id, room in ROOMS.items():
            btn = tk.Button(room_grid, text=f"{room['name']}\n정원 {room['capacity']}명 (최소 {room['min_people']}명)",
                            width=24, height=3, bg="#e3f2fd", command=lambda r=room_id: self.show_time_screen(date, r))
            btn.grid(row=(room_id - 1) // 3, column=(room_id - 1) % 3, padx=12, pady=12)

        room_grid.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

        tk.Button(self, text="이전 (날짜 선택으로)", font=("맑은 고딕", 10), command=self.show_date_screen).pack(pady=15)

    def show_time_screen(self, date, room_id):
        self.clear_screen()
        self.selected_slots = []
        self.time_buttons = {}
        room = ROOMS[room_id]
        
        tk.Label(self, text=f"⏱️ {room['name']} 시간 예약 ({date})", font=("맑은 고딕", 15, "bold")).pack(pady=15)

        legend_frame = tk.Frame(self)
        legend_frame.pack(pady=5)
        tk.Label(legend_frame, text="예약가능", bg="#9be79b", width=10, font=("맑은 고딕", 9)).pack(side="left", padx=5)
        tk.Label(legend_frame, text="내가선택함", bg="#ffe680", width=10, font=("맑은 고딕", 9)).pack(side="left", padx=5)
        tk.Label(legend_frame, text="사용중/마감", bg="#ff9fbd", width=10, font=("맑은 고딕", 9)).pack(side="left", padx=5)

        time_frame = tk.Frame(self)
        time_frame.pack(pady=20)

        for index, slot in enumerate(TIME_SLOTS):
            if self.is_past_time(date, slot):
                text, color, state = f"{slot}\n[마감]", "#e0e0e0", "disabled"
            elif self.is_reserved(date, room_id, slot):
                text, color, state = f"{slot}\n[사용중]", "#ff9fbd", "disabled"
            else:
                text, color, state = f"{slot}\n[예약가능]", "#9be79b", "normal"

            btn = tk.Button(time_frame, text=text, width=12, height=2, bg=color, state=state,
                            command=lambda s=slot: self.select_time_slot(s))
            btn.grid(row=index // 4, column=index % 4, padx=6, pady=6)
            
            if state == "normal":
                self.time_buttons[slot] = btn

        action_frame = tk.Frame(self)
        action_frame.pack(pady=20)

        tk.Button(action_frame, text="선택한 시간으로 예약하기", font=("맑은 고딕", 11, "bold"), 
                  bg="#4CAF50", fg="white", width=25, height=2,
                  command=lambda: self.reserve_room(date, room_id)).pack(pady=10)

        tk.Button(action_frame, text="이전 (스터디룸 목록으로)", font=("맑은 고딕", 10), 
                  command=lambda: self.show_room_screen(date)).pack(side="left", padx=10)

    def select_time_slot(self, slot):
        if slot in self.selected_slots:
            idx = self.selected_slots.index(slot)
            for s in self.selected_slots[idx:]:
                if s in self.time_buttons:
                    self.time_buttons[s].config(bg="#9be79b", text=f"{s}\n[예약가능]")
            self.selected_slots = self.selected_slots[:idx]
            return

        if len(self.selected_slots) >= 3:
            messagebox.showwarning("선택 제한", "스터디룸은 최대 연속 3시간까지만 예약이 가능합니다.\n기존 선택이 초기화됩니다.")
            self.reset_all_slots()
            return

        if self.selected_slots:
            hours = sorted([int(s.split("-")[0]) for s in self.selected_slots])
            new_hour = int(slot.split("-")[0])
            if not (new_hour == hours[-1] + 1 or new_hour == hours[0] - 1):
                messagebox.showwarning("선택 오류", "연속된 시간대만 함께 선택하여 예약할 수 있습니다.")
                self.reset_all_slots()
                return

        self.selected_slots.append(slot)
        self.selected_slots.sort()
        if slot in self.time_buttons:
            self.time_buttons[slot].config(bg="#ffe680", text=f"{slot}\n[선택됨]")

    def reset_all_slots(self):
        for s in self.selected_slots:
            if s in self.time_buttons:
                self.time_buttons[s].config(bg="#9be79b", text=f"{s}\n[예약가능]")
        self.selected_slots = []

    def reserve_room(self, date, room_id):
        room = ROOMS[room_id]
        
        if not self.selected_slots:
            messagebox.showwarning("선택 오류", "먼저 이용하실 시간대를 위 그리드에서 클릭해 주세요. (최대 3시간 연속 가능)")
            return

        time_summary = f"{self.selected_slots[0].split('-')[0]}:00 ~ {self.selected_slots[-1].split('-')[1]}:00"

        for slot in self.selected_slots:
            if self.is_reserved(date, room_id, slot):
                messagebox.showerror("예약 불가", f"선택하신 시간대 중 [{slot}]이 이미 예약되었습니다. 다시 설정해 주세요.")
                return

        member_input = simpledialog.askstring("팀원 명단 인증", f"[{time_summary}]에 동반 이용할 팀원의 학번을 쉼표(,)로 구분해 입력하세요.")
        if member_input is None: 
            return

        members = [m.strip() for m in member_input.split(",") if m.strip()]
        
        if self.user in members:
            messagebox.showerror("입력 오류", "방장(본인) 학번은 명단에 명시할 필요가 없습니다.")
            return

        registered_users = login_2.load_users()
        invalid_members = [m for m in members if m not in registered_users]

        if invalid_members:
            messagebox.showerror("예약 불가", f"존재하지 않는 유저(학번)가 포함되어 있습니다:\n{', '.join(invalid_members)}\n회원가입 여부를 확인해 주세요.")
            return

        total_people = len(members) + 1
        if total_people < room["min_people"] or total_people > room["capacity"]:
            messagebox.showerror("인원 기준 오류", f"해당 룸 인원 조건 제한에 부합하지 않습니다.\n(최소: {room['min_people']}명, 최대: {room['capacity']}명)\n현재 입력 인원: {total_people}명")
            return

        # 리스트에 데이터를 넣으면 프록시 객체가 감지하여 자동으로 json 파일에 쓰기 작업을 수행합니다.
        for slot in self.selected_slots:
            RESERVATIONS.append({
                "leader": self.user, "members": members, "date": date,
                "room_id": room_id, "time_slot": slot, "people_count": total_people, "checked_in": False
            })
        
        messagebox.showinfo("예약 완료", f"{room['name']} [{time_summary}] 연속 예약이 확정되었습니다.\n현황은 마이페이지에서 통합 관리됩니다.")
        self.on_back()