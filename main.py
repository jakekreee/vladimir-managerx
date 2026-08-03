import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import datetime
import re
import random
import time
from config import TOKEN, GROUP_ID, BOT_ID
from database import Database

class Bot:
    def __init__(self):
        self.token = TOKEN
        self.group_id = GROUP_ID
        self.vk_session = vk_api.VkApi(token=self.token)
        self.vk = self.vk_session.get_api()
        self.longpoll = VkLongPoll(self.vk_session)
        self.db = Database()
        self.bot_id = BOT_ID or self._get_bot_id()
        self.commands = {
            'stats': self.cmd_stats,
            'help': self.cmd_help,
            'getid': self.cmd_getid,
            'kick': self.cmd_kick,
            'mute': self.cmd_mute,
            'unmute': self.cmd_unmute,
            'warn': self.cmd_warn,
            'unwarn': self.cmd_unwarn,
            'warnlist': self.cmd_warnlist,
            'mutelist': self.cmd_mutelist,
            'nicklist': self.cmd_nicklist,
            'nonicks': self.cmd_nonicks,
            'onlinelist': self.cmd_onlinelist,
            'getban': self.cmd_baninfo,
            'baninfo': self.cmd_baninfo,
            'чекбан': self.cmd_baninfo,
            'гетбан': self.cmd_baninfo,
            'getnick': self.cmd_getnick,
            'getacc': self.cmd_getacc,
            'staff': self.cmd_staff,
            'setnick': self.cmd_setnick,
            'removenick': self.cmd_removenick,
            'clear': self.cmd_clear,
            'aban': self.cmd_aban,
            'addmoder': self.cmd_addmoder,
            'removerole': self.cmd_removerole,
            'ban': self.cmd_ban,
            'unban': self.cmd_unban,
            'gmute': self.cmd_gmute,
            'gunmute': self.cmd_gunmute,
            'gwarn': self.cmd_gwarn,
            'gunwarn': self.cmd_gunwarn,
            'zov': self.cmd_zov,
            'online': self.cmd_online,
            'addsendmoder': self.cmd_addsendmoder,
            'gsetnick': self.cmd_gsetnick,
            'gremovenick': self.cmd_gremovenick,
            'banlist': self.cmd_banlist,
            'gkick': self.cmd_gkick,
            'gzov': self.cmd_gzov,
            'addadmin': self.cmd_addadmin,
            'pin': self.cmd_pin,
            'unpin': self.cmd_unpin,
            'silence': self.cmd_silence,
            'addsendadmin': self.cmd_addsendadmin,
            'gban': self.cmd_gban,
            'gunban': self.cmd_gunban,
            'chat': self.cmd_chat,
            'gbanlist': self.cmd_gbanlist,
            'unaban': self.cmd_unaban,
            'addchief': self.cmd_addchief,
            'urkick': self.cmd_urkick,
            'rename': self.cmd_rename,
            'gsetrole': self.cmd_gsetrole,
            'gremoverole': self.cmd_gremoverole,
            'addspec': self.cmd_addspec,
            'mygroups': self.cmd_mygroups,
            'creategroup': self.cmd_creategroup,
            'delgroup': self.cmd_delgroup,
            'bind': self.cmd_bind,
            'unbind': self.cmd_unbind,
            'start': self.cmd_start,
            'logs': self.cmd_logs,
            'giveowner': self.cmd_giveowner,
        }
        self.aliases = {
            'snick': 'setnick',
            'rnick': 'removenick',
            'moder': 'addmoder',
            'smoder': 'addsendmoder',
            'admin': 'addadmin',
            'sadmin': 'addsendadmin',
            'addga': 'addchief',
            'spec': 'addspec',
            'nlist': 'nicklist'
        }

    def _get_bot_id(self):
        try:
            res = self.vk.users.get()[0]
            return res['id']
        except:
            return None

    def get_role_level(self, role):
        levels = {
            'user': 0,
            'moder': 1,
            'smoder': 2,
            'admin': 3,
            'sadmin': 4,
            'gadmin': 5,
            'specadmin': 6,
            'owner': 7
        }
        return levels.get(role, 0)

    def check_permission(self, user_id, chat_id, required_role):
        gban_until = self.db.get_global_ban(user_id)
        if gban_until > int(time.time()):
            return False, "Вы в глобальном бане."
        ban_until = self.db.get_ban(user_id, chat_id)
        if ban_until > int(time.time()):
            return False, "Вы забанены в этом чате."
        if required_role != 'user' and self.db.get_admin_blocked(user_id, chat_id) == 1:
            return False, "Вам заблокированы админ-команды."
        user_role = self.db.get_role(user_id, chat_id)
        if self.get_role_level(user_role) >= self.get_role_level(required_role):
            return True, ""
        return False, "Недостаточно прав."

    def get_user_name(self, user_id, chat_id=None):
        if chat_id:
            nick = self.db.get_nickname(user_id, chat_id)
            if nick:
                return nick
        try:
            user = self.vk.users.get(user_ids=user_id)[0]
            return f"{user['first_name']} {user['last_name']}"
        except:
            return f"id{user_id}"

    def get_chat_title(self, chat_id):
        try:
            conv = self.vk.messages.getConversationsById(peer_ids=chat_id)
            if conv['items']:
                return conv['items'][0]['chat_settings']['title']
        except:
            pass
        return f"Чат {chat_id}"

    def send_message(self, chat_id, message, reply_to=None, keyboard=None):
        if not chat_id:
            return
        params = {
            'peer_id': chat_id,
            'message': message,
            'random_id': random.randint(1, 2**31)
        }
        if reply_to:
            params['reply_to'] = reply_to
        if keyboard:
            params['keyboard'] = keyboard if isinstance(keyboard, str) else keyboard.get_keyboard()
        try:
            self.vk.messages.send(**params)
        except Exception as e:
            print(f"Ошибка отправки: {e}")

    def get_user_by_mention(self, text):
        pattern = r'\[id(\d+)\|.*?\]'
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))
        numbers = re.findall(r'\d+', text)
        if numbers:
            return int(numbers[0])
        return None

    # ==================== КОМАНДЫ ====================

    def cmd_stats(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        target = user_id
        if args:
            potential_target = self.get_user_by_mention(' '.join(args))
            if potential_target:
                target = potential_target
            else:
                self.send_message(chat_id, "Пользователь не найден.", reply_to=event.message_id)
                return
        if target != user_id and self.get_role_level(self.db.get_role(user_id, chat_id)) < self.get_role_level('moder'):
            self.send_message(chat_id, "Недостаточно прав для просмотра статистики другого пользователя.", reply_to=event.message_id)
            return

        role = self.db.get_role(target, chat_id)
        warns = self.db.get_warn(target, chat_id)
        nick = self.db.get_nickname(target, chat_id) or "не установлен"
        ban_until = self.db.get_ban(target, chat_id)
        gban_until = self.db.get_global_ban(target)
        now = int(time.time())
        chat_ban_status = "Нет" if ban_until < now else datetime.datetime.fromtimestamp(ban_until).strftime("%d.%m.%Y %H:%M") + " (UTC+3)"
        global_ban_status = "отсутствует" if gban_until < now else "до " + datetime.datetime.fromtimestamp(gban_until).strftime("%d.%m.%Y %H:%M") + " (UTC+3)"
        msg_count = self.db.get_message_count(target, chat_id)
        last_msg_time = self.db.get_last_message_time(target, chat_id)
        last_msg_str = "нет сообщений" if last_msg_time == 0 else datetime.datetime.fromtimestamp(last_msg_time).strftime("%d.%m.%Y %H:%M:%S") + " (UTC+3)"

        ban_records = self.db.get_ban_records(target)
        total_bans = len(ban_records)
        active_bans = [b for b in ban_records if b[6] == 0 and b[5] > now]
        active_ban_count = len(active_bans)

        msg = f"📊 Информация о пользователе\n"
        msg += f"Роль: {role}\n"
        msg += f"Блокировок: {total_bans}\n"
        msg += f"Общая блокировка в чатах: {global_ban_status}\n"
        msg += f"Общая блокировка в беседах игроков: {active_ban_count}\n"
        msg += f"Активные предупреждения: {warns}\n"
        msg += f"Блокировка чата: {chat_ban_status}\n"
        msg += f"Ник: {nick}\n"
        msg += f"Всего сообщений: {msg_count}\n"
        msg += f"Последнее сообщение: {last_msg_str}"

        keyboard = None
        if self.get_role_level(self.db.get_role(user_id, chat_id)) >= self.get_role_level('moder') and target != user_id:
            keyboard = VkKeyboard(one_time=False)
            keyboard.add_button("Все предупреждения", color=VkKeyboardColor.PRIMARY, payload={"command": f"warnlist {target}"})
            keyboard.add_button("Информация о блокировках", color=VkKeyboardColor.NEGATIVE, payload={"command": f"baninfo {target}"})
            keyboard = keyboard.get_keyboard()

        self.send_message(chat_id, msg, reply_to=event.message_id, keyboard=keyboard)

    def cmd_baninfo(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        if not args:
            self.send_message(chat_id, "Укажите пользователя.", reply_to=event.message_id)
            return
        target = self.get_user_by_mention(' '.join(args))
        if not target:
            self.send_message(chat_id, "Пользователь не найден.", reply_to=event.message_id)
            return
        if self.get_role_level(self.db.get_role(user_id, chat_id)) < self.get_role_level('moder'):
            self.send_message(chat_id, "Недостаточно прав.", reply_to=event.message_id)
            return

        now = int(time.time())
        gban_until = self.db.get_global_ban(target)
        gban_status = "отсутствует" if gban_until < now else f"до {datetime.datetime.fromtimestamp(gban_until).strftime('%d.%m.%Y %H:%M:%S')} (UTC+3)"

        msg = f"🔒 Информация о блокировках пользователя {self.get_user_name(target, chat_id)}\n\n"
        msg += f"Блокировка во всех беседах — {gban_status} (gban)\n\n"

        ban_records = self.db.get_ban_records(target, only_global=False)
        active_bans = [b for b in ban_records if b[6] == 0 and b[5] > now]
        if active_bans:
            msg += f"Блокировки в беседах ({len(active_bans)}):\n"
            for idx, ban in enumerate(active_bans, 1):
                chat_id_ban = ban[2]
                chat_title = self.get_chat_title(chat_id_ban) if chat_id_ban else "Глобальный"
                mod_name = self.get_user_name(ban[3])
                reason = ban[4] if ban[4] else "Не указана"
                issued = datetime.datetime.fromtimestamp(ban[5]).strftime("%d.%m.%Y %H:%M:%S")
                expire = datetime.datetime.fromtimestamp(ban[6]).strftime("%d.%m.%Y %H:%M:%S")
                msg += f"{idx}) {chat_title} | {mod_name} | {reason} | {issued} МСК (UTC+3) (до {expire})\n"
        else:
            msg += "Блокировки в беседах отсутствуют (ban)"

        self.send_message(chat_id, msg, reply_to=event.message_id)

    def cmd_kick(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        if not args:
            self.send_message(chat_id, "Укажите пользователя (упоминание или id).", reply_to=event.message_id)
            return
        target = self.get_user_by_mention(' '.join(args))
        if not target:
            self.send_message(chat_id, "Пользователь не найден.", reply_to=event.message_id)
            return
        try:
            self.vk.messages.removeChatUser(chat_id=chat_id - 2000000000, user_id=target)
            self.send_message(chat_id, f"Пользователь {self.get_user_name(target, chat_id)} кикнут.")
            self.db.add_log(chat_id, user_id, f"kick {target}")
        except Exception as e:
            self.send_message(chat_id, f"Ошибка: {e}", reply_to=event.message_id)

    def cmd_mute(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        if len(args) < 2:
            self.send_message(chat_id, "Использование: mute [пользователь] [время в минутах]", reply_to=event.message_id)
            return
        target = self.get_user_by_mention(args[0])
        if not target:
            self.send_message(chat_id, "Пользователь не найден.", reply_to=event.message_id)
            return
        try:
            minutes = int(args[1])
        except:
            self.send_message(chat_id, "Время должно быть числом (минуты).", reply_to=event.message_id)
            return
        until = int(time.time()) + minutes * 60
        self.db.set_mute(target, chat_id, until)
        self.send_message(chat_id, f"Пользователь {self.get_user_name(target, chat_id)} замучен на {minutes} минут.")
        self.db.add_log(chat_id, user_id, f"mute {target} {minutes}")

    def cmd_unmute(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        if not args:
            self.send_message(chat_id, "Укажите пользователя.", reply_to=event.message_id)
            return
        target = self.get_user_by_mention(' '.join(args))
        if not target:
            self.send_message(chat_id, "Пользователь не найден.", reply_to=event.message_id)
            return
        self.db.set_mute(target, chat_id, 0)
        self.send_message(chat_id, f"Мут снят с {self.get_user_name(target, chat_id)}.")
        self.db.add_log(chat_id, user_id, f"unmute {target}")

    def cmd_warn(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        if not args:
            self.send_message(chat_id, "Укажите пользователя.", reply_to=event.message_id)
            return
        target = self.get_user_by_mention(' '.join(args))
        if not target:
            self.send_message(chat_id, "Пользователь не найден.", reply_to=event.message_id)
            return
        current = self.db.get_warn(target, chat_id)
        self.db.set_warn(target, chat_id, current + 1)
        self.send_message(chat_id, f"Предупреждение выдано {self.get_user_name(target, chat_id)} (всего: {current+1})")
        self.db.add_log(chat_id, user_id, f"warn {target}")

    def cmd_unwarn(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        if not args:
            self.send_message(chat_id, "Укажите пользователя.", reply_to=event.message_id)
            return
        target = self.get_user_by_mention(' '.join(args))
        if not target:
            self.send_message(chat_id, "Пользователь не найден.", reply_to=event.message_id)
            return
        current = self.db.get_warn(target, chat_id)
        if current > 0:
            self.db.set_warn(target, chat_id, current - 1)
            self.send_message(chat_id, f"Предупреждение снято с {self.get_user_name(target, chat_id)} (осталось: {current-1})")
        else:
            self.send_message(chat_id, f"У {self.get_user_name(target, chat_id)} нет предупреждений.")
        self.db.add_log(chat_id, user_id, f"unwarn {target}")

    def cmd_warnlist(self, event, args):
        chat_id = event.peer_id
        users = self.db.get_users_with_warn(chat_id)
        if not users:
            self.send_message(chat_id, "Список предупреждений пуст.")
            return
        msg = "⚠️ Список пользователей с предупреждениями:\n"
        for uid, count in users:
            name = self.get_user_name(uid, chat_id)
            msg += f"{name} (id{uid}) - {count}\n"
        self.send_message(chat_id, msg)

    def cmd_mutelist(self, event, args):
        chat_id = event.peer_id
        users = self.db.get_users_with_mute(chat_id)
        if not users:
            self.send_message(chat_id, "Список мута пуст.")
            return
        msg = "🔇 Список пользователей в муте:\n"
        now = int(time.time())
        for uid, until in users:
            name = self.get_user_name(uid, chat_id)
            remaining = until - now
            minutes = remaining // 60
            msg += f"{name} (id{uid}) - осталось {minutes} мин.\n"
        self.send_message(chat_id, msg)

    def cmd_nicklist(self, event, args):
        chat_id = event.peer_id
        users = self.db.get_users_with_nick(chat_id)
        if not users:
            self.send_message(chat_id, "Никнеймы не установлены.")
            return
        msg = "📛 Список никнеймов:\n"
        for uid, nick in users:
            msg += f"{nick} -> id{uid}\n"
        self.send_message(chat_id, msg)

    def cmd_nonicks(self, event, args):
        chat_id = event.peer_id
        try:
            members = self.vk.messages.getConversationMembers(peer_id=chat_id)
            users = [item['member_id'] for item in members['items'] if item['member_id'] > 0]
        except:
            self.send_message(chat_id, "Не удалось получить список участников.")
            return
        no_nicks = []
        for uid in users:
            nick = self.db.get_nickname(uid, chat_id)
            if not nick:
                no_nicks.append(uid)
        if not no_nicks:
            self.send_message(chat_id, "У всех участников есть никнеймы.")
            return
        msg = "Пользователи без никнеймов:\n"
        for uid in no_nicks:
            name = self.get_user_name(uid, chat_id)
            msg += f"{name} (id{uid})\n"
        self.send_message(chat_id, msg)

    def cmd_onlinelist(self, event, args):
        chat_id = event.peer_id
        try:
            members = self.vk.messages.getConversationMembers(peer_id=chat_id)
            online = [item['member_id'] for item in members['items'] if item.get('is_online')]
        except:
            self.send_message(chat_id, "Не удалось получить список онлайн.")
            return
        if not online:
            self.send_message(chat_id, "Онлайн пользователей нет.")
            return
        msg = "🟢 Онлайн пользователи:\n"
        for uid in online:
            name = self.get_user_name(uid, chat_id)
            msg += f"{name} (id{uid})\n"
        self.send_message(chat_id, msg)

    def cmd_getnick(self, event, args):
        chat_id = event.peer_id
        if not args:
            self.send_message(chat_id, "Укажите пользователя.", reply_to=event.message_id)
            return
        target = self.get_user_by_mention(' '.join(args))
        if not target:
            self.send_message(chat_id, "Пользователь не найден.", reply_to=event.message_id)
            return
        nick = self.db.get_nickname(target, chat_id)
        if nick:
            self.send_message(chat_id, f"Никнейм пользователя {self.get_user_name(target, chat_id)}: {nick}")
        else:
            self.send_message(chat_id, f"У пользователя {self.get_user_name(target, chat_id)} нет никнейма.")

    def cmd_getacc(self, event, args):
        chat_id = event.peer_id
        if not args:
            self.send_message(chat_id, "Укажите никнейм.", reply_to=event.message_id)
            return
        nick = ' '.join(args)
        users = self.db.get_users_with_nick(chat_id)
        found = [uid for uid, n in users if n.lower() == nick.lower()]
        if found:
            uid = found[0]
            name = self.get_user_name(uid, chat_id)
            self.send_message(chat_id, f"Пользователь с никнеймом '{nick}': {name} (id{uid})")
        else:
            self.send_message(chat_id, f"Пользователь с никнеймом '{nick}' не найден.")

    def cmd_staff(self, event, args):
        chat_id = event.peer_id
        staff = self.db.get_staff(chat_id)
        if not staff:
            self.send_message(chat_id, "В чате нет персонала с ролями.")
            return
        msg = "👥 Список персонала:\n"
        for uid, role in staff:
            name = self.get_user_name(uid, chat_id)
            msg += f"{name} (id{uid}) - {role}\n"
        self.send_message(chat_id, msg)

    def cmd_setnick(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        if len(args) < 2:
            self.send_message(chat_id, "Использование: setnick [пользователь] [никнейм]", reply_to=event.message_id)
            return
        target = self.get_user_by_mention(args[0])
        if not target:
            self.send_message(chat_id, "Пользователь не найден.", reply_to=event.message_id)
            return
        nickname = ' '.join(args[1:])
        self.db.set_nickname(target, chat_id, nickname)
        self.send_message(chat_id, f"Никнейм для {self.get_user_name(target, chat_id)} установлен: {nickname}")
        self.db.add_log(chat_id, user_id, f"setnick {target} {nickname}")

    def cmd_removenick(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        if not args:
            self.send_message(chat_id, "Укажите пользователя.", reply_to=event.message_id)
            return
        target = self.get_user_by_mention(' '.join(args))
        if not target:
            self.send_message(chat_id, "Пользователь не найден.", reply_to=event.message_id)
            return
        self.db.remove_nickname(target, chat_id)
        self.send_message(chat_id, f"Никнейм удалён у {self.get_user_name(target, chat_id)}.")
        self.db.add_log(chat_id, user_id, f"removenick {target}")

    def cmd_clear(self, event, args):
        self.send_message(event.peer_id, "Команда clear не поддерживается VK API.", reply_to=event.message_id)

    def cmd_aban(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        if not args:
            self.send_message(chat_id, "Укажите пользователя.", reply_to=event.message_id)
            return
        target = self.get_user_by_mention(' '.join(args))
        if not target:
            self.send_message(chat_id, "Пользователь не найден.", reply_to=event.message_id)
            return
        self.db.set_admin_blocked(target, chat_id, 1)
        self.send_message(chat_id, f"Пользователь {self.get_user_name(target, chat_id)} заблокирован для админ-команд.")
        self.db.add_log(chat_id, user_id, f"aban {target}")

    def cmd_addmoder(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        if not args:
            self.send_message(chat_id, "Укажите пользователя.", reply_to=event.message_id)
            return
        target = self.get_user_by_mention(' '.join(args))
        if not target:
            self.send_message(chat_id, "Пользователь не найден.", reply_to=event.message_id)
            return
        target_role = self.db.get_role(target, chat_id)
        if self.get_role_level(target_role) >= self.get_role_level('smoder'):
            self.send_message(chat_id, "Этот пользователь уже имеет равную или высшую роль.")
            return
        self.db.set_role(target, chat_id, 'smoder')
        self.send_message(chat_id, f"Роль модератора выдана {self.get_user_name(target, chat_id)}.")
        self.db.add_log(chat_id, user_id, f"addmoder {target}")

    def cmd_removerole(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        if not args:
            self.send_message(chat_id, "Укажите пользователя.", reply_to=event.message_id)
            return
        target = self.get_user_by_mention(' '.join(args))
        if not target:
            self.send_message(chat_id, "Пользователь не найден.", reply_to=event.message_id)
            return
        target_role = self.db.get_role(target, chat_id)
        if target_role == 'owner':
            self.send_message(chat_id, "Нельзя снять роль владельца.")
            return
        if self.get_role_level(target_role) >= self.get_role_level(self.db.get_role(user_id, chat_id)):
            self.send_message(chat_id, "Нельзя снять роль у пользователя с равной или высшей ролью.")
            return
        self.db.set_role(target, chat_id, 'user')
        self.send_message(chat_id, f"Роль снята с {self.get_user_name(target, chat_id)}.")
        self.db.add_log(chat_id, user_id, f"removerole {target}")

    def cmd_ban(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        if len(args) < 1:
            self.send_message(chat_id, "Использование: ban [пользователь] [дни (необязательно)] [причина]", reply_to=event.message_id)
            return
        target = self.get_user_by_mention(args[0])
        if not target:
            self.send_message(chat_id, "Пользователь не найден.", reply_to=event.message_id)
            return
        days = 0
        reason = "Не указана"
        if len(args) > 1:
            if args[1].isdigit():
                days = int(args[1])
                if days < 5 or days > 360:
                    self.send_message(chat_id, "Бан должен быть от 5 до 360 дней.", reply_to=event.message_id)
                    return
                if len(args) > 2:
                    reason = ' '.join(args[2:])
            else:
                reason = ' '.join(args[1:])
        if days == 0:
            until = 2**31
            days_str = "навсегда"
        else:
            until = int(time.time()) + days * 86400
            days_str = f"{days} дн."
        self.db.set_ban(target, chat_id, until)
        self.db.add_ban_record(target, chat_id, user_id, reason, until, is_global=0)
        self.send_message(chat_id, f"Пользователь {self.get_user_name(target, chat_id)} забанен на {days_str}. Причина: {reason}")
        self.db.add_log(chat_id, user_id, f"ban {target} {days} {reason}")

    def cmd_unban(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        if not args:
            self.send_message(chat_id, "Укажите пользователя.", reply_to=event.message_id)
            return
        target = self.get_user_by_mention(' '.join(args))
        if not target:
            self.send_message(chat_id, "Пользователь не найден.", reply_to=event.message_id)
            return
        self.db.set_ban(target, chat_id, 0)
        self.send_message(chat_id, f"Бан снят с {self.get_user_name(target, chat_id)}.")
        self.db.add_log(chat_id, user_id, f"unban {target}")

    def cmd_gmute(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        group_id = self.db.get_chat_group(chat_id)
        if not group_id:
            self.send_message(chat_id, "Этот чат не привязан к группе.", reply_to=event.message_id)
            return
        if len(args) < 2:
            self.send_message(chat_id, "Использование: gmute [пользователь] [минуты]", reply_to=event.message_id)
            return
        target = self.get_user_by_mention(args[0])
        if not target:
            self.send_message(chat_id, "Пользователь не найден.", reply_to=event.message_id)
            return
        try:
            minutes = int(args[1])
        except:
            self.send_message(chat_id, "Время должно быть числом (минуты).", reply_to=event.message_id)
            return
        until = int(time.time()) + minutes * 60
        chats = self.db.cur.execute('SELECT chat_id FROM chats WHERE group_id=?', (group_id,)).fetchall()
        for (ch,) in chats:
            self.db.set_mute(target, ch, until)
        self.send_message(chat_id, f"Глобальный мут для {self.get_user_name(target, chat_id)} на {minutes} мин.")
        self.db.add_log(chat_id, user_id, f"gmute {target} {minutes}")

    def cmd_gunmute(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        group_id = self.db.get_chat_group(chat_id)
        if not group_id:
            self.send_message(chat_id, "Этот чат не привязан к группе.", reply_to=event.message_id)
            return
        if not args:
            self.send_message(chat_id, "Укажите пользователя.", reply_to=event.message_id)
            return
        target = self.get_user_by_mention(' '.join(args))
        if not target:
            self.send_message(chat_id, "Пользователь не найден.", reply_to=event.message_id)
            return
        chats = self.db.cur.execute('SELECT chat_id FROM chats WHERE group_id=?', (group_id,)).fetchall()
        for (ch,) in chats:
            self.db.set_mute(target, ch, 0)
        self.send_message(chat_id, f"Глобальный мут снят с {self.get_user_name(target, chat_id)}.")
        self.db.add_log(chat_id, user_id, f"gunmute {target}")

    def cmd_gwarn(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        group_id = self.db.get_chat_group(chat_id)
        if not group_id:
            self.send_message(chat_id, "Этот чат не привязан к группе.", reply_to=event.message_id)
            return
        if not args:
            self.send_message(chat_id, "Укажите пользователя.", reply_to=event.message_id)
            return
        target = self.get_user_by_mention(' '.join(args))
        if not target:
            self.send_message(chat_id, "Пользователь не найден.", reply_to=event.message_id)
            return
        chats = self.db.cur.execute('SELECT chat_id FROM chats WHERE group_id=?', (group_id,)).fetchall()
        for (ch,) in chats:
            current = self.db.get_warn(target, ch)
            self.db.set_warn(target, ch, current + 1)
        self.send_message(chat_id, f"Глобальное предупреждение выдано {self.get_user_name(target, chat_id)}.")
        self.db.add_log(chat_id, user_id, f"gwarn {target}")

    def cmd_gunwarn(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        group_id = self.db.get_chat_group(chat_id)
        if not group_id:
            self.send_message(chat_id, "Этот чат не привязан к группе.", reply_to=event.message_id)
            return
        if not args:
            self.send_message(chat_id, "Укажите пользователя.", reply_to=event.message_id)
            return
        target = self.get_user_by_mention(' '.join(args))
        if not target:
            self.send_message(chat_id, "Пользователь не найден.", reply_to=event.message_id)
            return
        chats = self.db.cur.execute('SELECT chat_id FROM chats WHERE group_id=?', (group_id,)).fetchall()
        for (ch,) in chats:
            current = self.db.get_warn(target, ch)
            if current > 0:
                self.db.set_warn(target, ch, current - 1)
        self.send_message(chat_id, f"Глобальное предупреждение снято с {self.get_user_name(target, chat_id)}.")
        self.db.add_log(chat_id, user_id, f"gunwarn {target}")

    def cmd_zov(self, event, args):
        chat_id = event.peer_id
        try:
            members = self.vk.messages.getConversationMembers(peer_id=chat_id)
            users = [item['member_id'] for item in members['items'] if item['member_id'] > 0]
        except:
            self.send_message(chat_id, "Не удалось получить список участников.")
            return
        mentions = []
        for uid in users:
            name = self.get_user_name(uid, chat_id)
            mentions.append(f"[id{uid}|{name}]")
        msg = "📢 Внимание всем! " + " ".join(mentions)
        for part in [msg[i:i+4000] for i in range(0, len(msg), 4000)]:
            self.send_message(chat_id, part)

    def cmd_online(self, event, args):
        chat_id = event.peer_id
        try:
            members = self.vk.messages.getConversationMembers(peer_id=chat_id)
            online = [item['member_id'] for item in members['items'] if item.get('is_online') and item['member_id'] > 0]
        except:
            self.send_message(chat_id, "Не удалось получить список онлайн.")
            return
        if not online:
            self.send_message(chat_id, "Онлайн пользователей нет.")
            return
        mentions = []
        for uid in online:
            name = self.get_user_name(uid, chat_id)
            mentions.append(f"[id{uid}|{name}]")
        msg = "🟢 Онлайн: " + " ".join(mentions)
        self.send_message(chat_id, msg)

    def cmd_addsendmoder(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        if not args:
            self.send_message(chat_id, "Укажите пользователя.", reply_to=event.message_id)
            return
        target = self.get_user_by_mention(' '.join(args))
        if not target:
            self.send_message(chat_id, "Пользователь не найден.", reply_to=event.message_id)
            return
        if self.get_role_level(self.db.get_role(target, chat_id)) >= self.get_role_level('admin'):
            self.send_message(chat_id, "Этот пользователь уже имеет равную или высшую роль.")
            return
        self.db.set_role(target, chat_id, 'admin')
        self.send_message(chat_id, f"Роль старшего модератора выдана {self.get_user_name(target, chat_id)}.")
        self.db.add_log(chat_id, user_id, f"addsendmoder {target}")

    def cmd_gsetnick(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        group_id = self.db.get_chat_group(chat_id)
        if not group_id:
            self.send_message(chat_id, "Этот чат не привязан к группе.", reply_to=event.message_id)
            return
        if len(args) < 2:
            self.send_message(chat_id, "Использование: gsetnick [пользователь] [никнейм]", reply_to=event.message_id)
            return
        target = self.get_user_by_mention(args[0])
        if not target:
            self.send_message(chat_id, "Пользователь не найден.", reply_to=event.message_id)
            return
        nickname = ' '.join(args[1:])
        chats = self.db.cur.execute('SELECT chat_id FROM chats WHERE group_id=?', (group_id,)).fetchall()
        for (ch,) in chats:
            self.db.set_nickname(target, ch, nickname)
        self.send_message(chat_id, f"Глобальный никнейм '{nickname}' установлен для {self.get_user_name(target, chat_id)}.")
        self.db.add_log(chat_id, user_id, f"gsetnick {target} {nickname}")

    def cmd_gremovenick(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        group_id = self.db.get_chat_group(chat_id)
        if not group_id:
            self.send_message(chat_id, "Этот чат не привязан к группе.", reply_to=event.message_id)
            return
        if not args:
            self.send_message(chat_id, "Укажите пользователя.", reply_to=event.message_id)
            return
        target = self.get_user_by_mention(' '.join(args))
        if not target:
            self.send_message(chat_id, "Пользователь не найден.", reply_to=event.message_id)
            return
        chats = self.db.cur.execute('SELECT chat_id FROM chats WHERE group_id=?', (group_id,)).fetchall()
        for (ch,) in chats:
            self.db.remove_nickname(target, ch)
        self.send_message(chat_id, f"Глобальный никнейм удалён у {self.get_user_name(target, chat_id)}.")
        self.db.add_log(chat_id, user_id, f"gremovenick {target}")

    def cmd_banlist(self, event, args):
        chat_id = event.peer_id
        users = self.db.get_users_with_ban(chat_id)
        if not users:
            self.send_message(chat_id, "Список забаненных пуст.")
            return
        msg = "🚫 Список забаненных пользователей:\n"
        now = int(time.time())
        for uid, until in users:
            name = self.get_user_name(uid, chat_id)
            remaining = until - now
            days = remaining // 86400
            msg += f"{name} (id{uid}) - осталось {days} дн.\n"
        self.send_message(chat_id, msg)

    def cmd_gkick(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        group_id = self.db.get_chat_group(chat_id)
        if not group_id:
            self.send_message(chat_id, "Этот чат не привязан к группе.", reply_to=event.message_id)
            return
        if not args:
            self.send_message(chat_id, "Укажите пользователя.", reply_to=event.message_id)
            return
        target = self.get_user_by_mention(' '.join(args))
        if not target:
            self.send_message(chat_id, "Пользователь не найден.", reply_to=event.message_id)
            return
        chats = self.db.cur.execute('SELECT chat_id FROM chats WHERE group_id=?', (group_id,)).fetchall()
        for (ch,) in chats:
            try:
                self.vk.messages.removeChatUser(chat_id=ch - 2000000000, user_id=target)
            except:
                pass
        self.send_message(chat_id, f"Пользователь {self.get_user_name(target, chat_id)} кикнут из всех чатов группы.")
        self.db.add_log(chat_id, user_id, f"gkick {target}")

    def cmd_gzov(self, event, args):
        chat_id = event.peer_id
        group_id = self.db.get_chat_group(chat_id)
        if not group_id:
            self.send_message(chat_id, "Этот чат не привязан к группе.", reply_to=event.message_id)
            return
        chats = self.db.cur.execute('SELECT chat_id FROM chats WHERE group_id=?', (group_id,)).fetchall()
        all_users = set()
        for (ch,) in chats:
            try:
                members = self.vk.messages.getConversationMembers(peer_id=ch)
                for item in members['items']:
                    if item['member_id'] > 0:
                        all_users.add(item['member_id'])
            except:
                pass
        if not all_users:
            self.send_message(chat_id, "Нет пользователей для упоминания.")
            return
        mentions = []
        for uid in all_users:
            name = self.get_user_name(uid, chat_id)
            mentions.append(f"[id{uid}|{name}]")
        msg = "📢 Глобальный вызов: " + " ".join(mentions)
        for part in [msg[i:i+4000] for i in range(0, len(msg), 4000)]:
            self.send_message(chat_id, part)

    def cmd_addadmin(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        if not args:
            self.send_message(chat_id, "Укажите пользователя.", reply_to=event.message_id)
            return
        target = self.get_user_by_mention(' '.join(args))
        if not target:
            self.send_message(chat_id, "Пользователь не найден.", reply_to=event.message_id)
            return
        if self.get_role_level(self.db.get_role(target, chat_id)) >= self.get_role_level('sadmin'):
            self.send_message(chat_id, "Этот пользователь уже имеет равную или высшую роль.")
            return
        self.db.set_role(target, chat_id, 'sadmin')
        self.send_message(chat_id, f"Роль администратора выдана {self.get_user_name(target, chat_id)}.")
        self.db.add_log(chat_id, user_id, f"addadmin {target}")

    def cmd_pin(self, event, args):
        chat_id = event.peer_id
        if not args:
            self.send_message(chat_id, "Укажите ID сообщения для закрепления.", reply_to=event.message_id)
            return
        try:
            msg_id = int(args[0])
        except:
            self.send_message(chat_id, "ID сообщения должно быть числом.", reply_to=event.message_id)
            return
        try:
            self.vk.messages.pin(peer_id=chat_id, message_id=msg_id)
            self.send_message(chat_id, f"Сообщение {msg_id} закреплено.")
            self.db.add_log(chat_id, event.user_id, f"pin {msg_id}")
        except Exception as e:
            self.send_message(chat_id, f"Ошибка: {e}", reply_to=event.message_id)

    def cmd_unpin(self, event, args):
        chat_id = event.peer_id
        try:
            self.vk.messages.unpin(peer_id=chat_id)
            self.send_message(chat_id, "Закрепление снято.")
            self.db.add_log(chat_id, event.user_id, "unpin")
        except Exception as e:
            self.send_message(chat_id, f"Ошибка: {e}", reply_to=event.message_id)

    def cmd_silence(self, event, args):
        self.send_message(event.peer_id, "Режим тишины не реализован в этом примере.")

    def cmd_addsendadmin(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        if not args:
            self.send_message(chat_id, "Укажите пользователя.", reply_to=event.message_id)
            return
        target = self.get_user_by_mention(' '.join(args))
        if not target:
            self.send_message(chat_id, "Пользователь не найден.", reply_to=event.message_id)
            return
        if self.get_role_level(self.db.get_role(target, chat_id)) >= self.get_role_level('gadmin'):
            self.send_message(chat_id, "Этот пользователь уже имеет равную или высшую роль.")
            return
        self.db.set_role(target, chat_id, 'gadmin')
        self.send_message(chat_id, f"Роль старшего администратора выдана {self.get_user_name(target, chat_id)}.")
        self.db.add_log(chat_id, user_id, f"addsendadmin {target}")

    def cmd_gban(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        if len(args) < 1:
            self.send_message(chat_id, "Использование: gban [пользователь] [дни (необязательно)] [причина]", reply_to=event.message_id)
            return
        target = self.get_user_by_mention(args[0])
        if not target:
            self.send_message(chat_id, "Пользователь не найден.", reply_to=event.message_id)
            return
        days = 0
        reason = "Не указана"
        if len(args) > 1:
            if args[1].isdigit():
                days = int(args[1])
                if len(args) > 2:
                    reason = ' '.join(args[2:])
            else:
                reason = ' '.join(args[1:])
        if days == 0:
            until = 2**31
            days_str = "навсегда"
        else:
            until = int(time.time()) + days * 86400
            days_str = f"{days} дн."
        self.db.set_global_ban(target, until, user_id, reason)
        self.send_message(chat_id, f"Глобальный бан выдан {self.get_user_name(target, chat_id)} на {days_str}. Причина: {reason}")
        self.db.add_log(chat_id, user_id, f"gban {target} {days} {reason}")

    def cmd_gunban(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        if not args:
            self.send_message(chat_id, "Укажите пользователя.", reply_to=event.message_id)
            return
        target = self.get_user_by_mention(' '.join(args))
        if not target:
            self.send_message(chat_id, "Пользователь не найден.", reply_to=event.message_id)
            return
        self.db.remove_global_ban(target)
        self.send_message(chat_id, f"Глобальный бан снят с {self.get_user_name(target, chat_id)}.")
        self.db.add_log(chat_id, user_id, f"gunban {target}")

    def cmd_chat(self, event, args):
        chat_id = event.peer_id
        group_id = self.db.get_chat_group(chat_id)
        active = self.db.get_chat_active(chat_id)
        log_enabled = self.db.get_log_enabled(chat_id)
        msg = f"📊 Информация о чате:\nID: {chat_id}\nГруппа: {group_id if group_id else 'не привязан'}\nАктивен: {'да' if active else 'нет'}\nЛоги: {'вкл' if log_enabled else 'выкл'}"
        self.send_message(chat_id, msg)

    def cmd_gbanlist(self, event, args):
        chat_id = event.peer_id
        bans = self.db.get_global_bans()
        if not bans:
            self.send_message(chat_id, "Глобальный бан-лист пуст.")
            return
        msg = "🌐 Глобальный бан-лист:\n"
        now = int(time.time())
        for uid, until in bans:
            name = self.get_user_name(uid, chat_id)
            remaining = until - now
            days = remaining // 86400
            msg += f"{name} (id{uid}) - осталось {days} дн.\n"
        self.send_message(chat_id, msg)

    def cmd_unaban(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        if not args:
            self.send_message(chat_id, "Укажите пользователя.", reply_to=event.message_id)
            return
        target = self.get_user_by_mention(' '.join(args))
        if not target:
            self.send_message(chat_id, "Пользователь не найден.", reply_to=event.message_id)
            return
        self.db.set_admin_blocked(target, chat_id, 0)
        self.send_message(chat_id, f"Блокировка админ-команд снята с {self.get_user_name(target, chat_id)}.")
        self.db.add_log(chat_id, user_id, f"unaban {target}")

    def cmd_addchief(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        if not args:
            self.send_message(chat_id, "Укажите пользователя.", reply_to=event.message_id)
            return
        target = self.get_user_by_mention(' '.join(args))
        if not target:
            self.send_message(chat_id, "Пользователь не найден.", reply_to=event.message_id)
            return
        if self.get_role_level(self.db.get_role(target, chat_id)) >= self.get_role_level('specadmin'):
            self.send_message(chat_id, "Этот пользователь уже имеет равную или высшую роль.")
            return
        self.db.set_role(target, chat_id, 'specadmin')
        self.send_message(chat_id, f"Роль главного администратора выдана {self.get_user_name(target, chat_id)}.")
        self.db.add_log(chat_id, user_id, f"addchief {target}")

    def cmd_urkick(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        try:
            members = self.vk.messages.getConversationMembers(peer_id=chat_id)
            for item in members['items']:
                uid = item['member_id']
                if uid > 0:
                    try:
                        self.vk.messages.removeChatUser(chat_id=chat_id - 2000000000, user_id=uid)
                        time.sleep(0.5)
                    except:
                        pass
            self.send_message(chat_id, "Беседа расформирована.")
            self.db.add_log(chat_id, user_id, "urkick")
        except Exception as e:
            self.send_message(chat_id, f"Ошибка: {e}", reply_to=event.message_id)

    def cmd_rename(self, event, args):
        chat_id = event.peer_id
        if not args:
            self.send_message(chat_id, "Укажите новое название чата.", reply_to=event.message_id)
            return
        new_name = ' '.join(args)
        try:
            self.vk.messages.editChat(chat_id=chat_id - 2000000000, title=new_name)
            self.send_message(chat_id, f"Название чата изменено на '{new_name}'.")
            self.db.add_log(chat_id, event.user_id, f"rename {new_name}")
        except Exception as e:
            self.send_message(chat_id, f"Ошибка: {e}", reply_to=event.message_id)

    def cmd_gsetrole(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        group_id = self.db.get_chat_group(chat_id)
        if not group_id:
            self.send_message(chat_id, "Этот чат не привязан к группе.", reply_to=event.message_id)
            return
        if len(args) < 2:
            self.send_message(chat_id, "Использование: gsetrole [пользователь] [роль]", reply_to=event.message_id)
            return
        target = self.get_user_by_mention(args[0])
        if not target:
            self.send_message(chat_id, "Пользователь не найден.", reply_to=event.message_id)
            return
        role = args[1].lower()
        valid_roles = ['user', 'moder', 'smoder', 'admin', 'sadmin', 'gadmin', 'specadmin', 'owner']
        if role not in valid_roles:
            self.send_message(chat_id, "Некорректная роль. Доступные: " + ", ".join(valid_roles))
            return
        if self.get_role_level(role) >= self.get_role_level(self.db.get_role(user_id, chat_id)):
            self.send_message(chat_id, "Нельзя выдать роль выше или равную вашей.")
            return
        chats = self.db.cur.execute('SELECT chat_id FROM chats WHERE group_id=?', (group_id,)).fetchall()
        for (ch,) in chats:
            self.db.set_role(target, ch, role)
        self.send_message(chat_id, f"Роль '{role}' глобально установлена для {self.get_user_name(target, chat_id)}.")
        self.db.add_log(chat_id, user_id, f"gsetrole {target} {role}")

    def cmd_gremoverole(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        group_id = self.db.get_chat_group(chat_id)
        if not group_id:
            self.send_message(chat_id, "Этот чат не привязан к группе.", reply_to=event.message_id)
            return
        if not args:
            self.send_message(chat_id, "Укажите пользователя.", reply_to=event.message_id)
            return
        target = self.get_user_by_mention(' '.join(args))
        if not target:
            self.send_message(chat_id, "Пользователь не найден.", reply_to=event.message_id)
            return
        if self.db.get_role(target, chat_id) == 'owner':
            self.send_message(chat_id, "Нельзя снять роль владельца.")
            return
        chats = self.db.cur.execute('SELECT chat_id FROM chats WHERE group_id=?', (group_id,)).fetchall()
        for (ch,) in chats:
            self.db.set_role(target, ch, 'user')
        self.send_message(chat_id, f"Роль глобально снята с {self.get_user_name(target, chat_id)}.")
        self.db.add_log(chat_id, user_id, f"gremoverole {target}")

    def cmd_addspec(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        if not args:
            self.send_message(chat_id, "Укажите пользователя.", reply_to=event.message_id)
            return
        target = self.get_user_by_mention(' '.join(args))
        if not target:
            self.send_message(chat_id, "Пользователь не найден.", reply_to=event.message_id)
            return
        if self.get_role_level(self.db.get_role(target, chat_id)) >= self.get_role_level('specadmin'):
            self.send_message(chat_id, "Этот пользователь уже имеет равную или высшую роль.")
            return
        self.db.set_role(target, chat_id, 'specadmin')
        self.send_message(chat_id, f"Роль специального администратора выдана {self.get_user_name(target, chat_id)}.")
        self.db.add_log(chat_id, user_id, f"addspec {target}")

    def cmd_mygroups(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        groups = self.db.cur.execute('SELECT group_id FROM groups WHERE owner_id=?', (user_id,)).fetchall()
        if not groups:
            self.send_message(chat_id, "У вас нет созданных групп.")
            return
        msg = "📁 Ваши группы:\n"
        for (gid,) in groups:
            msg += f"ID: {gid}\n"
        self.send_message(chat_id, msg)

    def cmd_creategroup(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        if len(args) < 1:
            self.send_message(chat_id, "Укажите ID группы (число).", reply_to=event.message_id)
            return
        try:
            group_id = int(args[0])
        except:
            self.send_message(chat_id, "ID группы должно быть числом.", reply_to=event.message_id)
            return
        if self.db.get_group_owner(group_id):
            self.send_message(chat_id, "Группа с таким ID уже существует.")
            return
        self.db.create_group(group_id, user_id)
        self.send_message(chat_id, f"Группа {group_id} создана.")
        self.db.add_log(chat_id, user_id, f"creategroup {group_id}")

    def cmd_delgroup(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        if len(args) < 1:
            self.send_message(chat_id, "Укажите ID группы.", reply_to=event.message_id)
            return
        try:
            group_id = int(args[0])
        except:
            self.send_message(chat_id, "ID группы должно быть числом.", reply_to=event.message_id)
            return
        owner = self.db.get_group_owner(group_id)
        if owner != user_id:
            self.send_message(chat_id, "Вы не являетесь владельцем этой группы.")
            return
        self.db.delete_group(group_id)
        self.send_message(chat_id, f"Группа {group_id} удалена.")
        self.db.add_log(chat_id, user_id, f"delgroup {group_id}")

    def cmd_bind(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        if len(args) < 1:
            self.send_message(chat_id, "Укажите ID группы.", reply_to=event.message_id)
            return
        try:
            group_id = int(args[0])
        except:
            self.send_message(chat_id, "ID группы должно быть числом.", reply_to=event.message_id)
            return
        owner = self.db.get_group_owner(group_id)
        if owner != user_id:
            self.send_message(chat_id, "Вы не являетесь владельцем этой группы.")
            return
        self.db.bind_chat(chat_id, group_id)
        self.send_message(chat_id, f"Чат привязан к группе {group_id}.")
        self.db.add_log(chat_id, user_id, f"bind {group_id}")

    def cmd_unbind(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        group_id = self.db.get_chat_group(chat_id)
        if not group_id:
            self.send_message(chat_id, "Чат не привязан к группе.")
            return
        owner = self.db.get_group_owner(group_id)
        if owner != user_id:
            self.send_message(chat_id, "Вы не являетесь владельцем группы.")
            return
        self.db.unbind_chat(chat_id)
        self.send_message(chat_id, "Чат отвязан от группы.")
        self.db.add_log(chat_id, user_id, "unbind")

    def cmd_start(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        self.db.set_chat_active(chat_id, 1)
        self.send_message(chat_id, "✅ Чат активирован! Теперь все команды работают.")
        self.db.add_log(chat_id, user_id, "start")

    def cmd_logs(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        current = self.db.get_log_enabled(chat_id)
        new_status = 1 if current == 0 else 0
        self.db.set_log_enabled(chat_id, new_status)
        self.send_message(chat_id, f"Логирование {'включено' if new_status else 'выключено'}.")
        self.db.add_log(chat_id, user_id, f"logs {new_status}")

    def cmd_giveowner(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        if not args:
            self.send_message(chat_id, "Укажите пользователя.", reply_to=event.message_id)
            return
        target = self.get_user_by_mention(' '.join(args))
        if not target:
            self.send_message(chat_id, "Пользователь не найден.", reply_to=event.message_id)
            return
        if self.db.get_role(user_id, chat_id) != 'owner':
            self.send_message(chat_id, "Только владелец может передать права.")
            return
        self.db.set_role(target, chat_id, 'owner')
        self.db.set_role(user_id, chat_id, 'user')
        self.send_message(chat_id, f"Права владельца переданы {self.get_user_name(target, chat_id)}.")
        self.db.add_log(chat_id, user_id, f"giveowner {target}")

    def cmd_help(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        role = self.db.get_role(user_id, chat_id)
        commands = {
            'user': ['stats', 'help', 'getid'],
            'moder': ['kick', 'mute', 'unmute', 'warn', 'unwarn', 'warnlist', 'mutelist', 'nicklist', 'nonicks',
                      'onlinelist', 'getban', 'getnick', 'getacc', 'staff', 'setnick', 'removenick', 'clear', 'aban', 'baninfo'],
            'smoder': ['addmoder', 'removerole', 'ban', 'unban', 'gmute', 'gunmute', 'gwarn', 'gunwarn', 'zov', 'online'],
            'admin': ['addsendmoder', 'gsetnick', 'gremovenick', 'banlist', 'gkick', 'gzov'],
            'sadmin': ['addadmin', 'pin', 'unpin', 'silence'],
            'gadmin': ['addsendadmin', 'gban', 'gunban', 'chat', 'gbanlist', 'unaban'],
            'specadmin': ['addchief', 'urkick', 'rename', 'gsetrole', 'gremoverole'],
            'owner': ['addspec', 'mygroups', 'creategroup', 'delgroup', 'bind', 'unbind', 'start', 'logs', 'giveowner']
        }
        level = self.get_role_level(role)
        available = []
        for r, cmds in commands.items():
            if self.get_role_level(r) <= level:
                available.extend(cmds)
        available = sorted(set(available))
        msg = "📋 Доступные команды:\n" + ", ".join(available)
        self.send_message(chat_id, msg, reply_to=event.message_id)

    def cmd_getid(self, event, args):
        chat_id = event.peer_id
        user_id = event.user_id
        if args:
            target = self.get_user_by_mention(' '.join(args))
            if target:
                msg = f"ID пользователя: {target}"
            else:
                msg = "Пользователь не найден."
        else:
            msg = f"Ваш ID: {user_id}"
        self.send_message(chat_id, msg, reply_to=event.message_id)

    # ==================== ОБРАБОТКА СОБЫТИЙ ====================

    def handle_event(self, event):
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            chat_id = event.peer_id
            user_id = event.user_id
            text = event.text.strip()
            if not text:
                return

            self.db.increment_message_count(user_id, chat_id)

            if self.db.get_chat_active(chat_id) == 0:
                if text.startswith('!start') or text.startswith('!help') or text.startswith('!stats'):
                    pass
                else:
                    self.send_message(chat_id, "⚠️ Чат не активирован. Введите !start для активации.", reply_to=event.message_id)
                    return

            mute_until = self.db.get_mute(user_id, chat_id)
            if mute_until > int(time.time()):
                if text.startswith('!help') or text.startswith('!stats') or text.startswith('!getid'):
                    pass
                else:
                    self.send_message(chat_id, "Вы в муте, не можете писать.", reply_to=event.message_id)
                    return

            if not text.startswith('!'):
                return

            parts = text[1:].split()
            if not parts:
                return
            cmd = parts[0].lower()
            args = parts[1:]

            if cmd in self.aliases:
                cmd = self.aliases[cmd]

            if cmd not in self.commands:
                self.send_message(chat_id, f"Неизвестная команда. Используйте !help.", reply_to=event.message_id)
                return

            required_role = 'user'
            role_commands = {
                'user': ['stats', 'help', 'getid'],
                'moder': ['kick', 'mute', 'unmute', 'warn', 'unwarn', 'warnlist', 'mutelist', 'nicklist', 'nonicks',
                          'onlinelist', 'getban', 'getnick', 'getacc', 'staff', 'setnick', 'removenick', 'clear', 'aban', 'baninfo'],
                'smoder': ['addmoder', 'removerole', 'ban', 'unban', 'gmute', 'gunmute', 'gwarn', 'gunwarn', 'zov', 'online'],
                'admin': ['addsendmoder', 'gsetnick', 'gremovenick', 'banlist', 'gkick', 'gzov'],
                'sadmin': ['addadmin', 'pin', 'unpin', 'silence'],
                'gadmin': ['addsendadmin', 'gban', 'gunban', 'chat', 'gbanlist', 'unaban'],
                'specadmin': ['addchief', 'urkick', 'rename', 'gsetrole', 'gremoverole'],
                'owner': ['addspec', 'mygroups', 'creategroup', 'delgroup', 'bind', 'unbind', 'start', 'logs', 'giveowner']
            }
            for role, cmds in role_commands.items():
                if cmd in cmds:
                    required_role = role
                    break

            has_perm, msg = self.check_permission(user_id, chat_id, required_role)
            if not has_perm:
                self.send_message(chat_id, msg, reply_to=event.message_id)
                return

            try:
                self.commands[cmd](event, args)
            except Exception as e:
                self.send_message(chat_id, f"Ошибка выполнения команды: {e}", reply_to=event.message_id)

        elif event.type == VkEventType.CHAT_INVITE_USER:
            if event.invite_user_id == self.bot_id:
                chat_id = event.peer_id
                welcome = (
                    "🤖 Бот добавлен в беседу, выдайте мне администратора, а затем введите !start для активации беседы!\n\n"
                    "Также с помощью !help можете ознакомиться с доступными командами :)"
                )
                self.send_message(chat_id, welcome)

    def run(self):
        print("Бот запущен...")
        for event in self.longpoll.listen():
            try:
                self.handle_event(event)
            except Exception as e:
                print(f"Ошибка в обработке: {e}")

if __name__ == "__main__":
    bot = Bot()
    bot.run()
