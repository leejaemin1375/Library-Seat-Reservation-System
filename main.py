import tkinter as tk
import tkinter.messagebox as msgbox
import json
import os
from datetime import datetime
from login_2 import LoginPage
# [수정] study_room에 존재하는 함수 및 변수명(RESERVATIONS)으로 올바르게 임포트합니다.
from reading_room import ReadingRoomPage, load_rooms as load_reading_rooms
from study_room import StudyRoomPage, RESERVATIONS

READING_ROOMS_FILE = "reading_rooms.json"
STUDY_ROOMS_FILE = "study_rooms.json"

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("대학 도서관 통합 예약 시스템")
        self.geometry("500x400")
        self.current_user = None
        self.current_frame = None
        self.show_login_page()

    def clear_frame(self):
        if self.current_frame:
            self.current_frame.destroy()

    def show_login_page(self):
        self.clear_frame()
        self.geometry("500x400")
        self.resizable(False, False)
        self.current_frame = LoginPage(self, on_login_success=self.on_login_success)
        self.current_frame.pack(fill="both", expand=True)

    def on_login_success(self, user_id):
        self.current_user = user_id
        self.show_mypage()

    def show_mypage(self):
        self.clear_frame()
        self.geometry("500x600")
        self.resizable(False, False)

        self.current_frame = tk.Frame(self, padx=20, pady=20)
        self.current_frame.pack(fill="both", expand=True)

        # 상단 환영 메시지 및 로그아웃
        header_frame = tk.Frame(self.current_frame)
        header_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(header_frame, text=f"{self.current_user}님, 환영합니다!", font=("맑은 고딕", 12, "bold")).pack(side="left")
        tk.Button(header_frame, text="로그아웃", bg="#757575", fg="white", font=("맑은 고딕", 9),
                  command=self.show_login_page).pack(side="right")

        # 메뉴 버튼 영역
        menu_frame = tk.LabelFrame(self.current_frame, text="서비스 바로가기", font=("맑은 고딕", 10, "bold"), padx=15, pady=15)
        menu_frame.pack(fill="x", pady=10)

        tk.Button(menu_frame, text="열람실 좌석 예약", font=("맑은 고딕", 11), bg="#2196F3", fg="white", height=2,
                  command=self.show_reading_room_page).pack(fill="x", pady=5)
        tk.Button(menu_frame, text="스터디룸 예약", font=("맑은 고딕", 11), bg="#4CAF50", fg="white", height=2,
                  command=self.show_study_room_page).pack(fill="x", pady=5)

        # 실시간 예약 현황 영역
        status_box = tk.LabelFrame(self.current_frame, text="📅 나의 실시간 예약 현황", font=("맑은 고딕", 10, "bold"), padx=15, pady=15)
        status_box.pack(fill="both", expand=True, pady=10)

        # 데이터 로드
        rr_data = load_reading_rooms()

        # 1. 개인 열람실 현황 추출 및 표시
        rr_booked = None
        for room_name, r_info in rr_data.items():
            for seat_num, s_info in r_info.get("reservations", {}).items():
                if s_info.get("user") == self.current_user:
                    if datetime.now() < datetime.strptime(s_info["end_time"], "%Y-%m-%d %H:%M"):
                        rr_booked = (room_name, seat_num, s_info["end_time"])
                        break

        tk.Label(status_box, text="■ 개인 열람실", font=("맑은 고딕", 10, "bold"), fg="#4CAF50").pack(anchor="w", pady=2)
        if rr_booked:
            rr_frame = tk.Frame(status_box, bg="#f9f9f9", bd=1, relief="groove")
            rr_frame.pack(fill="x", pady=5, ipady=4)
            tk.Label(rr_frame, text=f"위치: {rr_booked[0]} [{rr_booked[1]}번 좌석]\n이용 종료 시간: {rr_booked[2]}", 
                     font=("맑은 고딕", 9), justify="left", bg="#f9f9f9").pack(side="left", padx=10)
            
            tk.Button(rr_frame, text="반납/취소", bg="#f44336", fg="white", font=("맑은 고딕", 9),
                      command=lambda: self.cancel_reading_room(rr_booked[0], rr_booked[1])).pack(side="right", padx=10)
            
            tk.Button(rr_frame, text="좌석 이동", bg="#FF9800", fg="white", font=("맑은 고딕", 9),
                      command=lambda r_name=rr_booked[0]: self.show_reading_room_for_move(r_name)).pack(side="right", padx=5)
        else:
            tk.Label(status_box, text="예약된 열람실 좌석이 없습니다.", font=("맑은 고딕", 9), fg="gray").pack(anchor="w", padx=10, pady=5)

        # 2. 스터디룸 현황 추출 및 표시 (study_room.py의 리스트형 RESERVATIONS 구조 반영)
        tk.Label(status_box, text="■ 스터디룸", font=("맑은 고딕", 10, "bold"), fg="#2196F3").pack(anchor="w", pady=(10, 2))
        
        # 내가 방장이거나 팀원에 포함된 예약 목록 필터링
        sr_booked = [res for res in RESERVATIONS if res["leader"] == self.current_user or self.current_user in res["members"]]

        if sr_booked:
            # 방 이름 매핑을 위해 study_room의 ROOMS 구조 참조
            from study_room import ROOMS as SR_ROOMS
            
            sr_container = tk.Frame(status_box)
            sr_container.pack(fill="both", expand=True)
            
            for res in sr_booked:
                sr_frame = tk.Frame(sr_container, bg="#f9f9f9", bd=1, relief="groove")
                sr_frame.pack(fill="x", pady=2, ipady=2)
                
                room_name = SR_ROOMS[res["room_id"]]["name"]
                role_txt = "[방장]" if res["leader"] == self.current_user else f"[팀원] 방장:{res['leader']}"
                info_txt = f"{room_name} | {res['date']} {res['time_slot']} {role_txt}"
                
                tk.Label(sr_frame, text=info_txt, font=("맑은 고딕", 9), bg="#f9f9f9").pack(side="left", padx=10)
                tk.Button(sr_frame, text="취소", bg="#f44336", fg="white", font=("맑은 고딕", 8),
                          command=lambda r=res: self.cancel_study_room(r)).pack(side="right", padx=10)
        else:
            tk.Label(status_box, text="예약된 스터디룸 내역이 없습니다.", font=("맑은 고딕", 9), fg="gray").pack(anchor="w", padx=10, pady=5)

    def show_reading_room_page(self):
        self.clear_frame()
        self.geometry("700x700")
        self.resizable(False, False)
        self.current_frame = ReadingRoomPage(self, user=self.current_user, on_back=lambda u: self.show_mypage())
        self.current_frame.pack(fill="both", expand=True)

    def show_reading_room_for_move(self, room_name):
        self.clear_frame()
        self.geometry("700x700")
        self.resizable(False, False)
        self.current_frame = ReadingRoomPage(self, user=self.current_user, on_back=lambda u: self.show_mypage(), target_room=room_name)
        self.current_frame.pack(fill="both", expand=True)

    def show_study_room_page(self):
        self.clear_frame()
        self.geometry("900x700")
        self.resizable(False, False)
        self.current_frame = StudyRoomPage(self, user=self.current_user, on_back=self.show_mypage)
        self.current_frame.pack(fill="both", expand=True)

    def cancel_reading_room(self, room_name, seat_num):
        if msgbox.askyesno("확인", f"{room_name} [{seat_num}번 좌석]을 반납하시겠습니까?"):
            data = load_reading_rooms()
            if room_name in data and str(seat_num) in data[room_name]["reservations"]:
                del data[room_name]["reservations"][str(seat_num)]
                try:
                    with open(READING_ROOMS_FILE, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)
                    msgbox.showinfo("완료", "반납이 완료되었습니다.")
                except IOError:
                    msgbox.showerror("오류", "파일 저장 중 문제가 발생했습니다.")
            self.show_mypage()

    def cancel_study_room(self, reservation):
        if reservation["leader"] != self.current_user:
            msgbox.showerror("권한 오류", "스터디룸 예약 취소 권한이 없습니다.\n(예약 취소는 방장만 가능합니다.)")
            return

        if msgbox.askyesno("확인", "스터디룸 예약을 취소하시겠습니까?\n취소 시 전체 연속 예약 및 팀원 명단이 함께 삭제됩니다."):
            if reservation in RESERVATIONS:
                RESERVATIONS.remove(reservation)
                msgbox.showinfo("완료", "취소가 완료되었습니다.")
                self.show_mypage()

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()