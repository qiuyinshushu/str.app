import streamlit as st
import json
import os

# 初始化会话状态，保存登录用户
if "current_user" not in st.session_state:
    st.session_state.current_user = None

# ==================== 用户类 ====================
class User:
    def __init__(self, username, account, password):
        self.username = username
        self.account = account
        self.password = password
    def to_dict(self):
        return {
            "username": self.username,
            "account": self.account,
            "password": self.password,
        }
    @classmethod
    def from_dict(cls, data):
        return cls(data["username"], data["account"], data["password"])
    def __str__(self):
        return f"用户名: {self.username}, 账号: {self.account}"

# ==================== 座位类 ====================
class Seat:
    VALID_AREAS = ["北区", "南区", "中区"]
    VALID_TYPES = ["普通座", "电脑座"]
    VALID_FLOORS = range(1, 7)
    VALID_SEAT_IDS = range(1, 101)
    def __init__(self, seat_id, floor, area, seat_type):
        self.seat_id = seat_id
        self.floor = floor
        self.area = area
        self.seat_type = seat_type
        self.status = "空闲"
        self.reserved_by = None
    def change_status(self, new_status):
        self.status = new_status
    def reserve(self, username):
        self.status = "已预约"
        self.reserved_by = username
    def release(self):
        self.status = "空闲"
        self.reserved_by = None
    def occupy(self, username):
        self.status = "已占用"
        self.reserved_by = username
    def to_dict(self):
        return {
            "seat_id": self.seat_id,
            "floor": self.floor,
            "area": self.area,
            "seat_type": self.seat_type,
            "status": self.status,
            "reserved_by": self.reserved_by,
        }
    @classmethod
    def from_dict(cls, data):
        seat = cls(data["seat_id"], data["floor"], data["area"], data["seat_type"])
        seat.status = data["status"]
        seat.reserved_by = data["reserved_by"]
        return seat
    def __str__(self):
        reserved_info = self.reserved_by if self.reserved_by else "无"
        return (f"{self.floor}楼{self.area}{self.seat_type}|"
                f"编号:{self.seat_id}|状态:{self.status}|预约人:{reserved_info}")
    def __eq__(self, other):
        if not isinstance(other, Seat):
            return False
        return (self.seat_id == other.seat_id
                and self.floor == other.floor
                and self.area == other.area
                and self.seat_type == other.seat_type)

