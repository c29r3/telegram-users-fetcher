#!/usr/bin/env python3
# Python 3.6+
import configparser
import getpass
import os
import timeit
from string import ascii_lowercase

import time
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsAdmins
from telethon.tl.types import ChannelParticipantsSearch


def init_config():
    """Creates a default config (if it does not exist)"""
    if not os.path.exists('config.ini'):
        print('configuration file not found -> create standard config')
        config['default'] = {'# 1st u need to register ur own application here - https://my.telegram.org/auth\n'
                             'api_id': 666666,
                             'api_hash': 'ffffffffffffffffffffffffffffffff',
                             'phone': 79775556644,
                             '\n# chat name in any format (link, chat name, chat_id)\n'
                             'channel': 'https://t.me/norn_community',
                             '\n# Skip users without @username. true or false\n'
                             'with_username_only': 'false',
                             '\n# exclude chat admins. true or false\n'
                             'exclude_admins': 'false',
                             '\n# pause per iteration (in seconds)\n'
                             'pause': 0.5}

        print('Config has been created, u should restart the script')
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
        exit()


def remove_file(filename):
    """Remove old file, if it exists"""
    if os.path.isfile(filename):
        os.remove(filename)


def client_connect():
    """
    Create new session file if it does not exists.
    At the first authorization is necessary to confirm via code
    Session file format example - '79996665544.session'
    """
    c = TelegramClient(config["default"]["phone"], config["default"]["api_id"], config["default"]["api_hash"])
    c.connect()
    print('Client check auth...')
    if not c.is_user_authorized():
        print('Need auth')
        c.send_code_request(config["default"]["phone"])
        c.sign_in(config["default"]["phone"], code=input('Enter code: '))

        if SessionPasswordNeededError is True:
            password = getpass.getpass('2fa password: ')
            c.sign_in(password=password)
            c.start(phone=config["default"]["phone"])

    print('Client initialization complete')
    return c


def parse_users(k):
    """
    Search and filter users by letter of the alphabet
    For example k = "a"
    """
    offset = 0
    while True:
        participants = client(GetParticipantsRequest(channel=channel, filter=ChannelParticipantsSearch(k),
                                                     offset=offset, limit=limit, hash=0))
        if not participants.users:
            break
        for user in participants.users:
            user_string = f'{user.id};{user.first_name};{user.last_name};{user.username}'
            try:
                if user.deleted is True or user.first_name == "Deleted" and user.last_name == "Account":
                    deleted_accounts.append(user_string.replace("None", "-"))
                    continue

                elif user.username is None and config["default"]["with_username_only"] == 'true':
                    print(f'Skip user without username --> {user.id} {user.first_name} {user.last_name}')
                    continue

                elif user.first_name[0].lower() or user.last_name[0].lower() in queryKey:
                    if user.bot is True:
                        bots.append(user_string.replace("None", "-"))

                    else:
                        all_participants.append(user_string.replace("None", "-"))

            except Exception as e:
                pass
        offset += len(participants.users)


def parse_admins():
    """
    :return: list of all chat administrators
    """
    admin_list = []
    print('Admin list:')
    for n, user in enumerate(client.iter_participants(channel, filter=ChannelParticipantsAdmins), 1):
        print(f'{n}) ID:{user.id} | NAME:{user.first_name} | LAST_NAME:{user.last_name} | USER_NAME:@{user.username}')
        admin_list.append(f'{user.id};{user.first_name};{user.last_name};{user.username}'.replace("None", "-"))
    return admin_list


all_participants = []
deleted_accounts = []
bots             = []
timer_start = timeit.default_timer()
config = configparser.ConfigParser()
config.read('config.ini')
init_config()
client = client_connect()
channel = client.get_entity(config["default"]["channel"])
total_users = client.get_participants(config["default"]["channel"]).total
limit = 200
queryKey = list(ascii_lowercase + 'йцукенгшщзхъфывапролджэячсмитьбю' + '1234567890')

print('Processing chat...')
for i, key in enumerate(queryKey, 1):
    parse_users(key)
    print(f'{i}\\{len(queryKey)}')
    time.sleep(float(config["default"]["pause"]))

all_participants = set(all_participants)
admin_list = parse_admins()

# Exclude admins from user list
user_list = [x for x in all_participants if x not in admin_list]
result_file = f'{config["default"]["channel"].replace("https://t.me/joinchat/", "").replace("https://t.me/", "")}.csv'
# Remove old file
remove_file(result_file)

with open(result_file, 'a', encoding='utf-8') as f:
    f.write("ID;FIRST_NAME;LAST_NAME;USERNAME;IS_ADMIN?\n")

    if config["default"]["exclude_admins"] == "false":
        # write admins first
        for admin in admin_list:
            f.write(f'{admin};yes\n')

    # write users
    for user in user_list:
        f.write(f'{user};-\n')


total_time = round((timeit.default_timer() - timer_start), 1)
print(f'Parsed {len(set(user_list))} users, '
      f'{len(set(admin_list))} admins, '
      f'deleted_users {len(set(deleted_accounts))}, '
      f'bots {len(set(bots))}.'
      f'\nTotal users in chat:{total_users}\n'
      f'Total time: {time.strftime("%H:%M:%S", time.gmtime(total_time))}')
