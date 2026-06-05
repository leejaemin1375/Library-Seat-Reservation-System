import tkinter as tk
from tkinter import messagebox, simpledialog
from datetime import datetime, timedelta
import json
import os

# 각 모듈에서 필요한 페이지 및 함수 임포트
from login_2 import LoginPage
from reading_room import ReadingRoomPage, load_reading_rooms, save_reading_rooms
from study_room import StudyRoomPage, load_study_reservations, save_study_reservations, ROOMS as SR_ROOMS

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("도서관 좌석 및 스터디룸 예약 시스템")
        self.geometry("500x600")
        self.resizable(False, False)

        self.current_user = None
        self.current_frame = None

        # 처음 실행 시 로그인 페이지 표시
        self.show_login_page()

        # 실시간 노쇼 감지 타이머 가동 (1초마다 체크)
        self.auto_cancel_no_show()

    def clear_frame(self):
        """현재 화면에 그려진 모든 위젯을 깨끗하게 제거합니다."""
        if self.current_frame is not None:
            self.current_frame.destroy()

    def show_login_page(self):
        self.clear_frame()
        self.geometry("400x500")
        self.current_frame = LoginPage(self, on_login_success=self.on_login_success)
        self.current_frame.pack(fill="both", expand=True)

    def on_login_success(self, student_id):
        """로그인 성공 시 호출되는 핸들러"""
        self.current_user = student_id
        # 로그인 성공 후 메인 대시보드(마이페이지)로 이동
        self.show_mypage()

    def show_mypage(self):
        self.clear_frame()
        self.geometry("520x680") # 요소가 늘어남에 따라 창 크기를 안정적으로 확장합니다.
        self.resizable(False, False)

        self.current_frame = tk.Frame(self, padx=20, pady=20)
        self.current_frame.pack(fill="both", expand=True)

        header_frame = tk.Frame(self.current_frame)
        header_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(header_frame, text=f"{self.current_user}님, 환영합니다!", font=("맑은 고딕", 12, "bold")).pack(side="left")
        tk.Button(header_frame, text="로그아웃", bg="#757575", fg="white", font=("맑은 고딕", 9),
                  command=self.show_login_page).pack(side="right")

        menu_frame = tk.LabelFrame(self.current_frame, text="서비스 바로가기", font=("맑은 고딕", 10, "bold"), padx=15, pady=15)
        menu_frame.pack(fill="x", pady=10)

        tk.Button(menu_frame, text="열람실 좌석 예약", font=("맑은 고딕", 11), bg="#2196F3", fg="white", height=2,
                  command=self.show_reading_room_page).pack(fill="x", pady=5)
        tk.Button(menu_frame, text="스터디룸 예약", font=("맑은 고딕", 11), bg="#4CAF50", fg="white", height=2,
                  command=self.show_study_room_page).pack(fill="x", pady=5)

        status_box = tk.LabelFrame(self.current_frame, text="📅 나의 실시간 예약 현황 (현장 인증형)", font=("맑은 고딕", 10, "bold"), padx=15, pady=15)
        status_box.pack(fill="both", expand=True, pady=10)

        # 1. 개인 열람실 상태 확인
        rr_data = load_reading_rooms()
        rr_booked = None
        for room_name, seats_map in rr_data.items():
            for seat_num, s_info in seats_map.items():
                if s_info.get("user") == self.current_user:
                    if datetime.now() < datetime.strptime(s_info["end_time"], "%Y-%m-%d %H:%M"):
                        # 이용 규칙(3시간)에 따라 종료 시간에서 3시간을 빼서 시작(입실) 시간을 계산합니다.
                        end_dt = datetime.strptime(s_info["end_time"], "%Y-%m-%d %H:%M")
                        start_dt = end_dt - timedelta(hours=3)
                        start_t_str = start_dt.strftime("%Y-%m-%d %H:%M")
                        
                        rr_booked = (room_name, seat_num, start_t_str, s_info["end_time"], s_info.get("checked_in", False))
                        break

        tk.Label(status_box, text="■ 개인 열람실 현황", font=("맑은 고딕", 10, "bold"), fg="#4CAF50").pack(anchor="w", pady=2)
        if rr_booked:
            room_n, seat_n, start_t, end_t, is_ci = rr_booked
            
            # 레이아웃 깨짐을 방지하기 위해 입실 전용 대형 프레임 구성
            rr_frame = tk.Frame(status_box, bg="#f9f9f9", bd=1, relief="groove", padx=10, pady=8)
            rr_frame.pack(fill="x", pady=5)
            
            # 정보 텍스트 영역 (좌측 배치)
            info_frame = tk.Frame(rr_frame, bg="#f9f9f9")
            info_frame.pack(side="left", fill="both", expand=True)
            
            status_txt = " [착석확인 완료]" if is_ci else " [미인증! 10분 내 인증 필수]"
            tk.Label(info_frame, text=f"위치: {room_n} [{seat_n}번]{status_txt}", 
                     font=("맑은 고딕", 9, "bold"), fg="#333" if is_ci else "#e91e63", bg="#f9f9f9", anchor="w").pack(fill="x", pady=1)
            tk.Label(info_frame, text=f"▶ 입실 시간: {start_t}", font=("맑은 고딕", 9), fg="#555", bg="#f9f9f9", anchor="w").pack(fill="x", pady=1)
            tk.Label(info_frame, text=f"▶ 종료 시간: {end_t}", font=("맑은 고딕", 9), fg="#555", bg="#f9f9f9", anchor="w").pack(fill="x", pady=1)
            
            # 버튼 조작 영역 (우측 배치 및 정렬 겹침 방지)
            btn_frame = tk.Frame(rr_frame, bg="#f9f9f9")
            btn_frame.pack(side="right", fill="y", padx=(5, 0))
            
            tk.Button(btn_frame, text="반납", bg="#f44336", fg="white", font=("맑은 고딕", 9), width=8,
                      command=lambda: self.cancel_reading_room(room_n, seat_n)).pack(side="bottom", pady=2)
            
            tk.Button(btn_frame, text="좌석 이동", bg="#FF9800", fg="white", font=("맑은 고딕", 9), width=8,
                      command=lambda r_name=room_n: self.show_reading_room_for_move(r_name)).pack(side="bottom", pady=2)
            
            # 미인증 상태일 때 가장 위에 시인성이 높은 진분홍색(#e91e63) 인증코드 입력 버튼 배치
            if not is_ci:
                tk.Button(btn_frame, text="코드 입력", bg="#e91e63", fg="white", font=("맑은 고딕", 9, "bold"), width=8,
                          command=lambda: self.checkin_reading_room(room_n, seat_n)).pack(side="bottom", pady=2)
        else:
            tk.Label(status_box, text="예약된 열람실 좌석이 없습니다.", font=("맑은 고딕", 9), fg="gray").pack(anchor="w", padx=10, pady=5)

        # 2. 스터디룸 현황 파싱
        tk.Label(status_box, text="■ 스터디룸 현황", font=("맑은 고딕", 10, "bold"), fg="#2196F3").pack(anchor="w", pady=(10, 2))
        current_sr_list = load_study_reservations()
        sr_booked = [res for res in current_sr_list if res["leader"] == self.current_user or self.current_user in res["members"]]

        if sr_booked:
            sr_container = tk.Frame(status_box)
            sr_container.pack(fill="both", expand=True)
            for res in sr_booked:
                sr_frame = tk.Frame(sr_container, bg="#f9f9f9", bd=1, relief="groove", padx=10, pady=6)
                sr_frame.pack(fill="x", pady=3)
                
                sr_info_frame = tk.Frame(sr_frame, bg="#f9f9f9")
                sr_info_frame.pack(side="left", fill="both", expand=True)

                room_info = SR_ROOMS.get(int(res["room_id"]))
                if room_info:
                    room_name = room_info["name"]
                else:
                    room_name = f"알 수 없는 공간(ID: {res['room_id']})"

                ci_status = " [입실완료]" if res.get("checked_in", False) else " [미입실]"
                role_txt = "[방장]" if res["leader"] == self.current_user else f"[팀원]"
                
                tk.Label(sr_info_frame, text=f"{room_name}{ci_status} ({role_txt})", font=("맑은 고딕", 9, "bold"), bg="#f9f9f9", anchor="w").pack(fill="x")
                tk.Label(sr_info_frame, text=f"▶ 예약 일시: {res['date']}시 ({res['time_slot']}시)", font=("맑은 고딕", 9), fg="#555", bg="#f9f9f9", anchor="w").pack(fill="x")
                
                sr_btn_frame = tk.Frame(sr_frame, bg="#f9f9f9")
                sr_btn_frame.pack(side="right", fill="y")
                
                tk.Button(sr_btn_frame, text="취소", bg="#f44336", fg="white", font=("맑은 고딕", 8), width=8,
                          command=lambda r=res: self.cancel_study_room(r)).pack(side="bottom", pady=1)
                
                if not res.get("checked_in", False) and res["leader"] == self.current_user:
                    tk.Button(sr_btn_frame, text="코드 입력", bg="#e91e63", fg="white", font=("맑은 고딕", 8, "bold"), width=8,
                              command=lambda r=res: self.checkin_study_room(r)).pack(side="bottom", pady=1)
        else:
            tk.Label(status_box, text="예약된 스터디룸 내역이 없습니다.", font=("맑은 고딕", 9), fg="gray").pack(anchor="w", padx=10, pady=5)

    def show_reading_room_page(self):
        self.clear_frame()
        self.geometry("800x650")
        self.current_frame = ReadingRoomPage(self, self.current_user, on_back=self.show_mypage)
        self.current_frame.pack(fill="both", expand=True)

    def show_study_room_page(self):
        self.clear_frame()
        self.geometry("700x600")
        self.current_frame = StudyRoomPage(self, self.current_user, on_back=self.show_mypage)
        self.current_frame.pack(fill="both", expand=True)

    # ----------------- [열람실 제어 로직] -----------------
    def checkin_reading_room(self, room_name, seat_num):
        """열람실 좌석 착석 인증 수행"""
        rr_data = load_reading_rooms()
        if room_name in rr_data and seat_num in rr_data[room_name]:
            rr_data[room_name][seat_num]["checked_in"] = True
            save_reading_rooms(rr_data)
            messagebox.showinfo("인증 성공", f"[{room_name}] {seat_num}번 좌석 착석 인증이 완료되었습니다.")
            self.show_mypage()

    def cancel_reading_room(self, room_name, seat_num):
        """열람실 좌석 조기 반납"""
        if messagebox.askyesno("좌석 반납", "선택하신 좌석을 반납하시겠습니까?"):
            rr_data = load_reading_rooms()
            if room_name in rr_data and seat_num in rr_data[room_name]:
                del rr_data[room_name][seat_num]
                save_reading_rooms(rr_data)
                messagebox.showinfo("반납 완료", "좌석이 정상적으로 반납되었습니다.")
                self.show_mypage()

    # ----------------- [스터디룸 제어 로직] -----------------
    def checkin_study_room(self, reservation):
        """마이페이지 대시보드 내에서 스터디룸 문/벽면 벽체 코드 인증 핸들러"""
        room_id = int(reservation["room_id"])
        room_info = SR_ROOMS.get(room_id)
        if not room_info:
            return

        code = simpledialog.askstring("스터디룸 인증", f"[{room_info['name']}] 문 또는 벽면에 부착된 인증 코드를 입력하세요.")
        if code and code.strip().upper() == room_info["checkin_code"].upper():
            sr_data = load_study_reservations()
            for r in sr_data:
                if (r["leader"] == reservation["leader"] and r["date"] == reservation["date"] and 
                    r["room_id"] == reservation["room_id"] and r["time_slot"] == reservation["time_slot"]):
                    r["checked_in"] = True
                    break
            save_study_reservations(sr_data)
            messagebox.showinfo("인증 완료", "스터디룸 체크인이 정상 승인되었습니다.")
            self.show_mypage()
        elif code is not None:
            messagebox.showerror("인증 실패", "코드가 올바르지 않습니다. 다시 확인해 주세요.")

    def cancel_study_room(self, reservation):
        """마이페이지 대시보드 내에서 스터디룸 예약 취소"""
        if messagebox.askyesno("예약 취소", "스터디룸 예약을 취소하시겠습니까?"):
            sr_data = load_study_reservations()
            updated = [
                r for r in sr_data if not (
                    r["leader"] == reservation["leader"] and 
                    r["date"] == reservation["date"] and 
                    r["room_id"] == reservation["room_id"] and 
                    r["time_slot"] == reservation["time_slot"]
                )
            ]
            save_study_reservations(updated)
            messagebox.showinfo("취소 성공", "예약이 정상적으로 취소되었습니다.")
            self.show_mypage()

    # ----------------- [백그라운드 노쇼 자동 취소 엔진] -----------------
    def auto_cancel_no_show(self):
        """
        1초마다 실행되며 예약 시작 시간 10분이 지나도록 
        체크인(checked_in) 하지 않은 열람실 및 당일 스터디룸 예약을 무한 루프 없이 자동 취소합니다.
        """
        now = datetime.now()
        rr_changed = False
        sr_changed = False

        # 1. 열람실 노쇼 자동 회수 (종료시간 기점 또는 시작 기점 로직 적용 가능)
        try:
            rr_data = load_reading_rooms()
            for room_name, seats_map in rr_data.items():
                expired = [
                    seat_num for seat_num, s_info in seats_map.items()
                    if s_info.get("end_time") and
                    now > datetime.strptime(s_info["end_time"], "%Y-%m-%d %H:%M")
                ]
                for seat_num in expired:
                    del rr_data[room_name][seat_num]
                    rr_changed = True
            if rr_changed:
                save_reading_rooms(rr_data)
        except Exception as e:
            print(f"열람실 실시간 스캔 에러: {e}")

        # 2. 스터디룸 노쇼 자동 회수 (날짜 조건 오류 완벽 해결)
        try:
            sr_data = load_study_reservations()
            updated_sr = []
            for res in sr_data:
                # 9-10 형식에서 시작 시간인 앞쪽 시간(9) 추출
                start_hour = int(res["time_slot"].split("-")[0])
                # 예약 데이터의 날짜와 시작 시간을 결합하여 타임스탬프 객체 생성
                start_dt = datetime.strptime(f"{res['date']} {start_hour:02d}:00", "%Y-%m-%d %H:%M")

                # [버그 수정 완료] 오늘 날짜 이면서 시작한 지 10분이 넘었는데 미착석(미체크인)인 경우 -> 노쇼 대상 (제외)
                if now > (start_dt + timedelta(minutes=10)) and not res.get("checked_in", False):
                    sr_changed = True
                    continue # 삭제(회수) 대상이므로 updated_sr에 보존하지 않음
                
                updated_sr.append(res)

            if sr_changed:
                save_study_reservations(updated_sr)
        except Exception as e:
            print(f"스터디룸 실시간 노쇼 스캔 에러: {e}")

        # 데이터가 실제로 변경되었을 때, 사용자가 마이페이지를 보고 있다면 무한 루프 없이 단 1회 화면 갱신
        if (rr_changed or sr_changed) and hasattr(self, 'current_frame') and type(self.current_frame) is tk.Frame:
            # 현재 떠 있는 프레임의 타이틀 등을 체크하여 마이페이지 활성화 상태일 때만 리프레시 수행
            # 무한 대시보드 리로드 현상을 막기 위해 체크 구조 유지
            self.show_mypage()

        # 1초 뒤 재귀 호출
        self.after(1000, self.auto_cancel_no_show)

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()