# ==================== 文件管理类 ====================
class FileManager:
    def __init__(self, user_file="users.json", seat_file="seats.json"):
        self.user_file = user_file
        self.seat_file = seat_file
    def load_users(self):
        if not os.path.exists(self.user_file):
            return {}
        try:
            with open(self.user_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {username: User.from_dict(info) for username, info in data.items()}
        except (json.JSONDecodeError, KeyError):
            st.write(f"[警告] 用户文件 {self.user_file} 格式错误，将使用空数据。")
            return {}
    def save_users(self, users):
        data = {username: user.to_dict() for username, user in users.items()}
        with open(self.user_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        st.write(f"[系统] 用户数据已保存到 {self.user_file}")
    def load_seats(self):
        if not os.path.exists(self.seat_file):
            return []
        try:
            with open(self.seat_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [Seat.from_dict(info) for info in data]
        except (json.JSONDecodeError, KeyError):
            st.write(f"[警告] 座位文件 {self.seat_file} 格式错误，将使用空数据。")
            return []
    def save_seats(self, seats):
        data = [seat.to_dict() for seat in seats]
        with open(self.seat_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        st.write(f"[系统] 座位数据已保存到 {self.seat_file}")

# ==================== 图书馆管理系统类 ====================
class LibrarySystem:
    def __init__(self):
        self.file_manager = FileManager()
        self.users = self.file_manager.load_users()
        self.seats = self.file_manager.load_seats()
        self.current_user = st.session_state.current_user

    def _save_all(self):
        self.file_manager.save_users(self.users)
        self.file_manager.save_seats(self.seats)

    def _find_seat(self, seat_id, floor, area, seat_type):
        for seat in self.seats:
            if (seat.seat_id == seat_id and seat.floor == floor
                    and seat.area == area and seat.seat_type == seat_type):
                return seat
        return None

    def _validate_seat_input(self, seat_id, floor, area, seat_type):
        if seat_id not in Seat.VALID_SEAT_IDS:
            return False, "座位编号必须在1~100之间。"
        if floor not in Seat.VALID_FLOORS:
            return False, "楼层必须在1~6之间。"
        if area not in Seat.VALID_AREAS:
            return False, "区域必须为北区、南区或中区。"
        if seat_type not in Seat.VALID_TYPES:
            return False, "座位类型必须为普通座或电脑座。"
        return True, ""

    def register(self, username, account, password, confirm_pwd):
        st.write("\n----- 用户注册 -----")
        if not username:
            st.write("[错误] 用户名不能为空！")
            return False
        if username in self.users:
            st.write("[错误] 该用户名已被注册，请更换一个。")
            return False
        if not account:
            st.write("[错误] 账号不能为空！")
            return False
        if not password:
            st.write("[错误] 密码不能为空！")
            return False
        if password != confirm_pwd:
            st.write("[错误] 两次输入的密码不一致！")
            return False
        self.users[username] = User(username, account, password)
        self.file_manager.save_users(self.users)
        st.write(f"[成功] 用户 {username} 注册成功！")
        return True

    def login(self, username, account, password):
        st.write("\n----- 用户登录 -----")
        if username not in self.users:
            st.write("[错误] 用户名不存在，请先注册。")
            return False
        user = self.users[username]
        if user.account == account and user.password == password:
            self.current_user = username
            st.session_state.current_user = username
            st.write(f"[成功] 欢迎回来，{username}！")
            return True
        else:
            st.write("[错误] 账号或密码错误！")
            return False

    def logout(self):
        if self.current_user:
            st.write(f"[系统] 用户 {self.current_user} 已登出。")
            self.current_user = None
            st.session_state.current_user = None
        else:
            st.write("[提示] 当前没有登录用户。")

    def show_user_info(self):
        if not self.current_user:
            st.write("[提示] 请先登录。")
            return
        user = self.users[self.current_user]
        st.write(f"\n----- 当前用户信息 -----")
        st.write(f"  用户名: {user.username}")
        st.write(f"  账  号: {user.account}")
        reserved_count = sum(1 for s in self.seats if s.reserved_by == self.current_user)
        st.write(f"  已预约座位数: {reserved_count}")

    def add_seat(self, seat_id, floor, area, seat_type):
        st.write("\n----- 添加座位 -----")
        valid, msg = self._validate_seat_input(seat_id, floor, area, seat_type)
        if not valid:
            st.write(f"[错误] {msg}")
            return
        if self._find_seat(seat_id, floor, area, seat_type):
            st.write("[错误] 该座位已存在，请勿重复添加。")
            return
        new_seat = Seat(seat_id, floor, area, seat_type)
        self.seats.append(new_seat)
        self.file_manager.save_seats(self.seats)
        st.write(f"[成功] 座位添加成功：{new_seat}")

    def show_seats(self):
        st.write("\n----- 座位列表 -----")
        if not self.seats:
            st.write("  （暂无座位数据）")
            return
        sorted_seats = sorted(self.seats, key=lambda s: (s.floor, s.area, s.seat_id))
        for seat in sorted_seats:
            st.write(f"  {seat}")

    def search_seats(self, choice, floor_in, area_in, type_in, status_in):
        st.write("\n----- 查询座位 -----")
        st.write("可按以下条件查询：")
        st.write("  1 - 按楼层查询")
        st.write("  2 - 按区域查询")
        st.write("  3 - 按类型查询")
        st.write("  4 - 按状态查询")
        st.write("  5 - 查询我预约的座位")
        results = []
        if choice == "1":
            results = [s for s in self.seats if s.floor == floor_in]
        elif choice == "2":
            results = [s for s in self.seats if s.area == area_in]
        elif choice == "3":
            results = [s for s in self.seats if s.seat_type == type_in]
        elif choice == "4":
            results = [s for s in self.seats if s.status == status_in]
        elif choice == "5":
            if not self.current_user:
                st.write("[提示] 请先登录。")
                return
            results = [s for s in self.seats if s.reserved_by == self.current_user]
        else:
            st.write("[错误] 无效选项。")
            return
        if not results:
            st.write("  未找到符合条件的座位。")
        else:
            for seat in results:
                st.write(f"  {seat}")

    def reserve_seat(self, seat_id, floor, area, seat_type, confirm_choice):
        if not self.current_user:
            st.write("[提示] 请先登录后再预约座位。")
            return
        st.write("\n----- 预约座位 -----")
        seat = self._find_seat(seat_id, floor, area, seat_type)
        if not seat:
            st.write("[错误] 未找到该座位，请确认座位信息。")
            return
        if seat.status != "空闲":
            st.write(f"[错误] 该座位当前状态为「{seat.status}」，无法预约。")
            return
        user_reserved = [s for s in self.seats if s.reserved_by == self.current_user]
        if user_reserved:
            st.write(f"[提示] 您已预约了以下座位：")
            for s in user_reserved:
                st.write(f"  {s}")
            if confirm_choice != "y":
                st.write("[提示] 已取消预约。")
                return
        seat.reserve(self.current_user)
        self.file_manager.save_seats(self.seats)
        st.write(f"[成功] 预约成功！{seat}")

    def occupy_seat(self, seat_id, floor, area, seat_type):
        if not self.current_user:
            st.write("[提示] 请先登录。")
            return
        st.write("\n----- 签到占座 -----")
        seat = self._find_seat(seat_id, floor, area, seat_type)
        if not seat:
            st.write("[错误] 未找到该座位。")
            return
        if seat.status == "已占用":
            st.write("[错误] 该座位已被占用。")
            return
        if seat.reserved_by != self.current_user:
            st.write("[错误] 该座位不是您预约的，无法签到。")
            return
        seat.occupy(self.current_user)
        self.file_manager.save_seats(self.seats)
        st.write(f"[成功] 签到成功！{seat}")

    def release_seat(self, seat_id, floor, area, seat_type):
        st.write("\n----- 释放座位 -----")
        seat = self._find_seat(seat_id, floor, area, seat_type)
        if not seat:
            st.write("[错误] 未找到该座位。")
            return
        if seat.status == "空闲":
            st.write("[提示] 该座位已经是空闲状态，无需释放。")
            return
        if self.current_user and seat.reserved_by != self.current_user:
            st.write("[错误] 您只能释放自己预约的座位。")
            return
        seat.release()
        self.file_manager.save_seats(self.seats)
        st.write(f"[成功] 座位已释放：{seat}")

    def modify_seat(self, old_id, old_floor, old_area, old_type, new_id, new_floor, new_area, new_type):
        if not self.current_user:
            st.write("[提示] 请先登录。")
            return
        st.write("\n----- 修改预约（更换座位）-----")
        st.write("请输入原座位信息：")
        old_seat = self._find_seat(old_id, old_floor, old_area, old_type)
        if not old_seat:
            st.write("[错误] 未找到原座位。")
            return
        if old_seat.reserved_by != self.current_user:
            st.write("[错误] 您只能修改自己预约的座位。")
            return
        st.write("请输入新座位信息：")
        new_seat = self._find_seat(new_id, new_floor, new_area, new_type)
        if not new_seat:
            st.write("[错误] 未找到新座位，请确认座位信息。")
            return
        if new_seat.status != "空闲":
            st.write(f"[错误] 新座位当前状态为「{new_seat.status}」，无法预约。")
            return
        old_seat.release()
        new_seat.reserve(self.current_user)
        self.file_manager.save_seats(self.seats)
        st.write(f"[成功] 已将预约从 {old_floor}楼{old_area}{old_type}#{old_id} 更换为 {new_seat}")

    def delete_seat(self, seat_id, floor, area, seat_type, confirm_del):
        st.write("\n----- 删除座位 -----")
        seat = self._find_seat(seat_id, floor, area, seat_type)
        if not seat:
            st.write("[错误] 未找到该座位。")
            return
        if seat.status != "空闲":
            st.write(f"[警告] 该座位当前状态为「{seat.status}」，仍有用户在使用！")
            if confirm_del != "y":
                st.write("[提示] 已取消删除。")
                return
        self.seats.remove(seat)
        self.file_manager.save_seats(self.seats)
        st.write(f"[成功] 座位已删除：{floor}楼{area}{seat_type}#{seat_id}")

    def statistics(self):
        st.write("\n===== 数据统计 =====")
        total = len(self.seats)
        free = sum(1 for s in self.seats if s.status == "空闲")
        reserved = sum(1 for s in self.seats if s.status == "已预约")
        occupied = sum(1 for s in self.seats if s.status == "已占用")
        st.write(f"  座位总数: {total}")
        st.write(f"  空闲座位: {free}")
        st.write(f"  已预约:   {reserved}")
        st.write(f"  已占用:   {occupied}")
        st.write(f"  使用率:   {((reserved + occupied) / total * 100):.1f}%" if total > 0 else "  使用率:   N/A")
        if total > 0:
            st.write("\n  --- 按楼层统计 ---")
            for floor in sorted(set(s.floor for s in self.seats)):
                floor_seats = [s for s in self.seats if s.floor == floor]
                floor_used = sum(1 for s in floor_seats if s.status != "空闲")
                st.write(f"  {floor}楼: 共{len(floor_seats)}个座位, 已使用{floor_used}个")
        if total > 0:
            st.write("\n  --- 按类型统计 ---")
            for seat_type in Seat.VALID_TYPES:
                type_seats = [s for s in self.seats if s.seat_type == seat_type]
                type_used = sum(1 for s in type_seats if s.status != "空闲")
                st.write(f"  {seat_type}: 共{len(type_seats)}个, 已使用{type_used}个")
        if total > 0:
            st.write("\n  --- 按区域统计 ---")
            for area in Seat.VALID_AREAS:
                area_seats = [s for s in self.seats if s.area == area]
                area_used = sum(1 for s in area_seats if s.status != "空闲")
                st.write(f"  {area}: 共{len(area_seats)}个, 已使用{area_used}个")
        st.write(f"\n  注册用户总数: {len(self.users)}")
        st.write("=====================")

# 主程序入口
def main():
    st.title("图书馆座位预约管理系统")
    system = LibrarySystem()
    st.write("欢迎使用图书馆座位预约管理系统！")
    st.write(f"[系统] 已加载 {len(system.users)} 个用户, {len(system.seats)} 个座位。")

    # 主功能下拉菜单（替代原while循环）
    menu_list = [
        "0 - 退出系统",
        "1 - 用户注册",
        "2 - 用户登录",
        "3 - 用户登出",
        "4 - 查看个人信息",
        "5 - 添加座位",
        "6 - 显示所有座位",
        "7 - 查询座位",
        "8 - 预约座位",
        "9 - 签到占座",
        "10 - 释放座位",
        "11 - 修改预约（更换座位）",
        "12 - 删除座位",
        "13 - 数据统计",
        "14 - 保存数据"
    ]
    choice = st.selectbox("请选择功能选项", menu_list)

    # 0 退出系统
    if choice == "0 - 退出系统":
        system._save_all()
        st.write("感谢使用，再见！")

    # 1 用户注册
    elif choice == "1 - 用户注册":
        uname = st.text_input("请设置用户名：")
        acc = st.text_input("请设置账号：")
        pwd = st.text_input("请设置密码：", type="password")
        cpwd = st.text_input("请确认密码：", type="password")
        if st.button("提交注册"):
            system.register(uname, acc, pwd, cpwd)

    # 2 用户登录
    elif choice == "2 - 用户登录":
        uname = st.text_input("请输入用户名：")
        acc = st.text_input("请输入账号：")
        pwd = st.text_input("请输入密码：", type="password")
        if st.button("登录"):
            system.login(uname, acc, pwd)

    # 3 用户登出
    elif choice == "3 - 用户登出":
        system.logout()

    # 4 查看个人信息
    elif choice == "4 - 查看个人信息":
        system.show_user_info()

    # 5 添加座位
    elif choice == "5 - 添加座位":
        sid = st.number_input("请输入座位编号(1~100)：", min_value=1, max_value=100)
        floor = st.number_input("请输入楼层(1~6)：", min_value=1, max_value=6)
        area = st.text_input("请输入区域（北区/南区/中区）：")
        stype = st.text_input("请选择座位类型（普通座/电脑座）：")
        if st.button("确认添加"):
            system.add_seat(sid, floor, area, stype)

    # 6 显示所有座位
    elif choice == "6 - 显示所有座位":
        system.show_seats()

    # 7 查询座位
    elif choice == "7 - 查询座位":
        q_choice = st.selectbox("选择查询方式", ["1","2","3","4","5"])
        f = st.number_input("楼层", min_value=1, max_value=6)
        a = st.text_input("区域")
        t = st.text_input("座位类型")
        s = st.text_input("状态")
        if st.button("执行查询"):
            system.search_seats(q_choice, f, a, t, s)

    # 8 预约座位
    elif choice == "8 - 预约座位":
        sid = st.number_input("请输入座位编号(1~100)：", min_value=1, max_value=100)
        floor = st.number_input("请输入楼层(1~6)：", min_value=1, max_value=6)
        area = st.text_input("请输入区域（北区/南区/中区）：")
        stype = st.text_input("请选择座位类型（普通座/电脑座）：")
        confirm = st.text_input("是否继续预约新座位？(y/n)：")
        if st.button("确认预约"):
            system.reserve_seat(sid, floor, area, stype, confirm)

    # 9 签到占座
    elif choice == "9 - 签到占座":
        sid = st.number_input("请输入座位编号(1~100)：", min_value=1, max_value=100)
        floor = st.number_input("请输入楼层(1~6)：", min_value=1, max_value=6)
        area = st.text_input("请输入区域（北区/南区/中区）：")
        stype = st.text_input("请选择座位类型（普通座/电脑座）：")
        if st.button("确认签到"):
            system.occupy_seat(sid, floor, area, stype)

    # 10 释放座位
    elif choice == "10 - 释放座位":
        sid = st.number_input("请输入要释放的座位编号(1~100)：", min_value=1, max_value=100)
        floor = st.number_input("请输入楼层(1~6)：", min_value=1, max_value=6)
        area = st.text_input("请输入区域（北区/南区/中区）：")
        stype = st.text_input("请选择座位类型（普通座/电脑座）：")
        if st.button("确认释放"):
            system.release_seat(sid, floor, area, stype)

    # 11 修改预约
    elif choice == "11 - 修改预约（更换座位）":
        old_sid = st.number_input("原座位编号(1~100)：", min_value=1, max_value=100)
        old_floor = st.number_input("原楼层(1~6)：", min_value=1, max_value=6)
        old_area = st.text_input("原区域：")
        old_type = st.text_input("原类型：")
        new_sid = st.number_input("新座位编号(1~100)：", min_value=1, max_value=100)
        new_floor = st.number_input("新楼层(1~6)：", min_value=1, max_value=6)
        new_area = st.text_input("新区域：")
        new_type = st.text_input("新类型：")
        if st.button("确认更换"):
            system.modify_seat(old_sid, old_floor, old_area, old_type, new_sid, new_floor, new_area, new_type)

    # 12 删除座位
    elif choice == "12 - 删除座位":
        sid = st.number_input("请输入要删除的座位编号(1~100)：", min_value=1, max_value=100)
        floor = st.number_input("请输入楼层(1~6)：", min_value=1, max_value=6)
        area = st.text_input("请输入区域（北区/南区/中区）：")
        stype = st.text_input("请选择座位类型（普通座/电脑座）：")
        confirm_del = st.text_input("确定要强制删除吗？(y/n)：")
        if st.button("确认删除"):
            system.delete_seat(sid, floor, area, stype, confirm_del)

    # 13 数据统计
    elif choice == "13 - 数据统计":
        system.statistics()

    # 14 保存数据
    elif choice == "14 - 保存数据":
        system._save_all()

if __name__ == "__main__":
    main()
