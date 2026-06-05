import tkinter as tk
from tkinter import messagebox
from login_2 import LoginPage, load_users
from reading_room import ReadingRoomPage, load_rooms, save_rooms
from study_room import StudyRoomPage, RESERVATIONS

class MainApplication(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("대학 도서관 통합 예약 시스템")
        self.geometry("600x600")
        self.resizable(False, False)
        
        self.current_user = None
        self.current_frame = None
        
        # 최초 화면: 로그인 페이지
        self.show_login_page()

    def clear_frame(self):
        if self.current_frame is not None:
            self.current_frame.destroy()

    def show_login_page(self):
        self.clear_frame()
        self.geometry("320x240")
        self.resizable(False, False)
        self.current_frame = LoginPage(self, on_login_success=self.on_login_success)
        self.current_frame.pack(fill="both", expand=True)

    def on_login_success(self, username):
        self.current_user = username
        self.show_mypage()

    def show_mypage(self):
        """로그인 후 첫 진입 화면을 통합 마이페이지로 설정"""
        self.clear_frame()
        self.geometry("600x650")
        self.resizable(False, False)
        
        self.current_frame = tk.Frame(self)
        self.current_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # 상단 타이틀 및 사용자 정보
        tk.Label(self.current_frame, text="🏛️ 도서관 통합 마이페이지", font=("맑은 고딕", 18, "bold")).pack(pady=10)
        tk.Label(self.current_frame, text=f"반갑습니다, {self.current_user}님", font=("맑은 고딕", 11, "italic"), fg="#333").pack(pady=5)

        # ====== [통합 예약 관리 섹션] ======
        nav_box = tk.LabelFrame(self.current_frame, text="새로운 예약하기", font=("맑은 고딕", 10, "bold"), padx=10, pady=10)
        nav_box.pack(fill="x", pady=10)
        
        tk.Button(nav_box, text="개인 열람실 예약", bg="#4CAF50", fg="white", font=("맑은 고딕", 10, "bold"),
                  command=self.show_reading_room).pack(side="left", expand=True, fill="x", padx=5)
        tk.Button(nav_box, text="그룹 스터디룸 예약", bg="#2196F3", fg="white", font=("맑은 고딕", 10, "bold"),
                  command=self.show_study_room).pack(side="left", expand=True, fill="x", padx=5)

        # ====== [실시간 예약 현황 통합 조회] ======
        status_box = tk.LabelFrame(self.current_frame, text="나의 실시간 예약 현황", font=("맑은 고딕", 10, "bold"), padx=10, pady=10)
        status_box.pack(fill="both", expand=True, pady=10)

        # 1. 개인 열람실 현황 추출
        rooms_data = load_rooms()
        rr_booked = None
        for r_name, r_info in rooms_data.items():
            for s_key, s_info in r_info["reservations"].items():
                if s_info.get("user") == self.current_user:
                    rr_booked = (r_name, s_key, s_info["end_time"])
                    break

        tk.Label(status_box, text="■ 개인 열람실", font=("맑은 고딕", 10, "bold"), fg="#4CAF50").pack(anchor="w", pady=2)
        if rr_booked:
            rr_frame = tk.Frame(status_box, bg="#f9f9f9", bd=1, relief="groove")
            rr_frame.pack(fill="x", pady=5, ipady=4)
            tk.Label(rr_frame, text=f"위치: {rr_booked[0]} [{rr_booked[1]}번 좌석]\n이용 종료 시간: {rr_booked[2]}", 
                     font=("맑은 고딕", 9), justify="left", bg="#f9f9f9").pack(side="left", padx=10)
            tk.Button(rr_frame, text="반납/취소", bg="#f44336", fg="white", font=("맑은 고딕", 9),
                      command=lambda: self.cancel_reading_room(rr_booked[0], rr_booked[1])).pack(side="right", padx=10)
        else:
            tk.Label(status_box, text="예약된 열람실 좌석이 없습니다.", font=("맑은 고딕", 9), fg="gray").pack(anchor="w", padx=10, pady=5)

        tk.Canvas(status_box, height=1, bg="#ddd", bd=0, highlightthickness=0).pack(fill="x", pady=10)

        # 2. 그룹 스터디룸 현황 추출 (방장 및 팀원 명단 포함자 모두 조회)
        tk.Label(status_box, text="■ 그룹 스터디룸", font=("맑은 고딕", 10, "bold"), fg="#2196F3").pack(anchor="w", pady=2)
        sr_booked = [r for r in RESERVATIONS if r["leader"] == self.current_user or self.current_user in r["members"]]
        
        if sr_booked:
            from study_room import ROOMS as SR_ROOMS
            for res in sr_booked:
                sr_frame = tk.Frame(status_box, bg="#f9f9f9", bd=1, relief="groove")
                sr_frame.pack(fill="x", pady=5, ipady=4)
                
                room_name = SR_ROOMS[res["room_id"]]["name"]
                status_txt = "체크인 완료" if res.get("checked_in") else "체크인 전"
                
                role_txt = "[방장]" if res["leader"] == self.current_user else f"[팀원] 방장:{res['leader']}"
                info_txt = f"날짜: {res['date']} | 공간: {room_name} {role_txt}\n시간: {res['time_slot']} ({status_txt})"
                
                tk.Label(sr_frame, text=info_txt, font=("맑은 고딕", 9), justify="left", bg="#f9f9f9").pack(side="left", padx=10)
                tk.Button(sr_frame, text="취소", bg="#f44336", fg="white", font=("맑은 고딕", 9),
                          command=lambda r=res: self.cancel_study_room(r)).pack(side="right", padx=10)
        else:
            tk.Label(status_box, text="예약된 그룹 스터디룸이 없습니다.", font=("맑은 고딕", 9), fg="gray").pack(anchor="w", padx=10, pady=5)

        # 하단 로그아웃
        tk.Button(self.current_frame, text="로그아웃", font=("맑은 고딕", 9), width=10,
                  command=self.show_login_page).pack(side="bottom", pady=10)

    def cancel_reading_room(self, room_name, seat_key):
        if messagebox.askyesno("예약 취소", "열람실 좌석 예약을 취소하시겠습니까?"):
            rooms_data = load_rooms()
            if room_name in rooms_data and seat_key in rooms_data[room_name]["reservations"]:
                del rooms_data[room_name]["reservations"][seat_key]
                save_rooms(rooms_data)
                messagebox.showinfo("취소 완료", "열람실 좌석이 반납되었습니다.")
                self.show_mypage()

    def cancel_study_room(self, reservation):
        """[개선] 권한 검증 기능: 방장이 아닌 팀원이 취소를 시도할 경우 경고창 차단"""
        if reservation["leader"] != self.current_user:
            messagebox.showerror("권한 오류", "스터디룸 예약 취소 권한이 없습니다.\n(예약 취소는 방장만 가능합니다.)")
            return

        if messagebox.askyesno("예약 취소", "스터디룸 예약을 취소하시겠습니까?\n취소 시 전체 연속 예약 및 팀원 명단이 함께 삭제됩니다."):
            if reservation in RESERVATIONS:
                RESERVATIONS.remove(reservation)
                messagebox.showinfo("취소 완료", "스터디룸 예약이 취소되었습니다.")
                self.show_mypage()

    def show_reading_room(self):
        self.clear_frame()
        self.geometry("400x600")
        self.resizable(False, False)
        self.current_frame = ReadingRoomPage(self, user=self.current_user, on_back=lambda u: self.show_mypage())
        self.current_frame.pack(fill="both", expand=True)

    def show_study_room(self):
        self.clear_frame()
        self.geometry("900x700")
        self.resizable(False, False)
        self.current_frame = StudyRoomPage(self, user=self.current_user, on_back=self.show_mypage)
        self.current_frame.pack(fill="both", expand=True)

if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()