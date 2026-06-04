import tkinter as tk
from tkinter import messagebox, simpledialog
from tkcalendar import DateEntry
from datetime import datetime

current_user = "20240001"

users = {
    "20240001": "김용준",
    "20240002": "이민수",
    "20240003": "박지훈",
    "20240004": "최유진",
    "20240005": "정수민",
    "20240006": "한지호",
    "20240007": "오세훈",
    "20240008": "윤가은",
    "20240009": "강민재",
    "20240010": "서지우",
}

rooms = {
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
time_slots = [f"{hour:02d}-{hour+1:02d}" for hour in range(9, 21)]

# 오늘 날짜 기준 문자열
today = datetime.today().date()
today_str = today.strftime("%Y-%m-%d")

# 상황을 보여주기 위해 오늘 날짜에 미리 예약된 데이터
# checked_in : False 이부분 체크인 안햇다는건데 솔직히 굳이 필요한지 모르겟어서 일단 보류
reservations = [
    {
        "leader": "20240002",
        "members": ["20240003", "20240004", "20240005", "20240006", "20240007"],
        "date": today_str,
        "room_id": 1,
        "time_slot": "09-10",
        "people_count": 6,
        "checked_in": False,
    },
    {
        "leader": "20240003",
        "members": ["20240004", "20240005"],
        "date": today_str,
        "room_id": 3,
        "time_slot": "13-14",
        "people_count": 3,
    },
    {
        "leader": "20240004",
        "members": ["20240005", "20240006", "20240007", "20240008"],
        "date": today_str,
        "room_id": 2,
        "time_slot": "18-19",
        "people_count": 5,
    },
    {
        "leader": "20240006",
        "members": ["20240007", "20240008"],
        "date": today_str,
        "room_id": 5,
        "time_slot": "16-17",
        "people_count": 3,
    },
    {
        "leader": "20240007",
        "members": ["20240008", "20240009", "20240010"],
        "date": today_str,
        "room_id": 9,
        "time_slot": "19-20",
        "people_count": 4,
    },
]

# 예약 진행 중인 상태를 보여주기 위한 임시 잠금 데이터
temp_locks = [
    {
        "date": today_str,
        "room_id": 4,
        "time_slot": "15-16",
        "user": "20240009",
    },
    {
        "date": today_str,
        "room_id": 8,
        "time_slot": "17-18",
        "user": "20240010",
    },
]


def is_reserved(date, room_id, time_slot):
    for r in reservations:
        if r["date"] == date and r["room_id"] == room_id and r["time_slot"] == time_slot:
            return True
    return False


def is_locked(date, room_id, time_slot):
    for lock in temp_locks:
        if lock["date"] == date and lock["room_id"] == room_id and lock["time_slot"] == time_slot:
            return True
    return False


def add_lock(date, room_id, time_slot):
    temp_locks.append({
        "date": date,
        "room_id": room_id,
        "time_slot": time_slot,
        "user": current_user
    })


def remove_lock(date, room_id, time_slot):
    for lock in temp_locks:
        if (
            lock["date"] == date
            and lock["room_id"] == room_id
            and lock["time_slot"] == time_slot
            and lock["user"] == current_user
        ):
            temp_locks.remove(lock)
            return


def clear_screen():
    for widget in root.winfo_children():
        widget.destroy()
# 지난 날짜 선택 불가 
def validate_date(selected_date):

    today = datetime.today().date()

    if selected_date < today:
        messagebox.showerror(
            "날짜 오류",
            "지난 날짜는 예약할 수 없습니다."
        )
        return False

    return True
# 지난 시간 선택 불가 
def is_past_time(date, time_slot):

    selected_date = datetime.strptime(
        date,
        "%Y-%m-%d"
    ).date()

    now = datetime.now()

    # 오늘 날짜가 아니면 지난 시간 검사 안 함
    if selected_date != now.date():
        return False

    start_hour = int(time_slot.split("-")[0])
    end_hour = int(time_slot.split("-")[1])

    end_time = datetime(
        now.year,
        now.month,
        now.day,
        end_hour,
        0
    )

    # 종료 시간이 현재 시간보다 지났으면 마감
    if now >= end_time:
        return True

    return False
# 체크인 기능
def check_in(reservation):
    if reservation.get("checked_in") == True:
        messagebox.showinfo("체크인", "이미 체크인 완료된 예약입니다.")
        return

    possible, msg = can_check_in(reservation)

    if not possible:
        messagebox.showerror("체크인 불가", msg)
        return

    room = rooms[reservation["room_id"]]

    input_code = simpledialog.askstring(
        "체크인 코드 입력",
        f"{room['name']} 내부에 부착된 체크인 코드를 입력하세요."
    )

    if input_code is None:
        return

    if input_code == room["checkin_code"]:
        reservation["checked_in"] = True
        messagebox.showinfo("체크인 완료", "체크인이 완료되었습니다.")
        show_my_reservation_screen()
    else:
        messagebox.showerror("체크인 실패", "체크인 코드가 일치하지 않습니다.")
# 체크인 가능시간 검사
def can_check_in(reservation):

    now = datetime.now()

    reservation_date = datetime.strptime(
        reservation["date"],
        "%Y-%m-%d"
    ).date()

    if reservation_date != now.date():
        return False, "예약한 날짜에만 체크인할 수 있습니다."

    start_hour = int(reservation["time_slot"].split("-")[0])
    end_hour = int(reservation["time_slot"].split("-")[1])

    start_time = datetime(
        now.year,
        now.month,
        now.day,
        start_hour,
        0
    )

    end_time = datetime(
        now.year,
        now.month,
        now.day,
        end_hour,
        0
    )

    if now < start_time:
        return False, "아직 체크인 시간이 아닙니다."

    if now >= end_time:
        return False, "예약 시간이 종료되었습니다."

    return True, "체크인 가능"
# 방 내부 코드 확인
def show_room_code(room_id):
    room = rooms[room_id]

    messagebox.showinfo(
        "방 내부 체크인 코드",
        f"{room['name']} 내부에 부착된 코드입니다.\n\n"
        f"체크인 코드: {room['checkin_code']}"
    )

# 1. 날짜 선택 화면
def show_date_screen():
    clear_screen()

    tk.Label(
        root,
        text="스터디룸 예약 시스템",
        font=("맑은 고딕", 22, "bold")
    ).pack(pady=25)

    tk.Label(
        root,
        text=f"현재 로그인 사용자: {current_user}",
        font=("맑은 고딕", 12)
    ).pack(pady=5)

    tk.Label(
        root,
        text="예약할 날짜를 선택하세요.",
        font=("맑은 고딕", 15)
    ).pack(pady=20)
    
    tk.Button(
        root,
        text="내 예약 조회 / 취소 / 자리이동",
        command=show_my_reservation_screen
    ).pack(pady=30)
    
    frame = tk.Frame(root)
    frame.pack(pady=10)

    tk.Label(frame, text="날짜 입력:", font=("맑은 고딕", 12)).pack(side="left")
    # 날짜 선택 위젯 추가 (색상, 크기, 폰트 등 설정 가능)
    date_entry = DateEntry(
    frame,
    width=18,
    font=("맑은 고딕", 12),
    background="darkblue",
    foreground="white",
    borderwidth=2,
    date_pattern="yyyy-mm-dd",
    mindate=datetime.today().date()
)
    # 오늘 날짜로 초기값 설정 
    date_entry.set_date(today)
    
    date_entry.pack(side="left", padx=10)
    
    tk.Button(
        frame,
        text="조회",
        font=("맑은 고딕", 11),
        command=lambda: show_room_screen(date_entry.get().strip())
    ).pack(side="left")


# 2. 스터디룸 선택 화면
def show_room_screen(date):
    if date == "":
        messagebox.showwarning("입력 오류", "날짜를 입력하세요.")
        return

    clear_screen()

    tk.Label(
        root,
        text=f"{date} 예약할 공간 선택",
        font=("맑은 고딕", 20, "bold")
    ).pack(pady=20)

    tk.Label(
        root,
        text="스터디룸을 선택하면 해당 날짜의 예약 가능 시간이 표시됩니다.",
        font=("맑은 고딕", 12)
    ).pack(pady=5)

    room_frame = tk.Frame(root)
    room_frame.pack(pady=15)

    for room_id, room in rooms.items():
        btn = tk.Button(
            room_frame,
            text=f"{room['name']}\n정원 {room['capacity']}명 / 최소 {room['min_people']}명",
            width=24,
            height=3,
            bg="#d9eaff",
            command=lambda r=room_id: show_time_screen(date, r)
        )
        btn.grid(row=(room_id - 1) // 3, column=(room_id - 1) % 3, padx=10, pady=10)

    bottom = tk.Frame(root)
    bottom.pack(pady=10)

    tk.Button(bottom, text="날짜 다시 선택", command=show_date_screen).pack(side="left", padx=10)


# 3. 시간 선택 화면
def show_time_screen(date, room_id):
    clear_screen()

    room = rooms[room_id]

    tk.Label(
        root,
        text=f"{room['name']} 예약 가능 시간",
        font=("맑은 고딕", 20, "bold")
    ).pack(pady=15)

    tk.Label(
        root,
        text=f"날짜: {date}    정원: {room['capacity']}명    최소인원: {room['min_people']}명",
        font=("맑은 고딕", 13)
    ).pack(pady=5)

    legend = tk.Frame(root)
    legend.pack(pady=10)

    tk.Label(legend, text="가능", bg="#9be79b", width=10).pack(side="left", padx=5)
    tk.Label(legend, text="선택중", bg="#ffe680", width=10).pack(side="left", padx=5)
    tk.Label(legend, text="사용중", bg="#ff9fbd", width=10).pack(side="left", padx=5)

    tk.Button(
    root,
    text="방 내부 코드 확인",
    bg="#eeeeee",
    command=lambda: show_room_code(room_id)
    ).pack(pady=5)

    time_frame = tk.Frame(root)
    time_frame.pack(pady=15)

    for index, slot in enumerate(time_slots):
        if is_past_time(date, slot):

            text = f"{slot}\n마감"
            color = "#d3d3d3"
            state = "disabled"

        elif is_reserved(date, room_id, slot):

            text = f"{slot}\n사용중"
            color = "#ff9fbd"
            state = "disabled"

        elif is_locked(date, room_id, slot):

            text = f"{slot}\n선택중"
            color = "#ffe680"
            state = "disabled"

        else:

            text = f"{slot}\n가능"
            color = "#9be79b"
            state = "normal"

        tk.Button(
            time_frame,
            text=text,
            width=12,
            height=3,
            bg=color,
            state=state,
            command=lambda s=slot: reserve_room(date, room_id, s)
        ).grid(row=index // 4, column=index % 4, padx=8, pady=8)

    bottom = tk.Frame(root)
    bottom.pack(pady=10)

    tk.Button(bottom, text="스터디룸 다시 선택", command=lambda: show_room_screen(date)).pack(side="left", padx=10)
    tk.Button(bottom, text="날짜 다시 선택", command=show_date_screen).pack(side="left", padx=10)


# 4. 예약 처리
def reserve_room(date, room_id, time_slot):
    room = rooms[room_id]

    if is_reserved(date, room_id, time_slot):
        messagebox.showerror("예약 불가", "이미 사용중인 시간입니다.")
        return

    if is_locked(date, room_id, time_slot):
        messagebox.showerror("예약 불가", "다른 사용자가 선택중인 시간입니다.")
        return

    add_lock(date, room_id, time_slot)
    show_time_screen(date, room_id)

    member_input = simpledialog.askstring(
        "팀원 학번 입력",
        f"{room['name']} / {time_slot}\n"
        f"날짜: {date}\n"
        f"정원 {room['capacity']}명 / 최소인원 {room['min_people']}명\n\n"
        f"팀원 학번을 쉼표로 입력하세요.\n"
        f"본인({current_user})은 자동 포함됩니다."
    )

    if member_input is None:
        remove_lock(date, room_id, time_slot)
        show_time_screen(date, room_id)
        return

    if member_input.strip() == "":
        members = []
    else:
        members = [m.strip() for m in member_input.split(",")]

    if current_user in members:
        messagebox.showerror("입력 오류", "본인 학번은 자동 포함되므로 입력하지 않아도 됩니다.")
        remove_lock(date, room_id, time_slot)
        show_time_screen(date, room_id)
        return

    if len(members) != len(set(members)):
        messagebox.showerror("입력 오류", "팀원 학번이 중복되었습니다.")
        remove_lock(date, room_id, time_slot)
        show_time_screen(date, room_id)
        return

    for member in members:
        if member not in users:
            messagebox.showerror("입력 오류", f"{member} 학번은 존재하지 않습니다.")
            remove_lock(date, room_id, time_slot)
            show_time_screen(date, room_id)
            return

    total_people = len(members) + 1

    if total_people < room["min_people"]:
        messagebox.showerror(
            "예약 불가",
            f"최소 인원 {room['min_people']}명을 충족하지 못했습니다.\n"
            f"현재 인원: {total_people}명"
        )
        remove_lock(date, room_id, time_slot)
        show_time_screen(date, room_id)
        return

    if total_people > room["capacity"]:
        messagebox.showerror(
            "예약 불가",
            f"정원 {room['capacity']}명을 초과했습니다.\n"
            f"현재 인원: {total_people}명"
        )
        remove_lock(date, room_id, time_slot)
        show_time_screen(date, room_id)
        return

    reservations.append({
        "leader": current_user,
        "members": members,
        "date": date,
        "room_id": room_id,
        "time_slot": time_slot,
        "people_count": total_people,
    })

    remove_lock(date, room_id, time_slot)

    messagebox.showinfo(
        "예약 완료",
        f"예약이 완료되었습니다.\n\n"
        f"날짜: {date}\n"
        f"공간: {room['name']}\n"
        f"시간: {time_slot}\n"
        f"총 인원: {total_people}명"
    )

    show_time_screen(date, room_id)

def show_my_reservation_screen():
    clear_screen()

    tk.Label(
        root,
        text="내 예약 조회 / 취소",
        font=("맑은 고딕", 20, "bold")
    ).pack(pady=20)


    my_reservations = []

    for r in reservations:
        if r["leader"] == current_user:
            my_reservations.append(r)

    if len(my_reservations) == 0:
        tk.Label(
            root,
            text="현재 예약 내역이 없습니다.",
            font=("맑은 고딕", 13)
        ).pack(pady=20)

    else:
        for index, r in enumerate(my_reservations):
            room_name = rooms[r["room_id"]]["name"]
            members = ", ".join(r["members"]) if r["members"] else "없음"

            frame = tk.Frame(root, relief="solid", borderwidth=1)
            frame.pack(pady=8, padx=20, fill="x")

            checkin_status = "체크인 완료" if r.get("checked_in") else "체크인 전"
            text = (
                f"날짜: {r['date']} | 공간: {room_name} | 시간: {r['time_slot']}\n"
                f"예약자: {r['leader']} | 팀원: {members} | 인원: {r['people_count']}명\n"
                f"체크인 상태: {checkin_status}"
            )

            tk.Label(
                frame,
                text=text,
                font=("맑은 고딕", 11),
                justify="left"
            ).pack(side="left", padx=10, pady=10)

            tk.Button(
                frame,
                text="예약 취소",
                bg="#ffb3b3",
                command=lambda reservation=r: cancel_reservation(reservation)
            ).pack(side="right", padx=10)

            tk.Button(
                frame,
                text="자리 이동",
                bg="#b3d9ff",
                command=lambda reservation=r: move_reservation_screen(reservation)
            ).pack(side="right", padx=10)

            tk.Button(
                frame,
                text="체크인",
                bg="#c2f0c2",
                command=lambda reservation=r: check_in(reservation)
            ).pack(side="right", padx=10)
    tk.Button(
        root,
        text="처음으로",
        command=show_date_screen
    ).pack(pady=20)
def cancel_reservation(reservation):
    answer = messagebox.askyesno(
        "예약 취소",
        "정말 예약을 취소하시겠습니까?"
    )

    if answer:
        reservations.remove(reservation)
        messagebox.showinfo("취소 완료", "예약이 취소되었습니다.")
        show_my_reservation_screen()

def move_reservation_screen(reservation):
    clear_screen()

    date = reservation["date"]
    old_room_id = reservation["room_id"]
    old_time_slot = reservation["time_slot"]

    tk.Label(
        root,
        text="자리 이동",
        font=("맑은 고딕", 20, "bold")
    ).pack(pady=20)

    tk.Label(
        root,
        text=f"현재 예약: {rooms[old_room_id]['name']} / {old_time_slot}",
        font=("맑은 고딕", 13)
    ).pack(pady=10)

    tk.Label(
        root,
        text="이동할 스터디룸을 선택하세요.",
        font=("맑은 고딕", 12)
    ).pack(pady=10)

    room_frame = tk.Frame(root)
    room_frame.pack(pady=10)

    for room_id, room in rooms.items():
        tk.Button(
            room_frame,
            text=f"{room['name']}\n정원 {room['capacity']}명 / 최소 {room['min_people']}명",
            width=24,
            height=3,
            bg="#d9eaff",
            command=lambda r=room_id: move_time_screen(reservation, r)
        ).grid(row=(room_id - 1) // 3, column=(room_id - 1) % 3, padx=10, pady=10)

    tk.Button(
        root,
        text="뒤로가기",
        command=show_my_reservation_screen
    ).pack(pady=15)

def move_time_screen(reservation, new_room_id):
    clear_screen()

    date = reservation["date"]
    room = rooms[new_room_id]

    tk.Label(
        root,
        text=f"{room['name']} 이동 가능 시간",
        font=("맑은 고딕", 20, "bold")
    ).pack(pady=15)

    tk.Label(
        root,
        text=f"날짜: {date}    정원: {room['capacity']}명    최소인원: {room['min_people']}명",
        font=("맑은 고딕", 13)
    ).pack(pady=5)

    time_frame = tk.Frame(root)
    time_frame.pack(pady=15)

    for index, slot in enumerate(time_slots):
        if is_past_time(date, slot):
            text = f"{slot}\n마감"
            color = "#d3d3d3"
            state = "disabled"

        elif is_reserved(date, new_room_id, slot):
            text = f"{slot}\n사용중"
            color = "#ff9fbd"
            state = "disabled"

        elif is_locked(date, new_room_id, slot):
            text = f"{slot}\n선택중"
            color = "#ffe680"
            state = "disabled"

        else:
            text = f"{slot}\n가능"
            color = "#9be79b"
            state = "normal"

        tk.Button(
            time_frame,
            text=text,
            width=12,
            height=3,
            bg=color,
            state=state,
            command=lambda s=slot: move_reservation(reservation, new_room_id, s)
        ).grid(row=index // 4, column=index % 4, padx=8, pady=8)

    tk.Button(
        root,
        text="뒤로가기",
        command=lambda: move_reservation_screen(reservation)
    ).pack(pady=15)   
def move_reservation(reservation, new_room_id, new_time_slot):
    date = reservation["date"]
    new_room = rooms[new_room_id]

    total_people = reservation["people_count"]

    # 이동할 스터디룸의 최소 인원 검사
    if total_people < new_room["min_people"]:
        messagebox.showerror(
            "이동 불가",
            f"{new_room['name']}은 최소 {new_room['min_people']}명 이상이어야 합니다.\n"
            f"현재 예약 인원: {total_people}명"
        )
        return

    # 이동할 스터디룸의 정원 초과 검사
    if total_people > new_room["capacity"]:
        messagebox.showerror(
            "이동 불가",
            f"{new_room['name']}의 정원은 {new_room['capacity']}명입니다.\n"
            f"현재 예약 인원: {total_people}명"
        )
        return

    if is_reserved(date, new_room_id, new_time_slot):
        messagebox.showerror("이동 불가", "이미 사용중인 시간입니다.")
        return

    if is_locked(date, new_room_id, new_time_slot):
        messagebox.showerror("이동 불가", "다른 사용자가 선택중인 시간입니다.")
        return

    answer = messagebox.askyesno(
        "자리 이동",
        f"{new_room['name']} / {new_time_slot} 으로 이동하시겠습니까?"
    )

    if not answer:
        return

    reservation["room_id"] = new_room_id
    reservation["time_slot"] = new_time_slot

    messagebox.showinfo("이동 완료", "자리 이동이 완료되었습니다.")
    show_my_reservation_screen()

root = tk.Tk()
root.title("스터디룸 예약 시스템")
root.geometry("900x700")

show_date_screen()

root.mainloop()
