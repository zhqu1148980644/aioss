# coding=utf-8
# from __future__ import absolute_import, division, print_function, \
#     with_statement
import argparse
import inspect
import json
import os
import re


class Config(object):

    def __init__(self, server=False):
        self.server = server
        self.server_check_list = ['timeout', 'worker', 'pid_file', 'log_file',
                                  'default_method', 'default_protocol',
                                  'default_protocol_param', 'default_fast_open',
                                  'users']
        self.client_check_list = ['local_address', 'local_port', 'server_address']
        self.userinfo_check_list = ['port', 'password', 'method', 'protocol', 'protocol_param', 'fast_open']
        self.full_config = self.get_config()

    def __call__(self, port=None):

        user_config = self.create_user_config(port)
        if user_config is not None:
            return UserConfig(user_config, self.server)
        else:
            return None

    def get_config(self):
        aioss_path = os.path.dirname(os.path.realpath(inspect.getfile(inspect.currentframe())))
        default_config_dir = re.sub(r'\\', r'/', aioss_path) + r'/config.json'
        config = {}

        if self.server:
            # server only support load config file mode.
            parser = argparse.ArgumentParser(description='aio operating manual')
            parser.add_argument('-c', '--config', default=default_config_dir, help='choose your config file')
            args = parser.parse_args()
            config_path = args.config
            # load config file
            try:
                with open(config_path, 'r') as f:
                    config = json.loads(f.read())
            except Exception as e:
                print(e)
                raise ValueError
            # if value in config file is "",then delete it
            config = self.delete_empty(config)
            # if no user_dict in users,create default user_dict
            default_userdict = {
                "user1": {
                    "port": 8080
                }
            }
            # set default values and control value type
            config['timeout'] = config.setdefault('timeout', 300)
            config['worker'] = int(config.setdefault('worker', 1))
            config['pid_file'] = config.setdefault('pid_file', '/var/run/shadowsocks.pid')
            config['log_file'] = config.setdefault('log_file', '/var/log/shadowsocks.log')
            config['default_password'] = config.setdefault('default_password', 'fucksb').encode()
            config['default_method'] = config.setdefault('default_method', 'aes-258-cfb')
            config['default_protocol'] = config.setdefault('default_protocol', 'http_simple')
            config['default_protocol_param'] = config.setdefault('default_protocol_param', '')
            config['default_fast_open'] = config.setdefault('default_fast_open', False)
            config['users'] = self.parse_users(config.setdefault('users', default_userdict), config)
            # delete no meaning keys
            config = self.delete_nomeaning_key(self.server_check_list, dic=config)
            # check authenticity
            if self.check_config(config):
                return config
            else:
                print('configuration was wrong ,check it again!')
                raise ValueError
        else:
            # client support shell input and load config mode both.
            parser = argparse.ArgumentParser(description='aio operating manual')
            parser.add_argument('-c', '--config', help='choose your config file')
            parser.add_argument('-l', '--local_address', type=str, nargs=1,
                                help='set your address you want to listen,default is 127.0.0.1')
            parser.add_argument('-lp', '--local_port', type=int, nargs=1, help='set your local port you want to listen')
            parser.add_argument('-s', '--server_address', type=str, nargs=1,
                                help='set your server address you want to connect')
            parser.add_argument('-sp', '--port', type=int, nargs=1, help='set your server port you want to connect')
            parser.add_argument('-k', '--password', type=str, nargs=1, help='set your password')
            parser.add_argument('-m', '--method', type=str, nargs=1, help='set your method')
            parser.add_argument('-p', '--protocol', type=str, nargs=1, help='set your protocol')
            parser.add_argument('-o', '--protocol_param', type=str, nargs=1, help='set your protocol params')
            parser.add_argument('-f', '--fast_open', action='store_true', default=False, help='set your protocol')
            args = parser.parse_args()
            # if inputed -c/--config ,load config file
            if args.config is not None:
                config_path = args.config
                try:
                    with open(config_path, 'r') as f:
                        config = json.loads(f.read())
                except Exception as e:
                    print('config file loading failed,check your config file again')
            # if value in config file is "",then delete it
            config = self.delete_empty(config)
            # rewrite config where get new value from shell input
            for key, value in args.__dict__.items():
                if key != 'config' and key != 'c':
                    if value is not None:
                        config[key] = value
            # set default value and contro data type
            config['local_address'] = str(config.setdefault('local_address', '127.0.0.1'))
            config['local_port'] = int(config.setdefault('local_port', 1080))
            config['server_address'] = str(config.setdefault('server_address', 0))
            config['port'] = int(config.setdefault('port', 0))
            config['password'] = config.setdefault('password', 'fucksb').encode()
            config['method'] = str(config.setdefault('method', 'aes-258-cfb'))
            config['protocol'] = str(config.setdefault('protocol', 'http_simple'))
            config['protocol_param'] = str(config.setdefault('protocol_param', ''))
            config['fast_open'] = config.setdefault('fastopen', False)
            # if server_address or port were not set,then raise error
            if config['server_address'] == '0' or config['port'] == 0:
                print('At least set your server address and port!!!')
                raise ValueError
            # delete no meaning keys
            config = self.delete_nomeaning_key(self.client_check_list, self.userinfo_check_list, dic=config)
            # check correctability
            if self.check_config(config):
                return config
            else:
                print('configuration was wrong ,check it again!')
                raise ValueError

    def parse_users(self, user_dict, config):
        tmp_user_info_dict = {}
        for user, user_info in user_dict.items():
            user_info['port'] = int(user_info.setdefault('port', 0))
            if user_info['port'] == 0:
                print("At least set user's port!")
                raise ValueError
            user_info = self.delete_empty(user_info)

            info_list = [i for i in self.userinfo_check_list if i != 'port']

            for info in info_list:
                user_info[info] = user_info.setdefault(info, config['default_' + info])
            user_info = self.delete_nomeaning_key(self.userinfo_check_list, dic=user_info)
            user_info['password'] = user_info['password'].encode() if type(user_info['password']) is str else user_info[
                'password']

            tmp_user_info_dict[user] = user_info
            # user_info['password'] = user_info.setdefault('password',config['default_password'])
        return tmp_user_info_dict

    def delete_empty(self, dic):
        tmp = {key: value for key, value in dic.items() if value != ''}
        return tmp

    def delete_nomeaning_key(self, *args, dic):
        def convene(*args):
            tmp = []
            for li in args[0]:
                for key in li:
                    tmp.append(key)
            return tmp

        check_list = convene(args)
        return {key: value for key, value in dic.items() if key in check_list}

    def check_config(self, config):

        return True

    def create_user_config(self, port):
        if self.server:
            for user, user_info in self.full_config['users'].items():
                if user_info['port'] == int(port):
                    user_config = {}
                    user_config['timeout'] = self.full_config['timeout']
                    user_config['worker'] = self.full_config['worker']
                    user_config['pid_file'] = self.full_config['pid_file']
                    user_config['log_file'] = self.full_config['log_file']
                    user_config.update(user_info)
                    return user_config
            return None
        else:
            return self.full_config


class UserConfig(object):
    def __init__(self, user_config, server=False):
        self.server = server
        self.config = user_config

    @property
    def local_addr(self):
        if not self.server:
            return self.config.get('local_address', '127.0.0.1'), self.config.get('local_port', 1080)
        else:
            return self.config.get('local_address', '127.0.0.1'), self.config.get('port', None)

    @property
    def remote_addr(self):
        if not self.server:
            return self.config['server_address'], self.config['port']
        else:
            return None

    @property
    def encryptor(self):
        return self.config['password'], self.config['method']

    @property
    def protocol(self):
        return self.config['protocol']

    @property
    def method(self):
        return self.config['method']

    @property
    def password(self):
        return self.config['password']
