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

class StudyRoomPage(tk.Frame):
    def __init__(self, master, user, on_back):
        super().__init__(master)
        self.user = user
        self.on_back = on_back
        self.selected_slots = [] # ★ 사용자가 마우스로 클릭클릭한 임시 선택 시간대 리스트
        self.show_date_screen()

    def clear_screen(self):
        for widget in self.winfo_children():
            widget.destroy()

    def is_reserved(self, date, room_id, time_slot):
        reservations = load_study_reservations()
        return any(r["date"] == date and int(r["room_id"]) == int(room_id) and r["time_slot"] == time_slot for r in reservations)

    def is_past_time(self, date, time_slot):
        try:
            selected_date = datetime.strptime(date, "%Y-%m-%d").date()
            now = datetime.now()
            
            if selected_date < now.date():
                return True
            if selected_date > now.date():
                return False

            start_hour = int(time_slot.split("-")[0].split(":")[0])
            start_time = datetime(now.year, now.month, now.day, start_hour, 0)
            
            return now >= start_time
        except Exception:
            return True

    def show_date_screen(self):
        self.clear_screen()
        self.selected_slots = [] # 화면 초기화 시 선택 정보 초기화
        tk.Label(self, text="스터디룸 예약 시스템", font=("맑은 고딕", 22, "bold")).pack(pady=25)
        tk.Label(self, text=f"현재 로그인 사용자: {self.user}", font=("맑은 고딕", 12)).pack(pady=5)
        tk.Label(self, text="예약할 날짜를 선택하세요.", font=("맑은 고딕", 15)).pack(pady=20)
        
        tk.Button(self, text="내 예약 조회 / 취소", command=self.show_my_reservation_screen).pack(pady=15)
        
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
        self.selected_slots = [] # 화면 초기화 시 선택 정보 초기화
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
        tk.Button(bottom, text="메인메뉴로", command=self.on_back).pack(side="left", padx=10)

    def show_time_screen(self, date, room_id):
        self.clear_screen()
        room = ROOMS[room_id]

        tk.Label(self, text=f"{room['name']} 예약 가능 시간", font=("맑은 고딕", 20, "bold")).pack(pady=15)
        tk.Label(self, text=f"날짜: {date}  |  정원: {room['capacity']}명  |  최소인원: {room['min_people']}명", font=("맑은 고딕", 11)).pack(pady=5)
        
        # 안내 문구 상단에 노출
        tk.Label(self, text="※ 원하는 시간대 버튼을 클릭클릭하여 연속 최대 3시간까지 지정한 후 하단 [예약하기] 버튼을 누르세요.", 
                 font=("맑은 고딕", 10, "bold"), fg="#E53935").pack(pady=3)

        legend = tk.Frame(self)
        legend.pack(pady=5)
        tk.Label(legend, text="가능", bg="#9be79b", width=8).pack(side="left", padx=5)
        tk.Label(legend, text="선택중", bg="#ffe680", width=8).pack(side="left", padx=5)
        tk.Label(legend, text="사용중", bg="#ff9fbd", width=8).pack(side="left", padx=5)

        time_frame = tk.Frame(self)
        time_frame.pack(pady=15)

        for index, slot in enumerate(TIME_SLOTS):
            is_chosen = slot in self.selected_slots

            if self.is_past_time(date, room_id, slot) if 'room_id' in self.is_past_time.__code__.co_varnames else self.is_past_time(date, slot):
                text, color, state = f"{slot}\n마감", "#d3d3d3", "disabled"
            elif self.is_reserved(date, room_id, slot):
                text, color, state = f"{slot}\n사용중", "#ff9fbd", "disabled"
            elif is_chosen:
                text, color, state = f"{slot}\n선택중", "#ffe680", "normal"
            else:
                text, color, state = f"{slot}\n가능", "#9be79b", "normal"

            btn = tk.Button(time_frame, text=text, width=13, height=2, bg=color, state=state)
            btn.config(command=lambda s=slot, b=btn: self.reserve_room(date, room_id, s, b))
            btn.grid(row=index // 4, column=index % 4, padx=6, pady=6)

        bottom = tk.Frame(self)
        bottom.pack(pady=10)
        
        # ★ 하단에 일괄 처리를 수행할 예약 확정 실행 버튼 생성
        tk.Button(bottom, text="✅ 선택한 시간 최종 예약하기", font=("맑은 고딕", 11, "bold"), bg="#4CAF50", fg="white", padx=12,
                  command=lambda: self.process_final_reservation(date, room_id)).pack(side="left", padx=10)

        tk.Button(bottom, text="공간 다시 선택", command=lambda: self.show_room_screen(date)).pack(side="left", padx=10)
        tk.Button(bottom, text="날짜 다시 선택", command=self.show_date_screen).pack(side="left", padx=10)
        tk.Button(bottom, text="메인메뉴로", command=self.on_back).pack(side="left", padx=10)

    def reserve_room(self, date, room_id, time_slot, button):
        """시간 슬롯 버튼을 눌렀을 때 팝업창을 생략하고 즉시 리스트에 주황색('선택중')으로 담아내는 함수"""
        if time_slot in self.selected_slots:
            # 이미 선택된 목록을 다시 누르면 -> 토글식 선택 해제 처리
            self.selected_slots.remove(time_slot)
            button.config(bg="#9be79b", text=f"{time_slot}\n가능")
        else:
            # 1. 최대 연속 3시간 제약 규정 예외처리 검사
            if len(self.selected_slots) >= 3:
                messagebox.showwarning("선택 제한", "스터디룸은 1회 예약 시 최대 연속 3시간까지만 선택하실 수 있습니다.")
                return
                
            # 2. 중간에 빈 시간이 끊어지지 않도록 가로채기 검증
            if self.selected_slots:
                existing_hours = sorted([int(s.split(":")[0]) for s in self.selected_slots])
                current_hour = int(time_slot.split(":")[0])
                
                if current_hour != existing_hours[0] - 1 and current_hour != existing_hours[-1] + 1:
                    messagebox.showwarning("선택 오류", "예약 시간은 중간에 공백 없이 연속된 시간대로만 선택하셔야 합니다.")
                    return

            # 임시 배열 저장 및 UI 피드백 반영
            self.selected_slots.append(time_slot)
            button.config(bg="#ffe680", text=f"{time_slot}\n선택중")

    def process_final_reservation(self, date, room_id):
        """[선택한 시간 최종 예약하기] 버튼을 누를 시 실행되어 팀원을 입력받고 일괄 기록하는 동기화 메인 로직"""
        if not self.selected_slots:
            messagebox.showwarning("선택 오류", "선택된 시간이 없습니다.\n원하는 시간 버튼을 먼저 한 개 이상 클릭해 주세요.")
            return

        # 당일 지난 타임 차단 예외처리
        now = datetime.now()
        current_date_str = now.strftime("%Y-%m-%d")
        if date == current_date_str:
            try:
                sorted_slots = sorted(self.selected_slots)
                start_time_str = sorted_slots[0].split("-")[0].strip()
                start_hour, start_minute = map(int, start_time_str.split(":"))
                slot_start_datetime = now.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
                if now >= slot_start_datetime:
                    messagebox.showerror("예약 불가", "선택 항목 중 이미 시작되었거나 지나간 시간대가 포함되어 있어 처리가 불가능합니다.")
                    return
            except Exception as e:
                print(f"시간 동기화 파싱 오류: {e}")

        room = ROOMS[room_id]
        
        # 다중 클릭이 정상 완료된 뒤에 비로소 팀원 학번 입력 창 유도
        member_input = simpledialog.askstring("팀원 학번 입력", f"본인({self.user}) 외 팀원 학번을 쉼표(,)로 구분하여 입력하세요.")
        if member_input is None:
            return

        members = [m.strip() for m in member_input.split(",")] if member_input.strip() else []
        
        if str(self.user) in members:
            messagebox.showerror("입력 오류", "본인 학번은 자동으로 포함됩니다.")
            return

        # [팀원 가입 및 패널티 제재 상태 실시간 통합 교차 검증]
        from login_2 import load_users  
        from main import is_user_banned, load_penalties
        existing_users = load_users()   
        
        invalid_members = []
        banned_members = []
        
        for m in members:
            if m not in existing_users:
                invalid_members.append(m)
            else:
                banned, until = is_user_banned(m)
                if banned:
                    banned_members.append(f"{m}(~{until}까지 정지)")
                else:
                    p_info = load_penalties().get(m, {"count": 0})
                    if p_info["count"] >= 3:
                        banned_members.append(f"{m}(패널티 3회 누적인원)")
                
        if invalid_members:
            messagebox.showerror("예약 불가", f"등록되지 않은 사용자가 포함되어 있습니다.\n미가입 학번: {', '.join(invalid_members)}")
            return

        if banned_members:
            messagebox.showerror("팀원 참여 불가", f"패널티 제한 규정으로 인해 팀원으로 입실할 수 없는 학번이 포함되어 있습니다.\n\n대상자:\n{chr(10).join(banned_members)}")
            return

        total_people = len(members) + 1
        if total_people < room["min_people"] or total_people > room["capacity"]:
            messagebox.showerror("예약 불가", f"인원 조건 미달 또는 초과 (최소: {room['min_people']}, 최대: {room['capacity']})")
            return

        reservations = load_study_reservations()
        
        # 데이터 정합성 보장을 위한 선점 여부 파이널 더블 체크
        for slot in self.selected_slots:
            if self.is_reserved(date, room_id, slot):
                messagebox.showerror("예약 실패", f"처리 도중 {slot} 시간대가 이미 타인에게 먼저 선점되었습니다.")
                self.selected_slots = []
                self.show_time_screen(date, room_id)
                return

        # 선택했던 슬롯들을 하나씩 순회하며 배열에 모두 추가
        for slot in self.selected_slots:
            reservations.append({
                "leader": str(self.user), 
                "members": members, 
                "date": date, 
                "room_id": int(room_id), 
                "time_slot": slot, 
                "people_count": total_people, 
                "checked_in": False
            })
            
        save_study_reservations(reservations)
        
        messagebox.showinfo(
            "예약 완료", 
            f"선택하신 총 {len(self.selected_slots)}시간 연속 예약이 정상적으로 완료되었습니다.\n\n"
            "※ [노쇼 방지 필수 안내]\n"
            "매 예약 시작 시간 전후 10분 이내에 해당 스터디룸 벽면에 부착된 "
            "인증 코드를 마이페이지에서 반드시 등록해야 노쇼 패널티를 받지 않습니다."
        )
        
        # 내부 구조 바구니를 비워주고 화면 새로고침 단계를 진행합니다.
        self.selected_slots = []
        self.show_time_screen(date, room_id)
    
    def show_my_reservation_screen(self):
        self.clear_screen()
        tk.Label(self, text="내 예약 조회 / 취소", font=("맑은 고딕", 20, "bold")).pack(pady=20)

        reservations = load_study_reservations()
        my_res = [r for r in reservations if str(r["leader"]) == str(self.user) or str(self.user) in [str(m) for m in r["members"]]]

        if not my_res:
            tk.Label(self, text="현재 예약 내역이 없습니다.", font=("맑은 고딕", 13)).pack(pady=20)
        else:
            for r in my_res:
                room_info = ROOMS.get(int(r["room_id"]))
                room_name = room_info["name"] if room_info else f"알 수 없는 방(ID: {r['room_id']})"
                frame = tk.Frame(self, relief="solid", borderwidth=1)
                frame.pack(pady=5, padx=20, fill="x")

                status_txt = "체크인 완료" if r.get("checked_in") else "체크인 전"
                is_leader = str(r["leader"]) == str(self.user)
                role_txt = "[방장]" if is_leader else "[팀원]"
                
                text = f"[{role_txt}] 날짜: {r['date']} | 공간: {room_name} | 시간: {r['time_slot']}\n상태: {status_txt} | 인원: {r['people_count']}명"
                tk.Label(frame, text=text, font=("맑은 고딕", 10), justify="left").pack(side="left", padx=10, pady=5)
                
                if is_leader:
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