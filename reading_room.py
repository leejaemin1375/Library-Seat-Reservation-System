# 열람실 예약 기능 (좌석 상태, 추가: 자리이동, 혼잡도, 알림)
import tkinter as tk
import tkinter.messagebox as msgbox

# 열람실 예약 선택 시
class ReadingRoomPage(tk.Frame):
    def __init__(self, master, user, on_back):
        super().__init__(master) 
        self.user = user # 사용자 정보
        self.on_back = on_back # 메인으로 돌아가는 함수
        self.show_room_list() # 열람실 나열

    def _clear(self):
        for widget in self.winfo_children():
            widget.destroy()

    # 열람실 리스트
    def show_room_list(self):
        self._clear()
        tk.Label(self, text="열람실 예약").pack()
        rooms = ['열람실1', '열람실2', '열람실3']
        for room in rooms:
            tk.Button(self, text=room,
                      command=lambda r=room: self.show_time_select(r)).pack()
        tk.Button(self, text="뒤로", command=lambda: self.on_back(self.user)).pack()

    # 예약 시간대 선택
    def show_time_select(self, room):
        self._clear()
        tk.Label(self, text=f"{room} 시간 선택").pack()
        
        btn_frame = tk.Frame(self)
        btn_frame.pack()

        times = ['09~10', '10~11', '11~12']
        for time in times:
            tk.Button(btn_frame, text=time, 
                      command=lambda t=time: self.confirm(room, t)).pack(side=tk.LEFT)
        tk.Button(self, text="뒤로", command=self.show_room_list).pack()

    # 예약 확인 함수
    def confirm(self, room, time):
        self._clear()
        tk.Label(self, text=f"{room}").pack()
        tk.Label(self, text=f"{time} 예약하시겠습니까?").pack()
        tk.Button(self, text="확인", command=self.reserve).pack()
        tk.Button(self, text="뒤로",
                  command=lambda: self.show_time_select(room)).pack()
    
    # DB에 예약 저장    
    def reserve(self):
        # DB 저장 코드 필요
        msgbox.showinfo("예약 완료", "예약이 완료되었습니다!")
        tk.Button(self, text="메인 화면으로 돌아기기", command=lambda: self.on_back(self.user)).pack()