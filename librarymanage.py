import streamlit as st

import json
import os


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
            print(f"[警告] 用户文件 {self.user_file} 格式错误，将使用空数据。")
            return {}

    def save_users(self, users):

        data = {username: user.to_dict() for username, user in users.items()}
        with open(self.user_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"[系统] 用户数据已保存到 {self.user_file}")

    def load_seats(self):

        if not os.path.exists(self.seat_file):
            return []
        try:
            with open(self.seat_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [Seat.from_dict(info) for info in data]
        except (json.JSONDecodeError, KeyError):
            print(f"[警告] 座位文件 {self.seat_file} 格式错误，将使用空数据。")
            return []

    def save_seats(self, seats):

        data = [seat.to_dict() for seat in seats]
        with open(self.seat_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"[系统] 座位数据已保存到 {self.seat_file}")


# ==================== 图书馆管理系统类 ====================
class LibrarySystem:


    def __init__(self):


        self.file_manager = FileManager()  # 创建文件管理器实例，用于处理文件操作
        self.users = self.file_manager.load_users()   # {username: User}
        self.seats = self.file_manager.load_seats()   # [Seat]
        self.current_user = None
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


    def register(self):

        print("\n----- 用户注册 -----")
        username = input("请设置用户名：").strip()
        if not username:
            print("[错误] 用户名不能为空！")
            return False
        if username in self.users:
            print("[错误] 该用户名已被注册，请更换一个。")
            return False

        account = input("请设置账号：").strip()
        if not account:
            print("[错误] 账号不能为空！")
            return False

        password = input("请设置密码：").strip()
        if not password:
            print("[错误] 密码不能为空！")
            return False

        confirm_pwd = input("请确认密码：").strip()
        if password != confirm_pwd:
            print("[错误] 两次输入的密码不一致！")
            return False

        self.users[username] = User(username, account, password)
        self.file_manager.save_users(self.users)
        print(f"[成功] 用户 {username} 注册成功！")
        return True

    def login(self):

        print("\n----- 用户登录 -----")
        username = input("请输入用户名：").strip()
        if username not in self.users:
            print("[错误] 用户名不存在，请先注册。")
            return False

        account = input("请输入账号：").strip()
        password = input("请输入密码：").strip()

        user = self.users[username]
        if user.account == account and user.password == password:
            self.current_user = username
            print(f"[成功] 欢迎回来，{username}！")
            return True
        else:
            print("[错误] 账号或密码错误！")
            return False

    def logout(self):

        if self.current_user:
            print(f"[系统] 用户 {self.current_user} 已登出。")
            self.current_user = None
        else:
            print("[提示] 当前没有登录用户。")

    def show_user_info(self):

        if not self.current_user:
            print("[提示] 请先登录。")
            return
        user = self.users[self.current_user]
        print(f"\n----- 当前用户信息 -----")
        print(f"  用户名: {user.username}")
        print(f"  账  号: {user.account}")

        reserved_count = sum(1 for s in self.seats if s.reserved_by == self.current_user)
        print(f"  已预约座位数: {reserved_count}")


    def add_seat(self):

        print("\n----- 添加座位 -----")
        try:
            seat_id = int(input("请输入座位编号(1~100)："))
            floor = int(input("请输入楼层(1~6)："))
        except ValueError:
            print("[错误] 编号和楼层必须为数字！")
            return

        area = input("请输入区域（北区/南区/中区）：").strip()
        seat_type = input("请选择座位类型（普通座/电脑座）：").strip()

        valid, msg = self._validate_seat_input(seat_id, floor, area, seat_type)
        if not valid:
            print(f"[错误] {msg}")
            return

        if self._find_seat(seat_id, floor, area, seat_type):
            print("[错误] 该座位已存在，请勿重复添加。")
            return

        new_seat = Seat(seat_id, floor, area, seat_type)
        self.seats.append(new_seat)
        self.file_manager.save_seats(self.seats)
        print(f"[成功] 座位添加成功：{new_seat}")

    def show_seats(self):

        print("\n----- 座位列表 -----")
        if not self.seats:
            print("  （暂无座位数据）")
            return

        sorted_seats = sorted(self.seats, key=lambda s: (s.floor, s.area, s.seat_id))
        for seat in sorted_seats:
            print(f"  {seat}")

    def search_seats(self):

        print("\n----- 查询座位 -----")
        print("可按以下条件查询：")
        print("  1 - 按楼层查询")
        print("  2 - 按区域查询")
        print("  3 - 按类型查询")
        print("  4 - 按状态查询")
        print("  5 - 查询我预约的座位")
        choice = input("请选择查询方式：").strip()

        results = []
        if choice == "1":
            try:
                floor = int(input("请输入楼层(1~6)："))
                results = [s for s in self.seats if s.floor == floor]
            except ValueError:
                print("[错误] 楼层必须为数字。")
                return
        elif choice == "2":
            area = input("请输入区域（北区/南区/中区）：").strip()
            results = [s for s in self.seats if s.area == area]
        elif choice == "3":
            seat_type = input("请输入类型（普通座/电脑座）：").strip()
            results = [s for s in self.seats if s.seat_type == seat_type]
        elif choice == "4":
            status = input("请输入状态（空闲/已预约/已占用）：").strip()
            results = [s for s in self.seats if s.status == status]
        elif choice == "5":
            if not self.current_user:
                print("[提示] 请先登录。")
                return
            results = [s for s in self.seats if s.reserved_by == self.current_user]
        else:
            print("[错误] 无效选项。")
            return

        if not results:
            print("  未找到符合条件的座位。")
        else:
            for seat in results:
                print(f"  {seat}")

    def reserve_seat(self):

        if not self.current_user:
            print("[提示] 请先登录后再预约座位。")
            return

        print("\n----- 预约座位 -----")
        try:
            seat_id = int(input("请输入座位编号(1~100)："))
            floor = int(input("请输入楼层(1~6)："))
        except ValueError:
            print("[错误] 编号和楼层必须为数字！")
            return

        area = input("请输入区域（北区/南区/中区）：").strip()
        seat_type = input("请选择座位类型（普通座/电脑座）：").strip()

        seat = self._find_seat(seat_id, floor, area, seat_type)
        if not seat:
            print("[错误] 未找到该座位，请确认座位信息。")
            return

        if seat.status != "空闲":
            print(f"[错误] 该座位当前状态为「{seat.status}」，无法预约。")
            return

        user_reserved = [s for s in self.seats if s.reserved_by == self.current_user]
        if user_reserved:
            print(f"[提示] 您已预约了以下座位：")
            for s in user_reserved:
                print(f"  {s}")
            confirm = input("是否继续预约新座位？(y/n)：").strip().lower()
            if confirm != "y":
                print("[提示] 已取消预约。")
                return

        seat.reserve(self.current_user)
        self.file_manager.save_seats(self.seats)
        print(f"[成功] 预约成功！{seat}")

    def occupy_seat(self):

        if not self.current_user:
            print("[提示] 请先登录。")
            return

        print("\n----- 签到占座 -----")
        try:
            seat_id = int(input("请输入座位编号(1~100)："))
            floor = int(input("请输入楼层(1~6)："))
        except ValueError:
            print("[错误] 编号和楼层必须为数字！")
            return

        area = input("请输入区域（北区/南区/中区）：").strip()
        seat_type = input("请选择座位类型（普通座/电脑座）：").strip()

        seat = self._find_seat(seat_id, floor, area, seat_type)
        if not seat:
            print("[错误] 未找到该座位。")
            return

        if seat.status == "已占用":
            print("[错误] 该座位已被占用。")
            return

        if seat.reserved_by != self.current_user:
            print("[错误] 该座位不是您预约的，无法签到。")
            return

        seat.occupy(self.current_user)
        self.file_manager.save_seats(self.seats)
        print(f"[成功] 签到成功！{seat}")

    def release_seat(self):

        print("\n----- 释放座位 -----")
        try:
            seat_id = int(input("请输入要释放的座位编号(1~100)："))
            floor = int(input("请输入楼层(1~6)："))
        except ValueError:
            print("[错误] 编号和楼层必须为数字！")
            return

        area = input("请输入区域（北区/南区/中区）：").strip()
        seat_type = input("请选择座位类型（普通座/电脑座）：").strip()

        seat = self._find_seat(seat_id, floor, area, seat_type)
        if not seat:
            print("[错误] 未找到该座位。")
            return

        if seat.status == "空闲":
            print("[提示] 该座位已经是空闲状态，无需释放。")
            return

        if self.current_user and seat.reserved_by != self.current_user:
            print("[错误] 您只能释放自己预约的座位。")
            return

        seat.release()
        self.file_manager.save_seats(self.seats)
        print(f"[成功] 座位已释放：{seat}")

    def modify_seat(self):

        if not self.current_user:
            print("[提示] 请先登录。")
            return

        print("\n----- 修改预约（更换座位）-----")
        print("请输入原座位信息：")
        try:
            old_id = int(input("  原座位编号(1~100)："))
            old_floor = int(input("  原楼层(1~6)："))
        except ValueError:
            print("[错误] 编号和楼层必须为数字！")
            return

        old_area = input("  原区域（北区/南区/中区）：").strip()
        old_type = input("  原类型（普通座/电脑座）：").strip()

        old_seat = self._find_seat(old_id, old_floor, old_area, old_type)
        if not old_seat:
            print("[错误] 未找到原座位。")
            return

        if old_seat.reserved_by != self.current_user:
            print("[错误] 您只能修改自己预约的座位。")
            return

        print("请输入新座位信息：")
        try:
            new_id = int(input("  新座位编号(1~100)："))
            new_floor = int(input("  新楼层(1~6)："))
        except ValueError:
            print("[错误] 编号和楼层必须为数字！")
            return

        new_area = input("  新区域（北区/南区/中区）：").strip()
        new_type = input("  新类型（普通座/电脑座）：").strip()

        new_seat = self._find_seat(new_id, new_floor, new_area, new_type)
        if not new_seat:
            print("[错误] 未找到新座位，请确认座位信息。")
            return

        if new_seat.status != "空闲":
            print(f"[错误] 新座位当前状态为「{new_seat.status}」，无法预约。")
            return


        old_seat.release()
        new_seat.reserve(self.current_user)
        self.file_manager.save_seats(self.seats)
        print(f"[成功] 已将预约从 {old_floor}楼{old_area}{old_type}#{old_id} 更换为 {new_seat}")

    def delete_seat(self):

        print("\n----- 删除座位 -----")
        try:
            seat_id = int(input("请输入要删除的座位编号(1~100)："))
            floor = int(input("请输入楼层(1~6)："))
        except ValueError:
            print("[错误] 编号和楼层必须为数字！")
            return

        area = input("请输入区域（北区/南区/中区）：").strip()
        seat_type = input("请选择座位类型（普通座/电脑座）：").strip()

        seat = self._find_seat(seat_id, floor, area, seat_type)
        if not seat:
            print("[错误] 未找到该座位。")
            return

        if seat.status != "空闲":
            print(f"[警告] 该座位当前状态为「{seat.status}」，仍有用户在使用！")
            confirm = input("确定要强制删除吗？(y/n)：").strip().lower()
            if confirm != "y":
                print("[提示] 已取消删除。")
                return

        self.seats.remove(seat)
        self.file_manager.save_seats(self.seats)
        print(f"[成功] 座位已删除：{floor}楼{area}{seat_type}#{seat_id}")

    def statistics(self):

        print("\n===== 数据统计 =====")
        total = len(self.seats)
        free = sum(1 for s in self.seats if s.status == "空闲")
        reserved = sum(1 for s in self.seats if s.status == "已预约")
        occupied = sum(1 for s in self.seats if s.status == "已占用")

        print(f"  座位总数: {total}")
        print(f"  空闲座位: {free}")
        print(f"  已预约:   {reserved}")
        print(f"  已占用:   {occupied}")
        print(f"  使用率:   {((reserved + occupied) / total * 100):.1f}%" if total > 0 else "  使用率:   N/A")

        if total > 0:
            print("\n  --- 按楼层统计 ---")
            for floor in sorted(set(s.floor for s in self.seats)):
                floor_seats = [s for s in self.seats if s.floor == floor]
                floor_used = sum(1 for s in floor_seats if s.status != "空闲")
                print(f"  {floor}楼: 共{len(floor_seats)}个座位, 已使用{floor_used}个")

        if total > 0:
            print("\n  --- 按类型统计 ---")
            for seat_type in Seat.VALID_TYPES:
                type_seats = [s for s in self.seats if s.seat_type == seat_type]
                type_used = sum(1 for s in type_seats if s.status != "空闲")
                print(f"  {seat_type}: 共{len(type_seats)}个, 已使用{type_used}个")

        if total > 0:
            print("\n  --- 按区域统计 ---")
            for area in Seat.VALID_AREAS:
                area_seats = [s for s in self.seats if s.area == area]
                area_used = sum(1 for s in area_seats if s.status != "空闲")
                print(f"  {area}: 共{len(area_seats)}个, 已使用{area_used}个")

        print(f"\n  注册用户总数: {len(self.users)}")
        print("=====================")

    def show_main_menu(self):

        print("\n" + "=" * 40)
        print("       图书馆座位预约管理系统")
        print("=" * 40)
        if self.current_user:
            print(f"  当前用户: {self.current_user}")
        else:
            print("  当前用户: 未登录")
        print("-" * 40)
        print("  【用户管理】")
        print("    1 - 用户注册")
        print("    2 - 用户登录")
        print("    3 - 用户登出")
        print("    4 - 查看个人信息")
        print("  【座位管理】")
        print("    5 - 添加座位")
        print("    6 - 显示所有座位")
        print("    7 - 查询座位")
        print("    8 - 预约座位")
        print("    9 - 签到占座")
        print("    10 - 释放座位")
        print("    11 - 修改预约（更换座位）")
        print("    12 - 删除座位")
        print("  【系统功能】")
        print("    13 - 数据统计")
        print("    14 - 保存数据")
        print("    0 - 退出系统")
        print("=" * 40)

    def run(self):

        print("欢迎使用图书馆座位预约管理系统！")
        # 启动时自动加载已有数据
        print(f"[系统] 已加载 {len(self.users)} 个用户, {len(self.seats)} 个座位。")

        while True:
            self.show_main_menu()
            choice = input("请输入选项：").strip()

            if choice == "0":

                self._save_all()
                print("感谢使用，再见！")
                break
            elif choice == "1":
                self.register()
            elif choice == "2":
                self.login()
            elif choice == "3":
                self.logout()
            elif choice == "4":
                self.show_user_info()
            elif choice == "5":
                self.add_seat()
            elif choice == "6":
                self.show_seats()
            elif choice == "7":
                self.search_seats()
            elif choice == "8":
                self.reserve_seat()
            elif choice == "9":
                self.occupy_seat()
            elif choice == "10":
                self.release_seat()
            elif choice == "11":
                self.modify_seat()
            elif choice == "12":
                self.delete_seat()
            elif choice == "13":
                self.statistics()
            elif choice == "14":
                self._save_all()
            else:
                print("[错误] 无效选项，请重新输入。")

if __name__ == "__main__":
    system = LibrarySystem()
    system.run()
