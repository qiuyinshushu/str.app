import streamlit as st
import json
import os

# ==================== 全局样式优化（提升高级感） ====================
def set_custom_style():
    st.markdown("""
    <style>
    /* 整体样式 */
    .main {
        padding: 2rem;
        background-color: #f8f9fa;
    }
    /* 标题样式 */
    h1 {
        color: #2c3e50;
        text-align: center;
        font-weight: 700;
        margin-bottom: 2rem;
    }
    /* 卡片容器 */
    .card {
        background-color: white;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 1.5rem;
    }
    /* 按钮样式 */
    div.stButton > button {
        background-color: #3498db;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        transition: all 0.2s;
    }
    div.stButton > button:hover {
        background-color: #2980b9;
        transform: translateY(-2px);
    }
    /* 提示文本样式 */
    .status-text {
        padding: 0.8rem;
        border-radius: 6px;
        margin: 1rem 0;
    }
    /* 分隔线 */
    .divider {
        height: 2px;
        background-color: #eee;
        margin: 1.5rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

# ==================== 初始化会话状态 ====================
def init_session_state():
    # 登录状态
    if "current_user" not in st.session_state:
        st.session_state.current_user = None
    # 当前选中的功能（用于自动返回菜单）
    if "selected_func" not in st.session_state:
        st.session_state.selected_func = "请选择功能"
    # 功能执行状态（用于自动重置）
    if "func_executed" not in st.session_state:
        st.session_state.func_executed = False

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
    # ✅ 修改：座位编号范围扩大到1-3600（6楼×3区×200个座位）
    VALID_SEAT_IDS = range(1, 3601)
    
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
            st.markdown('<div class="status-text" style="background-color: #fff3cd;">[警告] 用户文件格式错误，将使用空数据。</div>', unsafe_allow_html=True)
            return {}
    def save_users(self, users):
        data = {username: user.to_dict() for username, user in users.items()}
        with open(self.user_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        st.markdown(f'<div class="status-text" style="background-color: #d4edda;">[系统] 用户数据已保存到 {self.user_file}</div>', unsafe_allow_html=True)
    def load_seats(self):
        if not os.path.exists(self.seat_file):
            return []
        try:
            with open(self.seat_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [Seat.from_dict(info) for info in data]
        except (json.JSONDecodeError, KeyError):
            st.markdown('<div class="status-text" style="background-color: #fff3cd;">[警告] 座位文件格式错误，将使用空数据。</div>', unsafe_allow_html=True)
            return []
    def save_seats(self, seats):
        data = [seat.to_dict() for seat in seats]
        with open(self.seat_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        st.markdown(f'<div class="status-text" style="background-color: #d4edda;">[系统] 座位数据已保存到 {self.seat_file}</div>', unsafe_allow_html=True)

# ==================== 图书馆管理系统类 ====================
class LibrarySystem:
    def __init__(self):
        self.file_manager = FileManager()
        self.users = self.file_manager.load_users()
        self.seats = self.file_manager.load_seats()
        self.current_user = st.session_state.current_user
        
        # 自动生成默认座位（第一次运行时执行）
        if not self.seats:
            self._generate_default_seats()
            self.file_manager.save_seats(self.seats)
            st.markdown('<div class="status-text" style="background-color: #d4edda;">[系统] 已自动生成1-6楼所有默认座位（共3600个）</div>', unsafe_allow_html=True)

    # ✅ 完全按照你的要求重写：每层3区，每区100普通+100电脑
    def _generate_default_seats(self):
        """自动生成1-6楼、南北中区、每区100个普通座+100个电脑座"""
        seat_id = 1
        # 遍历1-6楼
        for floor in Seat.VALID_FLOORS:
            # 遍历三个区域（北区、中区、南区）
            for area in Seat.VALID_AREAS:
                # 每个区域生成100个普通座
                for _ in range(100):
                    self.seats.append(Seat(seat_id, floor, area, "普通座"))
                    seat_id += 1
                # 每个区域生成100个电脑座
                for _ in range(100):
                    self.seats.append(Seat(seat_id, floor, area, "电脑座"))
                    seat_id += 1
        # 总座位数：6楼 × 3区 × 200个 = 3600个

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
            return False, "座位编号必须在1~3600之间。"
        if floor not in Seat.VALID_FLOORS:
            return False, "楼层必须在1~6之间。"
        if area not in Seat.VALID_AREAS:
            return False, "区域必须为北区、南区或中区。"
        if seat_type not in Seat.VALID_TYPES:
            return False, "座位类型必须为普通座或电脑座。"
        return True, ""

    def register(self, username, account, password, confirm_pwd):
        st.markdown("<h4>用户注册</h4>", unsafe_allow_html=True)
        if not username:
            st.markdown('<div class="status-text" style="background-color: #f8d7da;">[错误] 用户名不能为空！</div>', unsafe_allow_html=True)
            return False
        if username in self.users:
            st.markdown('<div class="status-text" style="background-color: #f8d7da;">[错误] 该用户名已被注册，请更换一个。</div>', unsafe_allow_html=True)
            return False
        if not account:
            st.markdown('<div class="status-text" style="background-color: #f8d7da;">[错误] 账号不能为空！</div>', unsafe_allow_html=True)
            return False
        if not password:
            st.markdown('<div class="status-text" style="background-color: #f8d7da;">[错误] 密码不能为空！</div>', unsafe_allow_html=True)
            return False
        if password != confirm_pwd:
            st.markdown('<div class="status-text" style="background-color: #f8d7da;">[错误] 两次输入的密码不一致！</div>', unsafe_allow_html=True)
            return False
        self.users[username] = User(username, account, password)
        self.file_manager.save_users(self.users)
        st.markdown(f'<div class="status-text" style="background-color: #d4edda;">[成功] 用户 {username} 注册成功！</div>', unsafe_allow_html=True)
        return True

    def login(self, username, account, password):
        st.markdown("<h4>用户登录</h4>", unsafe_allow_html=True)
        if username not in self.users:
            st.markdown('<div class="status-text" style="background-color: #f8d7da;">[错误] 用户名不存在，请先注册。</div>', unsafe_allow_html=True)
            return False
        user = self.users[username]
        if user.account == account and user.password == password:
            self.current_user = username
            st.session_state.current_user = username
            st.markdown(f'<div class="status-text" style="background-color: #d4edda;">[成功] 欢迎回来，{username}！</div>', unsafe_allow_html=True)
            # 登录成功后重置菜单选择
            st.session_state.selected_func = "请选择功能"
            return True
        else:
            st.markdown('<div class="status-text" style="background-color: #f8d7da;">[错误] 账号或密码错误！</div>', unsafe_allow_html=True)
            return False

    def logout(self):
        if self.current_user:
            st.markdown(f'<div class="status-text" style="background-color: #d4edda;">[系统] 用户 {self.current_user} 已登出。</div>', unsafe_allow_html=True)
            self.current_user = None
            st.session_state.current_user = None
        else:
            st.markdown('<div class="status-text" style="background-color: #fff3cd;">[提示] 当前没有登录用户。</div>', unsafe_allow_html=True)
        # 登出后重置菜单
        st.session_state.selected_func = "请选择功能"

    def show_user_info(self):
        if not self.current_user:
            st.markdown('<div class="status-text" style="background-color: #fff3cd;">[提示] 请先登录。</div>', unsafe_allow_html=True)
            return
        st.markdown("<h4>当前用户信息</h4>", unsafe_allow_html=True)
        user = self.users[self.current_user]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write(f"**用户名**: {user.username}")
        with col2:
            st.write(f"**账号**: {user.account}")
        with col3:
            reserved_count = sum(1 for s in self.seats if s.reserved_by == self.current_user)
            st.write(f"**已预约座位数**: {reserved_count}")

    def add_seat(self, seat_id, floor, area, seat_type):
        st.markdown("<h4>添加座位</h4>", unsafe_allow_html=True)
        valid, msg = self._validate_seat_input(seat_id, floor, area, seat_type)
        if not valid:
            st.markdown(f'<div class="status-text" style="background-color: #f8d7da;">[错误] {msg}</div>', unsafe_allow_html=True)
            return
        if self._find_seat(seat_id, floor, area, seat_type):
            st.markdown('<div class="status-text" style="background-color: #f8d7da;">[错误] 该座位已存在，请勿重复添加。</div>', unsafe_allow_html=True)
            return
        new_seat = Seat(seat_id, floor, area, seat_type)
        self.seats.append(new_seat)
        self.file_manager.save_seats(self.seats)
        st.markdown(f'<div class="status-text" style="background-color: #d4edda;">[成功] 座位添加成功：{new_seat}</div>', unsafe_allow_html=True)

    def show_seats(self):
        st.markdown("<h4>座位列表</h4>", unsafe_allow_html=True)
        if not self.seats:
            st.markdown('<div class="status-text" style="background-color: #fff3cd;">（暂无座位数据）</div>', unsafe_allow_html=True)
            return
        sorted_seats = sorted(self.seats, key=lambda s: (s.floor, s.area, s.seat_id))
        # 用卡片展示座位信息
        for idx, seat in enumerate(sorted_seats):
            with st.container():
                st.markdown(f"""
                <div class="card">
                    <p>{seat}</p>
                </div>
                """, unsafe_allow_html=True)
                if idx < len(sorted_seats)-1:
                    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    def search_seats(self, choice, floor_in, area_in, type_in, status_in):
        st.markdown("<h4>查询座位</h4>", unsafe_allow_html=True)
        query_tips = {
            "1": "按楼层查询",
            "2": "按区域查询",
            "3": "按类型查询",
            "4": "按状态查询",
            "5": "查询我预约的座位"
        }
        st.write(f"当前查询方式：{query_tips.get(choice, '无效选项')}")
        
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
                st.markdown('<div class="status-text" style="background-color: #fff3cd;">[提示] 请先登录。</div>', unsafe_allow_html=True)
                return
            results = [s for s in self.seats if s.reserved_by == self.current_user]
        else:
            st.markdown('<div class="status-text" style="background-color: #f8d7da;">[错误] 无效选项。</div>', unsafe_allow_html=True)
            return
        
        if not results:
            st.markdown('<div class="status-text" style="background-color: #fff3cd;">未找到符合条件的座位。</div>', unsafe_allow_html=True)
        else:
            for seat in results:
                st.markdown(f"""
                <div class="card">
                    <p>{seat}</p>
                </div>
                """, unsafe_allow_html=True)

    def reserve_seat(self, seat_id, floor, area, seat_type, confirm_choice):
        if not self.current_user:
            st.markdown('<div class="status-text" style="background-color: #fff3cd;">[提示] 请先登录后再预约座位。</div>', unsafe_allow_html=True)
            return
        st.markdown("<h4>预约座位</h4>", unsafe_allow_html=True)
        seat = self._find_seat(seat_id, floor, area, seat_type)
        if not seat:
            st.markdown('<div class="status-text" style="background-color: #f8d7da;">[错误] 未找到该座位，请确认座位信息。</div>', unsafe_allow_html=True)
            return
        if seat.status != "空闲":
            st.markdown(f'<div class="status-text" style="background-color: #f8d7da;">[错误] 该座位当前状态为「{seat.status}」，无法预约。</div>', unsafe_allow_html=True)
            return
        user_reserved = [s for s in self.seats if s.reserved_by == self.current_user]
        if user_reserved:
            st.markdown('<div class="status-text" style="background-color: #fff3cd;">[提示] 您已预约了以下座位：</div>', unsafe_allow_html=True)
            for s in user_reserved:
                st.write(f"  {s}")
            if confirm_choice != "y":
                st.markdown('<div class="status-text" style="background-color: #fff3cd;">[提示] 已取消预约。</div>', unsafe_allow_html=True)
                return
        seat.reserve(self.current_user)
        self.file_manager.save_seats(self.seats)
        st.markdown(f'<div class="status-text" style="background-color: #d4edda;">[成功] 预约成功！{seat}</div>', unsafe_allow_html=True)

    def occupy_seat(self, seat_id, floor, area, seat_type):
        if not self.current_user:
            st.markdown('<div class="status-text" style="background-color: #fff3cd;">[提示] 请先登录。</div>', unsafe_allow_html=True)
            return
        st.markdown("<h4>签到占座</h4>", unsafe_allow_html=True)
        seat = self._find_seat(seat_id, floor, area, seat_type)
        if not seat:
            st.markdown('<div class="status-text" style="background-color: #f8d7da;">[错误] 未找到该座位。</div>', unsafe_allow_html=True)
            return
        if seat.status == "已占用":
            st.markdown('<div class="status-text" style="background-color: #f8d7da;">[错误] 该座位已被占用。</div>', unsafe_allow_html=True)
            return
        if seat.reserved_by != self.current_user:
            st.markdown('<div class="status-text" style="background-color: #f8d7da;">[错误] 该座位不是您预约的，无法签到。</div>', unsafe_allow_html=True)
            return
        seat.occupy(self.current_user)
        self.file_manager.save_seats(self.seats)
        st.markdown(f'<div class="status-text" style="background-color: #d4edda;">[成功] 签到成功！{seat}</div>', unsafe_allow_html=True)

    def release_seat(self, seat_id, floor, area, seat_type):
        st.markdown("<h4>释放座位</h4>", unsafe_allow_html=True)
        seat = self._find_seat(seat_id, floor, area, seat_type)
        if not seat:
            st.markdown('<div class="status-text" style="background-color: #f8d7da;">[错误] 未找到该座位。</div>', unsafe_allow_html=True)
            return
        if seat.status == "空闲":
            st.markdown('<div class="status-text" style="background-color: #fff3cd;">[提示] 该座位已经是空闲状态，无需释放。</div>', unsafe_allow_html=True)
            return
        if self.current_user and seat.reserved_by != self.current_user:
            st.markdown('<div class="status-text" style="background-color: #f8d7da;">[错误] 您只能释放自己预约的座位。</div>', unsafe_allow_html=True)
            return
        seat.release()
        self.file_manager.save_seats(self.seats)
        st.markdown(f'<div class="status-text" style="background-color: #d4edda;">[成功] 座位已释放：{seat}</div>', unsafe_allow_html=True)

    def modify_seat(self, old_id, old_floor, old_area, old_type, new_id, new_floor, new_area, new_type):
        if not self.current_user:
            st.markdown('<div class="status-text" style="background-color: #fff3cd;">[提示] 请先登录。</div>', unsafe_allow_html=True)
            return
        st.markdown("<h4>修改预约（更换座位）</h4>", unsafe_allow_html=True)
        old_seat = self._find_seat(old_id, old_floor, old_area, old_type)
        if not old_seat:
            st.markdown('<div class="status-text" style="background-color: #f8d7da;">[错误] 未找到原座位。</div>', unsafe_allow_html=True)
            return
        if old_seat.reserved_by != self.current_user:
            st.markdown('<div class="status-text" style="background-color: #f8d7da;">[错误] 您只能修改自己预约的座位。</div>', unsafe_allow_html=True)
            return
        
        new_seat = self._find_seat(new_id, new_floor, new_area, new_type)
        if not new_seat:
            st.markdown('<div class="status-text" style="background-color: #f8d7da;">[错误] 未找到新座位，请确认座位信息。</div>', unsafe_allow_html=True)
            return
        if new_seat.status != "空闲":
            st.markdown(f'<div class="status-text" style="background-color: #f8d7da;">[错误] 新座位当前状态为「{new_seat.status}」，无法预约。</div>', unsafe_allow_html=True)
            return
        
        old_seat.release()
        new_seat.reserve(self.current_user)
        self.file_manager.save_seats(self.seats)
        st.markdown(f'<div class="status-text" style="background-color: #d4edda;">[成功] 已将预约从 {old_floor}楼{old_area}{old_type}#{old_id} 更换为 {new_seat}</div>', unsafe_allow_html=True)

    def delete_seat(self, seat_id, floor, area, seat_type, confirm_del):
        st.markdown("<h4>删除座位</h4>", unsafe_allow_html=True)
        seat = self._find_seat(seat_id, floor, area, seat_type)
        if not seat:
            st.markdown('<div class="status-text" style="background-color: #f8d7da;">[错误] 未找到该座位。</div>', unsafe_allow_html=True)
            return
        if seat.status != "空闲":
            st.markdown(f'<div class="status-text" style="background-color: #fff3cd;">[警告] 该座位当前状态为「{seat.status}」，仍有用户在使用！</div>', unsafe_allow_html=True)
            if confirm_del != "y":
                st.markdown('<div class="status-text" style="background-color: #fff3cd;">[提示] 已取消删除。</div>', unsafe_allow_html=True)
                return
        self.seats.remove(seat)
        self.file_manager.save_seats(self.seats)
        st.markdown(f'<div class="status-text" style="background-color: #d4edda;">[成功] 座位已删除：{floor}楼{area}{seat_type}#{seat_id}</div>', unsafe_allow_html=True)

    def statistics(self):
        st.markdown("<h4>数据统计</h4>", unsafe_allow_html=True)
        total = len(self.seats)
        free = sum(1 for s in self.seats if s.status == "空闲")
        reserved = sum(1 for s in self.seats if s.status == "已预约")
        occupied = sum(1 for s in self.seats if s.status == "已占用")
        
        # 统计卡片布局
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="card">
                <h5>座位总数</h5>
                <p style="font-size: 2rem; font-weight: 700;">{total}</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="card">
                <h5>空闲座位</h5>
                <p style="font-size: 2rem; font-weight: 700; color: #28a745;">{free}</p>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="card">
                <h5>已预约</h5>
                <p style="font-size: 2rem; font-weight: 700; color: #ffc107;">{reserved}</p>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class="card">
                <h5>已占用</h5>
                <p style="font-size: 2rem; font-weight: 700; color: #dc3545;">{occupied}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # 使用率
        if total > 0:
            usage_rate = ((reserved + occupied) / total * 100)
            st.markdown(f"""
            <div class="card">
                <h5>座位使用率</h5>
                <p style="font-size: 1.5rem; font-weight: 700;">{usage_rate:.1f}%</p>
            </div>
            """, unsafe_allow_html=True)
            
            # 按楼层/类型/区域统计
            st.markdown("<h5>按维度统计</h5>", unsafe_allow_html=True)
            tab1, tab2, tab3 = st.tabs(["楼层", "类型", "区域"])
            
            with tab1:
                for floor in sorted(set(s.floor for s in self.seats)):
                    floor_seats = [s for s in self.seats if s.floor == floor]
                    floor_used = sum(1 for s in floor_seats if s.status != "空闲")
                    st.write(f"**{floor}楼**: 共{len(floor_seats)}个座位, 已使用{floor_used}个")
            
            with tab2:
                for seat_type in Seat.VALID_TYPES:
                    type_seats = [s for s in self.seats if s.seat_type == seat_type]
                    type_used = sum(1 for s in type_seats if s.status != "空闲")
                    st.write(f"**{seat_type}**: 共{len(type_seats)}个, 已使用{type_used}个")
            
            with tab3:
                for area in Seat.VALID_AREAS:
                    area_seats = [s for s in self.seats if s.area == area]
                    area_used = sum(1 for s in area_seats if s.status != "空闲")
                    st.write(f"**{area}**: 共{len(area_seats)}个, 已使用{area_used}个")
        
        # 用户统计
        st.markdown(f"""
        <div class="card">
            <h5>注册用户总数</h5>
            <p style="font-size: 1.5rem; font-weight: 700;">{len(self.users)}</p>
        </div>
        """, unsafe_allow_html=True)

# ==================== 主程序 ====================
def main():
    # 初始化
    init_session_state()
    set_custom_style()
    
    # 页面标题
    st.title("📚 图书馆座位预约管理系统")
    
    # 加载系统
    system = LibrarySystem()
    
    # 登录状态提示
    if st.session_state.current_user:
        st.sidebar.markdown(f"""
        <div class="card">
            <h4>👤 当前登录</h4>
            <p>{st.session_state.current_user}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.sidebar.markdown("""
        <div class="card">
            <h4>🔒 未登录状态</h4>
            <p>请先登录以使用完整功能</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 菜单逻辑：未登录只显示1/2，登录后显示其他功能
    if not st.session_state.current_user:
        menu_list = [
            "请选择功能",
            "1 - 用户注册",
            "2 - 用户登录"
        ]
    else:
        menu_list = [
            "请选择功能",
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
    
    # 功能选择（自动重置逻辑）
    if st.session_state.func_executed:
        st.session_state.selected_func = "请选择功能"
        st.session_state.func_executed = False
    
    # 功能选择下拉框
    st.session_state.selected_func = st.selectbox(
        "🔍 请选择功能选项",
        menu_list,
        index=menu_list.index(st.session_state.selected_func)
    )
    
    # 分隔线
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    # 功能执行区域（卡片化）
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        
        # 0 退出逻辑（整合到刷新/关闭）
        # 1 用户注册
        if st.session_state.selected_func == "1 - 用户注册":
            uname = st.text_input("请设置用户名：", key="reg_uname")
            acc = st.text_input("请设置账号：", key="reg_acc")
            pwd = st.text_input("请设置密码：", type="password", key="reg_pwd")
            cpwd = st.text_input("请确认密码：", type="password", key="reg_cpwd")
            if st.button("提交注册"):
                system.register(uname, acc, pwd, cpwd)
                st.session_state.func_executed = True
                st.rerun()
        
        # 2 用户登录
        elif st.session_state.selected_func == "2 - 用户登录":
            uname = st.text_input("请输入用户名：", key="login_uname")
            acc = st.text_input("请输入账号：", key="login_acc")
            pwd = st.text_input("请输入密码：", type="password", key="login_pwd")
            if st.button("登录"):
                system.login(uname, acc, pwd)
                st.session_state.func_executed = True
                st.rerun()
        
        # 3 用户登出
        elif st.session_state.selected_func == "3 - 用户登出":
            if st.button("确认登出"):
                system.logout()
                st.session_state.func_executed = True
                st.rerun()
        
        # 4 查看个人信息
        elif st.session_state.selected_func == "4 - 查看个人信息":
            system.show_user_info()
            if st.button("返回菜单"):
                st.session_state.func_executed = True
                st.rerun()
        
        # 5 添加座位
        elif st.session_state.selected_func == "5 - 添加座位":
            sid = st.number_input("请输入座位编号(1~3600)：", min_value=1, max_value=3600, key="add_sid")
            floor = st.number_input("请输入楼层(1~6)：", min_value=1, max_value=6, key="add_floor")
            area = st.selectbox("请选择区域：", Seat.VALID_AREAS, key="add_area")
            stype = st.selectbox("请选择座位类型：", Seat.VALID_TYPES, key="add_type")
            if st.button("确认添加"):
                system.add_seat(sid, floor, area, stype)
                st.session_state.func_executed = True
                st.rerun()
        
        # 6 显示所有座位
        elif st.session_state.selected_func == "6 - 显示所有座位":
            system.show_seats()
            if st.button("返回菜单"):
                st.session_state.func_executed = True
                st.rerun()
        
        # 7 查询座位
        elif st.session_state.selected_func == "7 - 查询座位":
            q_choice = st.selectbox(
                "选择查询方式", 
                ["1","2","3","4","5"],
                format_func=lambda x: {
                    "1":"按楼层", "2":"按区域", "3":"按类型", 
                    "4":"按状态", "5":"我的预约"
                }[x],
                key="q_choice"
            )
            col1, col2 = st.columns(2)
            with col1:
                f = st.number_input("楼层(1~6)：", min_value=1, max_value=6, key="q_floor")
                a = st.selectbox("区域：", [""] + Seat.VALID_AREAS, key="q_area")
            with col2:
                t = st.selectbox("座位类型：", [""] + Seat.VALID_TYPES, key="q_type")
                s = st.selectbox("状态：", ["", "空闲", "已预约", "已占用"], key="q_status")
            
            if st.button("执行查询"):
                system.search_seats(q_choice, f, a, t, s)
            if st.button("返回菜单", key="q_back"):
                st.session_state.func_executed = True
                st.rerun()
        
        # 8 预约座位
        elif st.session_state.selected_func == "8 - 预约座位":
            sid = st.number_input("请输入座位编号(1~3600)：", min_value=1, max_value=3600, key="res_sid")
            floor = st.number_input("请输入楼层(1~6)：", min_value=1, max_value=6, key="res_floor")
            area = st.selectbox("请选择区域：", Seat.VALID_AREAS, key="res_area")
            stype = st.selectbox("请选择座位类型：", Seat.VALID_TYPES, key="res_type")
            confirm = st.selectbox("是否继续预约新座位？", ["", "y", "n"], key="res_confirm")
            if st.button("确认预约"):
                system.reserve_seat(sid, floor, area, stype, confirm)
                st.session_state.func_executed = True
                st.rerun()
        
        # 9 签到占座
        elif st.session_state.selected_func == "9 - 签到占座":
            sid = st.number_input("请输入座位编号(1~3600)：", min_value=1, max_value=3600, key="occ_sid")
            floor = st.number_input("请输入楼层(1~6)：", min_value=1, max_value=6, key="occ_floor")
            area = st.selectbox("请选择区域：", Seat.VALID_AREAS, key="occ_area")
            stype = st.selectbox("请选择座位类型：", Seat.VALID_TYPES, key="occ_type")
            if st.button("确认签到"):
                system.occupy_seat(sid, floor, area, stype)
                st.session_state.func_executed = True
                st.rerun()
        
        # 10 释放座位
        elif st.session_state.selected_func == "10 - 释放座位":
            sid = st.number_input("请输入要释放的座位编号(1~3600)：", min_value=1, max_value=3600, key="rel_sid")
            floor = st.number_input("请输入楼层(1~6)：", min_value=1, max_value=6, key="rel_floor")
            area = st.selectbox("请选择区域：", Seat.VALID_AREAS, key="rel_area")
            stype = st.selectbox("请选择座位类型：", Seat.VALID_TYPES, key="rel_type")
            if st.button("确认释放"):
                system.release_seat(sid, floor, area, stype)
                st.session_state.func_executed = True
                st.rerun()
        
        # 11 修改预约
        elif st.session_state.selected_func == "11 - 修改预约（更换座位）":
            st.markdown("<h6>原座位信息</h6>", unsafe_allow_html=True)
            old_sid = st.number_input("原座位编号：", min_value=1, max_value=3600, key="mod_old_sid")
            old_floor = st.number_input("原楼层：", min_value=1, max_value=6, key="mod_old_floor")
            old_area = st.selectbox("原区域：", Seat.VALID_AREAS, key="mod_old_area")
            old_type = st.selectbox("原类型：", Seat.VALID_TYPES, key="mod_old_type")
            
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            
            st.markdown("<h6>新座位信息</h6>", unsafe_allow_html=True)
            new_sid = st.number_input("新座位编号：", min_value=1, max_value=3600, key="mod_new_sid")
            new_floor = st.number_input("新楼层：", min_value=1, max_value=6, key="mod_new_floor")
            new_area = st.selectbox("新区域：", Seat.VALID_AREAS, key="mod_new_area")
            new_type = st.selectbox("新类型：", Seat.VALID_TYPES, key="mod_new_type")
            
            if st.button("确认更换"):
                system.modify_seat(old_sid, old_floor, old_area, old_type, new_sid, new_floor, new_area, new_type)
                st.session_state.func_executed = True
                st.rerun()
        
        # 12 删除座位
        elif st.session_state.selected_func == "12 - 删除座位":
            sid = st.number_input("请输入要删除的座位编号(1~3600)：", min_value=1, max_value=3600, key="del_sid")
            floor = st.number_input("请输入楼层(1~6)：", min_value=1, max_value=6, key="del_floor")
            area = st.selectbox("请选择区域：", Seat.VALID_AREAS, key="del_area")
            stype = st.selectbox("请选择座位类型：", Seat.VALID_TYPES, key="del_type")
            confirm_del = st.selectbox("确定要强制删除吗？", ["", "y", "n"], key="del_confirm")
            if st.button("确认删除"):
                system.delete_seat(sid, floor, area, stype, confirm_del)
                st.session_state.func_executed = True
                st.rerun()
        
        # 13 数据统计
        elif st.session_state.selected_func == "13 - 数据统计":
            system.statistics()
            if st.button("返回菜单", key="stat_back"):
                st.session_state.func_executed = True
                st.rerun()
        
        # 14 保存数据
        elif st.session_state.selected_func == "14 - 保存数据":
            if st.button("确认保存所有数据"):
                system._save_all()
                st.session_state.func_executed = True
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
