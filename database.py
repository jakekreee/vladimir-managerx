import sqlite3
import time

class Database:
    def __init__(self, db_file="bot_data.db"):
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.cur = self.conn.cursor()
        self._init_db()

    def _init_db(self):
        # Таблица пользователей
        self.cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER,
                chat_id INTEGER,
                role TEXT DEFAULT 'user',
                nickname TEXT,
                warn_count INTEGER DEFAULT 0,
                mute_until INTEGER DEFAULT 0,
                ban_until INTEGER DEFAULT 0,
                admin_blocked INTEGER DEFAULT 0,
                message_count INTEGER DEFAULT 0,
                last_message_time INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, chat_id)
            )
        ''')
        # Таблица глобальных банов
        self.cur.execute('''
            CREATE TABLE IF NOT EXISTS global_bans (
                user_id INTEGER,
                ban_until INTEGER DEFAULT 0,
                PRIMARY KEY (user_id)
            )
        ''')
        # Таблица групп
        self.cur.execute('''
            CREATE TABLE IF NOT EXISTS groups (
                group_id INTEGER PRIMARY KEY,
                owner_id INTEGER
            )
        ''')
        # Таблица чатов
        self.cur.execute('''
            CREATE TABLE IF NOT EXISTS chats (
                chat_id INTEGER PRIMARY KEY,
                group_id INTEGER,
                active INTEGER DEFAULT 1,
                log_enabled INTEGER DEFAULT 0
            )
        ''')
        # Таблица логов
        self.cur.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                user_id INTEGER,
                action TEXT,
                timestamp INTEGER
            )
        ''')
        # Таблица банов (история)
        self.cur.execute('''
            CREATE TABLE IF NOT EXISTS bans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                chat_id INTEGER,
                moderator_id INTEGER,
                reason TEXT,
                issued_at INTEGER,
                expire_at INTEGER,
                is_global INTEGER DEFAULT 0
            )
        ''')
        self.conn.commit()

    # ==================== ПОЛЬЗОВАТЕЛИ ====================
    def get_user(self, user_id, chat_id):
        self.cur.execute('SELECT * FROM users WHERE user_id=? AND chat_id=?', (user_id, chat_id))
        return self.cur.fetchone()

    def set_role(self, user_id, chat_id, role):
        if self.get_user(user_id, chat_id) is None:
            self.cur.execute('INSERT INTO users (user_id, chat_id) VALUES (?, ?)', (user_id, chat_id))
        self.cur.execute('UPDATE users SET role=? WHERE user_id=? AND chat_id=?', (role, user_id, chat_id))
        self.conn.commit()

    def get_role(self, user_id, chat_id):
        res = self.get_user(user_id, chat_id)
        return res[2] if res else 'user'

    def set_nickname(self, user_id, chat_id, nickname):
        if self.get_user(user_id, chat_id) is None:
            self.cur.execute('INSERT INTO users (user_id, chat_id) VALUES (?, ?)', (user_id, chat_id))
        self.cur.execute('UPDATE users SET nickname=? WHERE user_id=? AND chat_id=?', (nickname, user_id, chat_id))
        self.conn.commit()

    def get_nickname(self, user_id, chat_id):
        res = self.get_user(user_id, chat_id)
        return res[3] if res else None

    def remove_nickname(self, user_id, chat_id):
        self.cur.execute('UPDATE users SET nickname=NULL WHERE user_id=? AND chat_id=?', (user_id, chat_id))
        self.conn.commit()

    def set_warn(self, user_id, chat_id, count):
        if self.get_user(user_id, chat_id) is None:
            self.cur.execute('INSERT INTO users (user_id, chat_id) VALUES (?, ?)', (user_id, chat_id))
        self.cur.execute('UPDATE users SET warn_count=? WHERE user_id=? AND chat_id=?', (count, user_id, chat_id))
        self.conn.commit()

    def get_warn(self, user_id, chat_id):
        res = self.get_user(user_id, chat_id)
        return res[4] if res else 0

    def set_mute(self, user_id, chat_id, until_timestamp):
        if self.get_user(user_id, chat_id) is None:
            self.cur.execute('INSERT INTO users (user_id, chat_id) VALUES (?, ?)', (user_id, chat_id))
        self.cur.execute('UPDATE users SET mute_until=? WHERE user_id=? AND chat_id=?', (until_timestamp, user_id, chat_id))
        self.conn.commit()

    def get_mute(self, user_id, chat_id):
        res = self.get_user(user_id, chat_id)
        return res[5] if res else 0

    def set_ban(self, user_id, chat_id, until_timestamp):
        if self.get_user(user_id, chat_id) is None:
            self.cur.execute('INSERT INTO users (user_id, chat_id) VALUES (?, ?)', (user_id, chat_id))
        self.cur.execute('UPDATE users SET ban_until=? WHERE user_id=? AND chat_id=?', (until_timestamp, user_id, chat_id))
        self.conn.commit()

    def get_ban(self, user_id, chat_id):
        res = self.get_user(user_id, chat_id)
        return res[6] if res else 0

    def set_admin_blocked(self, user_id, chat_id, blocked):
        if self.get_user(user_id, chat_id) is None:
            self.cur.execute('INSERT INTO users (user_id, chat_id) VALUES (?, ?)', (user_id, chat_id))
        self.cur.execute('UPDATE users SET admin_blocked=? WHERE user_id=? AND chat_id=?', (blocked, user_id, chat_id))
        self.conn.commit()

    def get_admin_blocked(self, user_id, chat_id):
        res = self.get_user(user_id, chat_id)
        return res[7] if res else 0

    def increment_message_count(self, user_id, chat_id):
        if self.get_user(user_id, chat_id) is None:
            self.cur.execute('INSERT INTO users (user_id, chat_id) VALUES (?, ?)', (user_id, chat_id))
        self.cur.execute('UPDATE users SET message_count = message_count + 1, last_message_time = ? WHERE user_id=? AND chat_id=?',
                         (int(time.time()), user_id, chat_id))
        self.conn.commit()

    def get_message_count(self, user_id, chat_id):
        res = self.get_user(user_id, chat_id)
        return res[8] if res else 0

    def get_last_message_time(self, user_id, chat_id):
        res = self.get_user(user_id, chat_id)
        return res[9] if res else 0

    # ==================== БАНЫ (ИСТОРИЯ) ====================
    def add_ban_record(self, user_id, chat_id, moderator_id, reason, expire_at, is_global=0):
        issued_at = int(time.time())
        self.cur.execute('''
            INSERT INTO bans (user_id, chat_id, moderator_id, reason, issued_at, expire_at, is_global)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, chat_id, moderator_id, reason, issued_at, expire_at, is_global))
        self.conn.commit()
        return self.cur.lastrowid

    def get_ban_records(self, user_id, chat_id=None, only_global=False):
        if chat_id is not None and not only_global:
            self.cur.execute('SELECT * FROM bans WHERE user_id=? AND (chat_id=? OR is_global=1) ORDER BY issued_at DESC', (user_id, chat_id))
        elif only_global:
            self.cur.execute('SELECT * FROM bans WHERE user_id=? AND is_global=1 ORDER BY issued_at DESC', (user_id,))
        else:
            self.cur.execute('SELECT * FROM bans WHERE user_id=? ORDER BY issued_at DESC', (user_id,))
        return self.cur.fetchall()

    # ==================== ГЛОБАЛЬНЫЕ БАНЫ ====================
    def get_global_ban(self, user_id):
        self.cur.execute('SELECT ban_until FROM global_bans WHERE user_id=?', (user_id,))
        res = self.cur.fetchone()
        return res[0] if res else 0

    def set_global_ban(self, user_id, until_timestamp, moderator_id, reason='Не указана'):
        self.cur.execute('INSERT OR REPLACE INTO global_bans (user_id, ban_until) VALUES (?, ?)', (user_id, until_timestamp))
        self.conn.commit()
        self.add_ban_record(user_id, None, moderator_id, reason, until_timestamp, is_global=1)

    def remove_global_ban(self, user_id):
        self.cur.execute('DELETE FROM global_bans WHERE user_id=?', (user_id,))
        self.conn.commit()

    # ==================== ГРУППЫ И ЧАТЫ ====================
    def create_group(self, group_id, owner_id):
        self.cur.execute('INSERT OR REPLACE INTO groups (group_id, owner_id) VALUES (?, ?)', (group_id, owner_id))
        self.conn.commit()

    def delete_group(self, group_id):
        self.cur.execute('DELETE FROM groups WHERE group_id=?', (group_id,))
        self.conn.commit()
        self.cur.execute('UPDATE chats SET group_id=NULL WHERE group_id=?', (group_id,))
        self.conn.commit()

    def get_group_owner(self, group_id):
        self.cur.execute('SELECT owner_id FROM groups WHERE group_id=?', (group_id,))
        res = self.cur.fetchone()
        return res[0] if res else None

    def bind_chat(self, chat_id, group_id):
        self.cur.execute('INSERT OR REPLACE INTO chats (chat_id, group_id) VALUES (?, ?)', (chat_id, group_id))
        self.conn.commit()

    def unbind_chat(self, chat_id):
        self.cur.execute('UPDATE chats SET group_id=NULL WHERE chat_id=?', (chat_id,))
        self.conn.commit()

    def get_chat_group(self, chat_id):
        self.cur.execute('SELECT group_id FROM chats WHERE chat_id=?', (chat_id,))
        res = self.cur.fetchone()
        return res[0] if res else None

    def set_chat_active(self, chat_id, active):
        self.cur.execute('UPDATE chats SET active=? WHERE chat_id=?', (active, chat_id))
        self.conn.commit()

    def get_chat_active(self, chat_id):
        self.cur.execute('SELECT active FROM chats WHERE chat_id=?', (chat_id,))
        res = self.cur.fetchone()
        return res[0] if res else 0

    def set_log_enabled(self, chat_id, enabled):
        self.cur.execute('UPDATE chats SET log_enabled=? WHERE chat_id=?', (enabled, chat_id))
        self.conn.commit()

    def get_log_enabled(self, chat_id):
        self.cur.execute('SELECT log_enabled FROM chats WHERE chat_id=?', (chat_id,))
        res = self.cur.fetchone()
        return res[0] if res else 0

    def add_log(self, chat_id, user_id, action):
        timestamp = int(time.time())
        self.cur.execute('INSERT INTO logs (chat_id, user_id, action, timestamp) VALUES (?, ?, ?, ?)',
                         (chat_id, user_id, action, timestamp))
        self.conn.commit()

    # ==================== СПИСКИ ====================
    def get_users_with_warn(self, chat_id):
        self.cur.execute('SELECT user_id, warn_count FROM users WHERE chat_id=? AND warn_count>0', (chat_id,))
        return self.cur.fetchall()

    def get_users_with_mute(self, chat_id):
        now = int(time.time())
        self.cur.execute('SELECT user_id, mute_until FROM users WHERE chat_id=? AND mute_until>?', (chat_id, now))
        return self.cur.fetchall()

    def get_users_with_nick(self, chat_id):
        self.cur.execute('SELECT user_id, nickname FROM users WHERE chat_id=? AND nickname IS NOT NULL', (chat_id,))
        return self.cur.fetchall()

    def get_users_with_ban(self, chat_id):
        now = int(time.time())
        self.cur.execute('SELECT user_id, ban_until FROM users WHERE chat_id=? AND ban_until>?', (chat_id, now))
        return self.cur.fetchall()

    def get_global_bans(self):
        now = int(time.time())
        self.cur.execute('SELECT user_id, ban_until FROM global_bans WHERE ban_until>?', (now,))
        return self.cur.fetchall()

    def get_staff(self, chat_id):
        self.cur.execute('SELECT user_id, role FROM users WHERE chat_id=? AND role!="user"', (chat_id,))
        return self.cur.fetchall()

    def close(self):
        self.conn.close()
