import tkinter as tk
from tkinter import messagebox, simpledialog
from tkcalendar import DateEntry
from datetime import datetime
import login_2

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
RESERVATIONS = []
TEMP_LOCKS = []

class StudyRoomPage(tk.Frame):
    def __init__(self, master, user, on_back):
        super().__init__(master)
        self.user = user
        self.on_back = on_back
        self.selected_time_slot = None  # 사용자가 선택한 시간을 저장할 변수
        self.time_buttons = {}          # 실시간 색상 변경을 위해 버튼 객체들을 저장할 딕셔너리
        self.show_date_screen()

    def clear_screen(self):
        for widget in self.winfo_children():
            widget.destroy()

    def is_reserved(self, date, room_id, time_slot):
        return any(r["date"] == date and r["room_id"] == room_id and r["time_slot"] == time_slot for r in RESERVATIONS)

    def is_locked(self, date, room_id, time_slot):
        return any(lock["date"] == date and lock["room_id"] == room_id and lock["time_slot"] == time_slot for lock in TEMP_LOCKS)

    def show_date_screen(self):
        self.clear_screen()
        self.selected_time_slot = None  # 날짜 변경 시 초기화
        
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
        self.selected_time_slot = None  # 룸 변경 시 초기화
        
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
        self.selected_time_slot = None  # 초기 진입 시 미선택 상태
        self.time_buttons = {}
        room = ROOMS[room_id]
        
        tk.Label(self, text=f"⏱️ {room['name']} 시간 예약 ({date})", font=("맑은 고딕", 15, "bold")).pack(pady=15)

        # 범례 표시 구역
        legend_frame = tk.Frame(self)
        legend_frame.pack(pady=5)
        tk.Label(legend_frame, text="예약가능", bg="#9be79b", width=10, font=("맑은 고딕", 9)).pack(side="left", padx=5)
        tk.Label(legend_frame, text="내가선택함", bg="#ffe680", width=10, font=("맑은 고딕", 9)).pack(side="left", padx=5)
        tk.Label(legend_frame, text="사용중(불가)", bg="#ff9fbd", width=10, font=("맑은 고딕", 9)).pack(side="left", padx=5)

        time_frame = tk.Frame(self)
        time_frame.pack(pady=20)

        # 시간 그리드 생성
        for index, slot in enumerate(TIME_SLOTS):
            if self.is_reserved(date, room_id, slot):
                text, color, state = f"{slot}\n[사용중]", "#ff9fbd", "disabled"
            else:
                text, color, state = f"{slot}\n[예약가능]", "#9be79b", "normal"

            btn = tk.Button(time_frame, text=text, width=12, height=2, bg=color, state=state,
                            command=lambda s=slot: self.select_time_slot(s))
            btn.grid(row=index // 4, column=index % 4, padx=6, pady=6)
            
            # 예약 가능한 버튼들만 추후 색상 제어를 위해 딕셔너리에 저장
            if state == "normal":
                self.time_buttons[slot] = btn

        # 하단 작업 관리 바 (예약하기 실행 버튼 포함)
        action_frame = tk.Frame(self)
        action_frame.pack(pady=20)

        # 최종 예약 진행 버튼 (처음엔 골라진 시간이 없으므로 일반 상태로 유도하고 클릭 시 체크)
        tk.Button(action_frame, text="선택한 시간으로 예약하기", font=("맑은 고딕", 11, "bold"), 
                  bg="#4CAF50", fg="white", width=25, height=2,
                  command=lambda: self.reserve_room(date, room_id)).pack(pady=10)

        tk.Button(action_frame, text="이전 (스터디룸 목록으로)", font=("맑은 고딕", 10), 
                  command=lambda: self.show_room_screen(date)).pack(side="left", padx=10)

    def select_time_slot(self, slot):
        """[개선 기능] 사용자가 시간을 누르면 즉시 예약하지 않고 '내가선택함' 노란색으로 상태 토글"""
        # 기존에 선택되어 있던 버튼이 있다면 원래 색상(연두색)으로 되돌림
        if self.selected_time_slot and self.selected_time_slot in self.time_buttons:
            self.time_buttons[self.selected_time_slot].config(bg="#9be79b", text=f"{self.selected_time_slot}\n[예약가능]")
        
        # 새로 선택한 슬롯 저장 및 색상 강조
        self.selected_time_slot = slot
        if slot in self.time_buttons:
            self.time_buttons[slot].config(bg="#ffe680", text=f"{slot}\n[선택됨]")

    def reserve_room(self, date, room_id):
        """[개선 기능] 하단 버튼을 눌렀을 때 비로소 작동하며, 선택된 시간이 있을 때만 명단 입력 팝업 노출"""
        room = ROOMS[room_id]
        
        # 예외 처리: 시간을 고르지 않고 예약 버튼부터 누른 경우 차단
        if not self.selected_time_slot:
            messagebox.showwarning("선택 오류", "먼저 이용하실 시간대를 위 그리드에서 클릭해 주세요.")
            return

        time_slot = self.selected_time_slot

        # 이중 예약 방지를 위한 최종 실시간 상태 재검증
        if self.is_reserved(date, room_id, time_slot):
            messagebox.showerror("예약 불가", "그새 다른 사용자가 예약을 완료한 시간대입니다. 다른 시간을 골라주세요.")
            return

        # 팝업을 띄워 팀원 확인 받기
        member_input = simpledialog.askstring("팀원 명단 인증", f"[{time_slot}]에 동반 이용할 팀원의 학번을 쉼표(,)로 구분해 입력하세요.")
        if member_input is None: 
            return

        members = [m.strip() for m in member_input.split(",") if m.strip()]
        
        if self.user in members:
            messagebox.showerror("입력 오류", "방장(본인) 학번은 명단에 명시할 필요가 없습니다.")
            return

        # 회원가입 데이터베이스(users.json) 연동 검증
        registered_users = login_2.load_users()
        invalid_members = [m for m in members if m not in registered_users]

        if invalid_members:
            messagebox.showerror("예약 불가", f"존재하지 않는 유저(학번)가 포함되어 있습니다:\n{', '.join(invalid_members)}\n회원가입 여부를 확인해 주세요.")
            return

        total_people = len(members) + 1
        if total_people < room["min_people"] or total_people > room["capacity"]:
            messagebox.showerror("인원 기준 오류", f"해당 룸 인원 조건 제한에 부합하지 않습니다.\n(최소: {room['min_people']}명, 최대: {room['capacity']}명)\n현재 입력 인원: {total_people}명")
            return

        # 중앙 저장소 데이터에 반영
        RESERVATIONS.append({
            "leader": self.user, "members": members, "date": date,
            "room_id": room_id, "time_slot": time_slot, "people_count": total_people, "checked_in": False
        })
        
        messagebox.showinfo("예약 완료", f"{room['name']} [{time_slot}] 예약이 확정되었습니다.\n현황은 마이페이지에서 통합 관리됩니다.")
        
        # 예약이 완료되면 부드럽게 메인 마이페이지 대시보드로 복귀
        self.on_back()