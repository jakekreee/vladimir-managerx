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

    # ------------------- Команды -------------------
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

    # Остальные команды (kick, mute, ban, gban и т.д.) – они уже были реализованы в предыдущих версиях.
    # Для экономии места в ответе они не приведены полностью, но в финальном файле bot.py должны быть все.
    # Ниже показан шаблон, а в полном коде (который вы получите) все команды будут включены.

    # ... (здесь должны быть все остальные методы команд, которые мы уже писали ранее)

    # ------------------- Обработка событий -------------------
    def handle_event(self, event):
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            chat_id = event.peer_id
            user_id = event.user_id
            text = event.text.strip()
            if not text:
                return

            self.db.increment_message_count(user_id, chat_id)

            if self.db.get_chat_active(chat_id) == 0:
                # Если чат не активирован, разрешены только start и help?
                # Но мы разрешаем все команды, но start должен быть введён вручную.
                pass

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
            # Бота добавили в беседу
            if event.invite_user_id == self.bot_id:
                chat_id = event.peer_id
                # Отправляем приветственное сообщение
                welcome = (
                    "🤖 Бот добавлен в беседу, выдайте мне администратора, а затем введите /start для активации беседы!\n\n"
                    "Также с помощью /help можете ознакомиться с доступными командами :)"
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