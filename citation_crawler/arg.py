import argparse
import importlib


def add_argument_pid(parser: argparse.ArgumentParser, *flags, dest: str = 'pid') -> None:
    if len(flags) <= 0:
        flags = ['-p', '--pid']
    parser.add_argument(
        *flags, dest=dest, action='append', required=False, default=[],
        help=f'Specified a list of paperId to start crawling.'
    )


def add_argument_aid(parser: argparse.ArgumentParser, *flags, dest: str = 'aid') -> None:
    if len(flags) <= 0:
        flags = ['-a', '--aid']
    parser.add_argument(
        *flags, dest=dest, action='append', required=False, default=[],
        help=f'Specified a list of authorId to start crawling.'
    )


def parse_args_pid_author(parser: argparse.ArgumentParser, pid_dest: str = 'pid', aid_dest: str = 'aid'):
    args = parser.parse_args()
    pid_list = []
    for pid_s in args.__getattribute__(pid_dest):
        try:
            pid = eval(pid_s)
            if isinstance(pid, str):
                pid_list.append(pid)
            else:
                pid_list.extend(pid)
        except:
            pid_list.append(pid_s)
    aid_list = []
    for aid_s in args.__getattribute__(aid_dest):
        try:
            aid = eval(aid_s)
            if isinstance(aid, str):
                aid_list.append(aid)
            else:
                aid_list.extend(aid)
        except:
            aid_list.append(aid_s)
    return pid_list, aid_list
