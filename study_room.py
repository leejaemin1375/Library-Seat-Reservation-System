import tkinter as tk
from tkinter import messagebox, simpledialog
from tkcalendar import DateEntry
from datetime import datetime
import json
import os

STUDY_ROOMS_FILE = "study_rooms.json"
STUDY_ROOMS_CONFIG_FILE = "study_rooms_config.json"

def load_study_reservations():
    if os.path.exists(STUDY_ROOMS_FILE):
        with open(STUDY_ROOMS_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                return data if isinstance(data, list) else []
            except json.JSONDecodeError:
                return []
    return []

def save_study_reservations(reservations):
    try:
        with open(STUDY_ROOMS_FILE, "w", encoding="utf-8") as f:
            json.dump(reservations, f, ensure_ascii=False, indent=4)
    except IOError:
        messagebox.showerror("파일 오류", "스터디룸 데이터를 저장하는 중 에러가 발생했습니다.")

def load_rooms_config():
    if os.path.exists(STUDY_ROOMS_CONFIG_FILE):
        with open(STUDY_ROOMS_CONFIG_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                return {int(k): v for k, v in data.items()}
            except (json.JSONDecodeError, ValueError):
                pass
    return {}

ROOMS = load_rooms_config()
TIME_SLOTS = [f"{hour:02d}:00-{(hour+1):02d}:00" for hour in range(9, 21)]
TEMP_LOCKS = []

class StudyRoomPage(tk.Frame):
    def __init__(self, master, user, on_back):
        super().__init__(master)
        self.user = user
        self.on_back = on_back
        self.show_date_screen()

    def clear_screen(self):
        for widget in self.winfo_children():
            widget.destroy()

    def is_reserved(self, date, room_id, time_slot):
        reservations = load_study_reservations()
        return any(r["date"] == date and int(r["room_id"]) == int(room_id) and r["time_slot"] == time_slot for r in reservations)

    def is_locked(self, date, room_id, time_slot):
        return any(lock["date"] == date and int(lock["room_id"]) == int(room_id) and lock["time_slot"] == time_slot for lock in TEMP_LOCKS)

    def add_lock(self, date, room_id, time_slot):
        TEMP_LOCKS.append({"date": date, "room_id": room_id, "time_slot": time_slot, "user": self.user})

    def remove_lock(self, date, room_id, time_slot):
        for lock in TEMP_LOCKS:
            if lock["date"] == date and int(lock["room_id"]) == int(room_id) and lock["time_slot"] == time_slot and lock["user"] == self.user:
                TEMP_LOCKS.remove(lock)
                return

    def is_past_time(self, date, time_slot):
        try:
            selected_date = datetime.strptime(date, "%Y-%m-%d").date()
            now = datetime.now()
            if selected_date != now.date():
                return False
            end_hour = int(time_slot.split("-")[1].split(":")[0])
            end_time = datetime(now.year, now.month, now.day, end_hour, 0)
            return now >= end_time
        except Exception:
            return True

    def show_date_screen(self):
        self.clear_screen()
        tk.Label(self, text="스터디룸 예약 시스템", font=("맑은 고딕", 22, "bold")).pack(pady=25)
        tk.Label(self, text=f"현재 로그인 사용자: {self.user}", font=("맑은 고딕", 12)).pack(pady=5)
        tk.Label(self, text="예약할 날짜를 선택하세요.", font=("맑은 고딕", 15)).pack(pady=20)
        
        tk.Button(self, text="내 예약 조회 / 취소 / 자리이동", command=self.show_my_reservation_screen).pack(pady=15)
        
        frame = tk.Frame(self)
        frame.pack(pady=10)
        tk.Label(frame, text="날짜 입력:", font=("맑은 고딕", 12)).pack(side="left")
        
        date_entry = DateEntry(frame, width=18, font=("맑은 고딕", 12), background="darkblue",
                              foreground="white", borderwidth=2, date_pattern="yyyy-mm-dd", mindate=datetime.today().date())
        date_entry.set_date(datetime.today())
        date_entry.pack(side="left", padx=10)
        
        tk.Button(frame, text="조회", font=("맑은 고딕", 11), command=lambda: self.show_room_screen(date_entry.get().strip())).pack(side="left")
        tk.Button(self, text="메인메뉴로", font=("맑은 고딕", 11), command=self.on_back).pack(pady=30)

    def show_room_screen(self, date):
        if not date:
            messagebox.showwarning("입력 오류", "날짜를 입력하세요.")
            return
        self.clear_screen()
        tk.Label(self, text=f"{date} 예약할 공간 선택", font=("맑은 고딕", 20, "bold")).pack(pady=20)

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
            btn = tk.Button(room_grid, text=f"{room['name']}\n정원 {room['capacity']}명 / 최소 {room['min_people']}명",
                            width=22, height=3, bg="#d9eaff", command=lambda r=room_id: self.show_time_screen(date, r))
            btn.grid(row=(room_id - 1) // 3, column=(room_id - 1) % 3, padx=10, pady=10)

        room_grid.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

        bottom = tk.Frame(self)
        bottom.pack(pady=15)
        tk.Button(bottom, text="날짜 다시 선택", command=self.show_date_screen).pack(side="left", padx=10)
        # 4번 요구사항: 공간 선택 화면 뒤로가기 버튼 추가
        tk.Button(bottom, text="메인메뉴로", command=self.on_back).pack(side="left", padx=10)

    def show_time_screen(self, date, room_id):
        self.clear_screen()
        room = ROOMS[room_id]

        tk.Label(self, text=f"{room['name']} 예약 가능 시간", font=("맑은 고딕", 20, "bold")).pack(pady=15)
        tk.Label(self, text=f"날짜: {date}  |  정원: {room['capacity']}명  |  최소인원: {room['min_people']}명", font=("맑은 고딕", 11)).pack(pady=5)

        legend = tk.Frame(self)
        legend.pack(pady=5)
        tk.Label(legend, text="가능", bg="#9be79b", width=8).pack(side="left", padx=5)
        tk.Label(legend, text="선택중", bg="#ffe680", width=8).pack(side="left", padx=5)
        tk.Label(legend, text="사용중", bg="#ff9fbd", width=8).pack(side="left", padx=5)

        time_frame = tk.Frame(self)
        time_frame.pack(pady=15)

        for index, slot in enumerate(TIME_SLOTS):
            if self.is_past_time(date, slot):
                text, color, state = f"{slot}\n마감", "#d3d3d3", "disabled"
            elif self.is_reserved(date, room_id, slot):
                text, color, state = f"{slot}\n사용중", "#ff9fbd", "disabled"
            elif self.is_locked(date, room_id, slot):
                text, color, state = f"{slot}\n선택중", "#ffe680", "disabled"
            else:
                text, color, state = f"{slot}\n가능", "#9be79b", "normal"

            tk.Button(time_frame, text=text, width=13, height=2, bg=color, state=state,
                      command=lambda s=slot: self.reserve_room(date, room_id, s)).grid(row=index // 4, column=index % 4, padx=6, pady=6)

        bottom = tk.Frame(self)
        bottom.pack(pady=10)
        tk.Button(bottom, text="공간 다시 선택", command=lambda: self.show_room_screen(date)).pack(side="left", padx=10)
        tk.Button(bottom, text="날짜 다시 선택", command=self.show_date_screen).pack(side="left", padx=10)
        # 4번 요구사항: 시간 선택 화면 뒤로가기 버튼 추가
        tk.Button(bottom, text="메인메뉴로", command=self.on_back).pack(side="left", padx=10)

    def reserve_room(self, date, room_id, time_slot):
        room = ROOMS[room_id]
        if self.is_reserved(date, room_id, time_slot) or self.is_locked(date, room_id, time_slot):
            messagebox.showerror("예약 불가", "신청할 수 없는 시간대입니다.")
            return

        self.add_lock(date, room_id, time_slot)
        
        member_input = simpledialog.askstring("팀원 학번 입력", f"본인({self.user}) 외 팀원 학번을 쉼표(,)로 구분하여 입력하세요.")
        if member_input is None:
            self.remove_lock(date, room_id, time_slot)
            self.show_time_screen(date, room_id)
            return

        members = [m.strip() for m in member_input.split(",")] if member_input.strip() else []
        
        if str(self.user) in members:
            messagebox.showerror("입력 오류", "본인 학번은 자동으로 포함됩니다.")
            self.remove_lock(date, room_id, time_slot)
            return

        total_people = len(members) + 1
        if total_people < room["min_people"] or total_people > room["capacity"]:
            messagebox.showerror("예약 불가", f"인원 조건 미달 또는 초과 (최소: {room['min_people']}, 최대: {room['capacity']})")
            self.remove_lock(date, room_id, time_slot)
            return

        reservations = load_study_reservations()
        reservations.append({
            "leader": str(self.user), 
            "members": members, 
            "date": date, 
            "room_id": int(room_id), 
            "time_slot": time_slot, 
            "people_count": total_people, 
            "checked_in": False
        })
        save_study_reservations(reservations)
        self.remove_lock(date, room_id, time_slot)
        
        messagebox.showinfo(
            "예약 완료", 
            "정상적으로 예약되었습니다.\n\n"
            "※ [노쇼 방지 필수 안내]\n"
            "예약 시작 시간 전후 10분 이내에 해당 스터디룸 출입문 및 벽면에 부착된 "
            "실제 인증 코드를 마이페이지에서 정확히 등록해야 입실 처리됩니다."
        )
        self.show_time_screen(date, room_id)

    def show_my_reservation_screen(self):
        self.clear_screen()
        tk.Label(self, text="내 예약 조회 / 취소", font=("맑은 고딕", 20, "bold")).pack(pady=20)

        reservations = load_study_reservations()
        my_res = [r for r in reservations if str(r["leader"]) == str(self.user)]

        if not my_res:
            tk.Label(self, text="현재 예약 내역이 없습니다.", font=("맑은 고딕", 13)).pack(pady=20)
        else:
            for r in my_res:
                room_info = ROOMS.get(int(r["room_id"]))
                room_name = room_info["name"] if room_info else f"알 수 없는 방(ID: {r['room_id']})"
                frame = tk.Frame(self, relief="solid", borderwidth=1)
                frame.pack(pady=5, padx=20, fill="x")

                status_txt = "체크인 완료" if r.get("checked_in") else "체크인 전"
                text = f"날짜: {r['date']} | 공간: {room_name} | 시간: {r['time_slot']}\n상태: {status_txt} | 인원: {r['people_count']}명"
                
                tk.Label(frame, text=text, font=("맑은 고딕", 10), justify="left").pack(side="left", padx=10, pady=5)
                tk.Button(frame, text="취소", bg="#ffb3b3", command=lambda res=r: self.cancel_reservation(res)).pack(side="right", padx=5)
                tk.Button(frame, text="이동", bg="#b3d9ff", command=lambda res=r: self.move_reservation_screen(res)).pack(side="right", padx=5)
                tk.Button(frame, text="체크인", bg="#c2f0c2", command=lambda res=r: self.check_in(res)).pack(side="right", padx=5)

        tk.Button(self, text="처음으로", command=self.show_date_screen).pack(pady=20)

    def cancel_reservation(self, reservation):
        if messagebox.askyesno("예약 취소", "정말 예약을 취소하시겠습니까?"):
            reservations = load_study_reservations()
            updated_reservations = [
                r for r in reservations if not (
                    str(r["leader"]) == str(reservation["leader"]) and 
                    r["date"] == reservation["date"] and 
                    int(r["room_id"]) == int(reservation["room_id"]) and 
                    r["time_slot"] == reservation["time_slot"]
                )
            ]
            save_study_reservations(updated_reservations)
            messagebox.showinfo("취소 완료", "예약이 취소되었습니다.")
            self.show_my_reservation_screen()

    def check_in(self, reservation):
        if reservation.get("checked_in"):
            messagebox.showinfo("체크인", "이미 체크인 되었습니다.")
            return
        
        room = ROOMS[int(reservation["room_id"])]
        code = simpledialog.askstring("스터디룸 인증", f"[{room['name']}] 문 및 벽면에 부착된 인증 코드를 입력하세요.")
        if code and code.strip().upper() == room['checkin_code'].upper():
            reservations = load_study_reservations()
            for r in reservations:
                if (str(r["leader"]) == str(reservation["leader"]) and r["date"] == reservation["date"] and 
                    int(r["room_id"]) == int(reservation["room_id"]) and r["time_slot"] == reservation["time_slot"]):
                    r["checked_in"] = True
                    break
            save_study_reservations(reservations)
            messagebox.showinfo("성공", "체크인이 완료되었습니다.")
            self.show_my_reservation_screen()
        else:
            if code is not None:
                messagebox.showerror("실패", "코드가 일치하지 않습니다. 벽면에 부착된 코드를 확인해 주세요.")

    def move_reservation_screen(self, reservation):
        self.clear_screen()
        tk.Label(self, text="자리 이동 공간 선택", font=("맑은 고딕", 20, "bold")).pack(pady=20)

        grid = tk.Frame(self)
        grid.pack(pady=10)

        for room_id, room in ROOMS.items():
            tk.Button(grid, text=f"{room['name']}", width=15, height=2, bg="#d9eaff",
                      command=lambda r=room_id: self.move_time_screen(reservation, r)).grid(row=(room_id-1)//4, column=(room_id-1)%4, padx=5, pady=5)

        tk.Button(self, text="취소", command=self.show_my_reservation_screen).pack(pady=15)

    def move_time_screen(self, reservation, new_room_id):
        self.clear_screen()
        room = ROOMS[new_room_id]
        tk.Label(self, text=f"{room['name']} 이동 시간 선택", font=("맑은 고딕", 16, "bold")).pack(pady=15)

        time_frame = tk.Frame(self)
        time_frame.pack(pady=15)

        for index, slot in enumerate(TIME_SLOTS):
            if self.is_reserved(reservation["date"], new_room_id, slot):
                state, color = "disabled", "#ff9fbd"
            else:
                state, color = "normal", "#9be79b"

            tk.Button(time_frame, text=slot, width=13, bg=color, state=state,
                      command=lambda s=slot: self.execute_move(reservation, new_room_id, s)).grid(row=index//4, column=index%4, padx=5, pady=5)

        tk.Button(self, text="뒤로", command=lambda: self.move_reservation_screen(reservation)).pack(pady=10)

    def execute_move(self, reservation, new_room_id, new_time_slot):
        room = ROOMS[new_room_id]
        if reservation["people_count"] < room["min_people"] or reservation["people_count"] > room["capacity"]:
            messagebox.showerror("이동 불가", "해당 방의 인원 제한에 맞지 않습니다.")
            return
        
        reservations = load_study_reservations()
        for r in reservations:
            if (str(r["leader"]) == str(reservation["leader"]) and r["date"] == reservation["date"] and 
                int(r["room_id"]) == int(reservation["room_id"]) and r["time_slot"] == reservation["time_slot"]):
                r["room_id"] = int(new_room_id)
                r["time_slot"] = new_time_slot
                break
        save_study_reservations(reservations)
        
        messagebox.showinfo("완료", "예약 공간이 성공적으로 변경되었습니다.")
        self.show_my_reservation_screen()