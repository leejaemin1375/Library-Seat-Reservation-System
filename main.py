import tkinter as tk
from tkinter import messagebox, simpledialog
from datetime import datetime, timedelta
import json
import os

from login_2 import LoginPage
from reading_room import ReadingRoomPage, load_reading_rooms, save_reading_rooms, get_rooms_config
from study_room import StudyRoomPage, load_study_reservations, save_study_reservations, ROOMS as SR_ROOMS

PENALTY_FILE = "penalties.json"

def load_penalties():
    if os.path.exists(PENALTY_FILE):
        with open(PENALTY_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_penalties(data):
    with open(PENALTY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def add_penalty(student_id):
    """패널티를 1회 부여하고, 3회 누적 시 3일 정지 시간을 설정합니다."""
    penalties = load_penalties()
    if student_id not in penalties:
        penalties[student_id] = {"count": 0, "ban_until": None}
    
    penalties[student_id]["count"] += 1
    
    if penalties[student_id]["count"] >= 3:
        ban_expiry = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d %H:%M")
        penalties[student_id]["ban_until"] = ban_expiry
        
    save_penalties(penalties)
    return penalties[student_id]

def is_user_banned(student_id):
    """사용자가 패널티로 인해 예약 불가 상태인지 확인합니다."""
    penalties = load_penalties()
    if student_id in penalties:
        info = penalties[student_id]
        if info["count"] >= 3 and info["ban_until"]:
            ban_dt = datetime.strptime(info["ban_until"], "%Y-%m-%d %H:%M")
            if datetime.now() < ban_dt:
                return True, info["ban_until"]
            else:
                # 3일이 지나면 패널티 리셋
                penalties[student_id] = {"count": 0, "ban_until": None}
                save_penalties(penalties)
    return False, None


class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("도서관 좌석 및 스터디룸 예약 시스템")
        self.geometry("500x600")
        self.resizable(False, False)

        self.current_user = None
        self.current_frame = None

        self.show_login_page()
        self.auto_cancel_no_show()

    def clear_frame(self):
        if self.current_frame is not None:
            self.current_frame.destroy()

    def show_login_page(self):
        self.clear_frame()
        self.geometry("400x500")
        self.current_frame = LoginPage(self, on_login_success=self.on_login_success)
        self.current_frame.pack(fill="both", expand=True)

    def on_login_success(self, student_id):
        self.current_user = student_id
        self.show_mypage()

    def show_mypage(self):
        self.clear_frame()
        self.geometry("540x720")
        self.resizable(False, False)

        self.current_frame = tk.Frame(self, padx=20, pady=20)
        self.current_frame.pack(fill="both", expand=True)

        header_frame = tk.Frame(self.current_frame)
        header_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(header_frame, text=f"{self.current_user}님, 환영합니다!", font=("맑은 고딕", 12, "bold")).pack(side="left")
        tk.Button(header_frame, text="로그아웃", bg="#757575", fg="white", font=("맑은 고딕", 9),
                  command=self.show_login_page).pack(side="right", padx=(5, 0))
        tk.Button(header_frame, text="회원탈퇴", bg="#d32f2f", fg="white", font=("맑은 고딕", 9),
                  command=self.delete_account).pack(side="right")

        # 패널티 실시간 대시보드 출력 상자
        p_data = load_penalties().get(self.current_user, {"count": 0, "ban_until": None})
        p_count = p_data["count"]
        p_ban = p_data["ban_until"]
        
        penalty_sub_frame = tk.Frame(self.current_frame, bg="#fff3cd", bd=1, relief="solid", padx=10, pady=5)
        penalty_sub_frame.pack(fill="x", pady=(0, 10))
        
        p_text = f"⚠️ 나의 누적 패널티: {p_count}회"
        if p_count >= 3:
            p_text += f" (🚨 3회 누적 정지: {p_ban}까지 예약/팀원 참여 불가)"
        tk.Label(penalty_sub_frame, text=p_text, font=("맑은 고딕", 9, "bold"), fg="#856404", bg="#fff3cd").pack(anchor="w")

        menu_frame = tk.LabelFrame(self.current_frame, text="서비스 바로가기", font=("맑은 고딕", 10, "bold"), padx=15, pady=15)
        menu_frame.pack(fill="x", pady=5)

        tk.Button(menu_frame, text="열람실 좌석 예약", font=("맑은 고딕", 11), bg="#2196F3", fg="white", height=2,
                  command=self.show_reading_room_page).pack(fill="x", pady=5)
        tk.Button(menu_frame, text="스터디룸 예약", font=("맑은 고딕", 11), bg="#4CAF50", fg="white", height=2,
                  command=self.show_study_room_page).pack(fill="x", pady=5)

        status_box = tk.LabelFrame(self.current_frame, text="📅 나의 실시간 예약 현황", font=("맑은 고딕", 10, "bold"), padx=15, pady=15)
        status_box.pack(fill="both", expand=True, pady=10)

        # 1. 개인 열람실 상태 확인
        rr_data = load_reading_rooms()
        rr_booked = None
        for room_name, seats_map in rr_data.items():
            for seat_num, s_info in seats_map.items():
                if s_info.get("user") == self.current_user:
                    if datetime.now() < datetime.strptime(s_info["end_time"], "%Y-%m-%d %H:%M"):
                        rr_booked = (room_name, seat_num, s_info["booked_at"], s_info["end_time"], s_info.get("checked_in", False))
                        break

        tk.Label(status_box, text="■ 개인 열람실 현황", font=("맑은 고딕", 10, "bold"), fg="#4CAF50").pack(anchor="w", pady=2)
        if rr_booked:
            room_n, seat_n, booked_at, end_t, is_ci = rr_booked
            rr_frame = tk.Frame(status_box, bg="#f9f9f9", bd=1, relief="groove", padx=10, pady=8)
            rr_frame.pack(fill="x", pady=5)
            info_frame = tk.Frame(rr_frame, bg="#f9f9f9")
            info_frame.pack(side="left", fill="both", expand=True)
            
            status_txt = " [착석확인 완료]" if is_ci else " [미인증! 예약후 10분 내 인증 필수]"
            tk.Label(info_frame, text=f"위치: {room_n} [{seat_n}번]{status_txt}", 
                     font=("맑은 고딕", 9, "bold"), fg="#333" if is_ci else "#e91e63", bg="#f9f9f9", anchor="w").pack(fill="x", pady=1)
            tk.Label(info_frame, text=f"▶ 예약 시점: {booked_at}", font=("맑은 고딕", 9), fg="#555", bg="#f9f9f9", anchor="w").pack(fill="x", pady=1)
            tk.Label(info_frame, text=f"▶ 예약 종료: {end_t}", font=("맑은 고딕", 9), fg="#555", bg="#f9f9f9", anchor="w").pack(fill="x", pady=1)
            
            btn_frame = tk.Frame(rr_frame, bg="#f9f9f9")
            btn_frame.pack(side="right", fill="y", padx=(5, 0))
            
            tk.Button(btn_frame, text="반납", bg="#f44336", fg="white", font=("맑은 고딕", 9), width=8,
                      command=lambda: self.cancel_reading_room(room_n, seat_n)).pack(side="bottom", pady=2)
            
            if not is_ci:
                # 예약후 10분 이내에만 코드 입력 버튼 활성화
                b_dt = datetime.strptime(booked_at, "%Y-%m-%d %H:%M")
                if datetime.now() <= (b_dt + timedelta(minutes=10)):
                    tk.Button(btn_frame, text="코드 입력", bg="#e91e63", fg="white", font=("맑은 고딕", 9, "bold"), width=8,
                              command=lambda: self.checkin_reading_room(room_n, seat_n)).pack(side="bottom", pady=2)
        else:
            tk.Label(status_box, text="예약된 열람실 좌석이 없습니다.", font=("맑은 고딕", 9), fg="gray").pack(anchor="w", padx=10, pady=5)

        # 스터디룸 현황 파싱
        tk.Label(status_box, text="■ 스터디룸 현황", font=("맑은 고딕", 10, "bold"), fg="#2196F3").pack(anchor="w", pady=(10, 2))
        current_sr_list = load_study_reservations()
        sr_booked = [res for res in current_sr_list if str(res["leader"]) == str(self.current_user) or str(self.current_user) in [str(m) for m in res["members"]]]

        if sr_booked:
            sr_container = tk.Frame(status_box)
            sr_container.pack(fill="both", expand=True)
            for res in sr_booked:
                sr_frame = tk.Frame(sr_container, bg="#f9f9f9", bd=1, relief="groove", padx=10, pady=6)
                sr_frame.pack(fill="x", pady=3)
                sr_info_frame = tk.Frame(sr_frame, bg="#f9f9f9")
                sr_info_frame.pack(side="left", fill="both", expand=True)

                room_info = SR_ROOMS.get(int(res["room_id"]))
                room_name = room_info["name"] if room_info else f"알 수 없는 공간(ID: {res['room_id']})"
                ci_status = " [입실완료]" if res.get("checked_in", False) else " [미입실]"
                is_leader = str(res["leader"]) == str(self.current_user)
                role_txt = "[방장]" if is_leader else f"[팀원]"
                
                tk.Label(sr_info_frame, text=f"{room_name}{ci_status} ({role_txt})", font=("맑은 고딕", 9, "bold"), bg="#f9f9f9", anchor="w").pack(fill="x")
                tk.Label(sr_info_frame, text=f"▶ 예약 일시: {res['date']} ({res['time_slot']})", font=("맑은 고딕", 9), fg="#555", bg="#f9f9f9", anchor="w").pack(fill="x")
                
                sr_btn_frame = tk.Frame(sr_frame, bg="#f9f9f9")
                sr_btn_frame.pack(side="right", fill="y")
                
                if is_leader:
                    tk.Button(sr_btn_frame, text="취소", bg="#f44336", fg="white", font=("맑은 고딕", 8), width=8,
                              command=lambda r=res: self.cancel_study_room(r)).pack(side="bottom", pady=1)
                    
                    if not res.get("checked_in", False):
                        start_hour = int(res["time_slot"].split("-")[0].split(":")[0])
                        start_dt = datetime.strptime(f"{res['date']} {start_hour:02d}:00", "%Y-%m-%d %H:%M")
                        if start_dt <= datetime.now() <= (start_dt + timedelta(minutes=10)):
                            tk.Button(sr_btn_frame, text="코드 입력", bg="#e91e63", fg="white", font=("맑은 고딕", 8, "bold"), width=8,
                                      command=lambda r=res: self.checkin_study_room(r)).pack(side="bottom", pady=1)
                else:
                    tk.Label(sr_btn_frame, text="취소 권한 없음", font=("맑은 고딕", 8), fg="gray", bg="#f9f9f9").pack(side="bottom", pady=5)
        else:
            tk.Label(status_box, text="예약된 스터디룸 내역이 없습니다.", font=("맑은 고딕", 9), fg="gray").pack(anchor="w", padx=10, pady=5)

    def show_reading_room_page(self):
        banned, until = is_user_banned(self.current_user)
        if banned:
            messagebox.showerror("예약 제한", f"패널티 3회 누적으로 인해 예약을 할 수 없습니다.\n제한 해제 일시: {until}")
            return
        self.clear_frame()
        self.geometry("800x650")
        self.current_frame = ReadingRoomPage(self, self.current_user, on_back=self.show_mypage)
        self.current_frame.pack(fill="both", expand=True)

    def show_study_room_page(self):
        banned, until = is_user_banned(self.current_user)
        if banned:
            messagebox.showerror("예약 제한", f"패널티 3회 누적으로 인해 예약을 할 수 없습니다.\n제한 해제 일시: {until}")
            return
        self.clear_frame()
        self.geometry("700x600")
        self.current_frame = StudyRoomPage(self, self.current_user, on_back=self.show_mypage)
        self.current_frame.pack(fill="both", expand=True)

    def checkin_reading_room(self, room_name, seat_num):
        rr_data = load_reading_rooms()
        if room_name not in rr_data or str(seat_num) not in rr_data[room_name]:
            messagebox.showerror("오류", "예약 정보가 유효하지 않습니다.")
            return
            
        s_info = rr_data[room_name][str(seat_num)]
        booked_dt = datetime.strptime(s_info["booked_at"], "%Y-%m-%d %H:%M")
        
        if datetime.now() > (booked_dt + timedelta(minutes=10)):
            messagebox.showerror("인증 실패", "인증 가능 시간(예약 후 10분)이 초과되어 인증할 수 없습니다.")
            return

        try:
            rooms_config = get_rooms_config()
            correct_code = rooms_config[room_name]["seats"][str(seat_num)]
        except Exception:
            auth_code_map = {"열람실1": "R1", "열람실2": "R2", "열람실3": "R3"}
            correct_code = auth_code_map.get(room_name, "1234")

        code = simpledialog.askstring("좌석 인증", f"[{room_name} {seat_num}번] 책상 표면에 부착된 인증 코드를 입력하세요.")
        if code and code.strip().upper() == correct_code.upper():
            rr_data = load_reading_rooms()
            if room_name in rr_data and str(seat_num) in rr_data[room_name]:
                rr_data[room_name][str(seat_num)]["checked_in"] = True
                save_reading_rooms(rr_data)
                messagebox.showinfo("인증 성공", f"[{room_name}] {seat_num}번 좌석 착석 인증이 완료되었습니다.")
                self.show_mypage()
        elif code is not None:
            messagebox.showerror("인증 실패", "코드가 올바르지 않습니다.")

    def cancel_reading_room(self, room_name, seat_num):
        if messagebox.askyesno("좌석 반납", "선택하신 좌석을 반납하시겠습니까?"):
            rr_data = load_reading_rooms()
            if room_name in rr_data and str(seat_num) in rr_data[room_name]:
                del rr_data[room_name][str(seat_num)]
                save_reading_rooms(rr_data)
                messagebox.showinfo("반납 완료", "좌석이 정상적으로 반납되었습니다.")
                self.show_mypage()

    def checkin_study_room(self, reservation):
        room_id = int(reservation["room_id"])
        room_info = SR_ROOMS.get(room_id)
        if not room_info: return

        start_hour = int(reservation["time_slot"].split("-")[0].split(":")[0])
        start_dt = datetime.strptime(f"{reservation['date']} {start_hour:02d}:00", "%Y-%m-%d %H:%M")
        
        if datetime.now() < start_dt or datetime.now() > (start_dt + timedelta(minutes=10)):
            messagebox.showerror("인증 실패", "스터디룸 인증은 입실 시작 시간 후 10분까지만 가능합니다.")
            return

        code = simpledialog.askstring("스터디룸 인증", f"[{room_info['name']}] 문 또는 벽면에 부착된 인증 코드를 입력하세요.")
        if code and code.strip().upper() == room_info["checkin_code"].upper():
            sr_data = load_study_reservations()
            for r in sr_data:
                if (str(r["leader"]) == str(reservation["leader"]) and r["date"] == reservation["date"] and 
                    int(r["room_id"]) == int(reservation["room_id"]) and r["time_slot"] == reservation["time_slot"]):
                    r["checked_in"] = True
                    break
            save_study_reservations(sr_data)
            messagebox.showinfo("인증 완료", "스터디룸 체크인이 정상 승인되었습니다.")
            self.show_mypage()
        elif code is not None:
            messagebox.showerror("인증 실패", "코드가 올바르지 않습니다.")

    def cancel_study_room(self, reservation):
        if messagebox.askyesno("예약 취소", "스터디룸 예약을 취소하시겠습니까?"):
            sr_data = load_study_reservations()
            updated = [
                r for r in sr_data if not (
                    str(r["leader"]) == str(reservation["leader"]) and 
                    r["date"] == reservation["date"] and 
                    int(r["room_id"]) == int(reservation["room_id"]) and 
                    r["time_slot"] == reservation["time_slot"]
                )
            ]
            save_study_reservations(updated)
            messagebox.showinfo("취소 성공", "예약이 정상적으로 취소되었습니다.")
            self.show_mypage()
    
    def delete_account(self):
        """회원 탈퇴 기능을 수행합니다. 조건에 따른 제약 및 연동 처리를 포함합니다."""
        if not messagebox.askyesno("회원 탈퇴", "정말 탈퇴하시겠습니까?\n탈퇴 후에는 계정을 복구할 수 없습니다."):
            return

        # 스터디룸 예약 확인 (방장 또는 팀원으로 참여한 실시간 예약이 있는지 검사)
        current_sr_list = load_study_reservations()
        sr_booked = [
            res for res in current_sr_list 
            if str(res["leader"]) == str(self.current_user) or str(self.current_user) in [str(m) for m in res["members"]]
        ]
        
        if sr_booked:
            messagebox.showerror(
                "탈퇴 불가", 
                "현재 예약된 스터디룸 내역(방장 혹은 팀원)이 존재하여 탈퇴할 수 없습니다.\n"
                "모든 스터디룸 이용이 끝나거나 예약이 취소된 후 다시 시도해주세요."
            )
            return

        # 열람실 예약 확인 및 즉시 반납 처리
        rr_data = load_reading_rooms()
        rr_changed = False
        
        for room_name, seats_map in list(rr_data.items()):
            for seat_num, s_info in list(seats_map.items()):
                if s_info.get("user") == self.current_user:
                    # 현재 시간 기준으로 종료되지 않은 유효한 예약인 경우 즉시 반납
                    if datetime.now() < datetime.strptime(s_info["end_time"], "%Y-%m-%d %H:%M"):
                        del rr_data[room_name][seat_num]
                        rr_changed = True
                        break
        
        if rr_changed:
            save_reading_rooms(rr_data)

        # 패널티 정보 삭제 (선택 사항: 탈퇴하는 회원의 패널티 데이터 정리)
        from main import load_penalties, save_penalties
        penalties = load_penalties()
        if self.current_user in penalties:
            del penalties[self.current_user]
            save_penalties(penalties)

        # users.json에서 사용자 계정 정보 삭제
        from login_2 import load_users, save_users
        users = load_users()
        if self.current_user in users:
            del users[self.current_user]
            save_users(users)
            
            messagebox.showinfo("탈퇴 완료", "회원 탈퇴가 정상적으로 처리되었습니다.\n로그인 화면으로 이동합니다.")
            self.current_user = None
            self.show_login_page()
        else:
            messagebox.showerror("오류", "사용자 정보를 찾을 수 없습니다.")

    def auto_cancel_no_show(self):
        """실시간 노쇼를 감지하여 10분이 지나면 예약 취소 및 자동 패널티를 부여하는 핵심 백그라운드 엔진"""
        now = datetime.now()
        rr_changed = False
        sr_changed = False

        # 열람실 감시 및 패널티 부과
        try:
            rr_data = load_reading_rooms()
            for room_name, seats_map in list(rr_data.items()):
                for seat_num, s_info in list(seats_map.items()):
                    booked_dt = datetime.strptime(s_info["booked_at"], "%Y-%m-%d %H:%M")
                    is_ci = s_info.get("checked_in", False)
                    
                    if not is_ci and now > (booked_dt + timedelta(minutes=10)):
                        user_to_penalty = s_info["user"]
                        del rr_data[room_name][seat_num]
                        rr_changed = True
                        add_penalty(user_to_penalty)
                    elif now > datetime.strptime(s_info["end_time"], "%Y-%m-%d %H:%M"):
                        del rr_data[room_name][seat_num]
                        rr_changed = True
            if rr_changed:
                save_reading_rooms(rr_data)
        except Exception:
            pass

        # 스터디룸 감시 및 패널티 부과
        try:
            sr_data = load_study_reservations()
            updated_sr = []
            for res in sr_data:
                try:
                    start_hour = int(res["time_slot"].split("-")[0].split(":")[0])
                    start_dt = datetime.strptime(f"{res['date']} {start_hour:02d}:00", "%Y-%m-%d %H:%M")
                    
                    if now > (start_dt + timedelta(minutes=10)) and not res.get("checked_in", False):
                        sr_changed = True
                        add_penalty(res["leader"])
                        continue
                except:
                    pass
                updated_sr.append(res)

            if sr_changed:
                save_study_reservations(updated_sr)
        except Exception:
            pass

        if (rr_changed or sr_changed) and hasattr(self, 'current_frame') and type(self.current_frame) is tk.Frame:
            self.show_mypage()

        self.after(1000, self.auto_cancel_no_show)

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()