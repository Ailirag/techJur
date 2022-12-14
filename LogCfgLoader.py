import os
import re
import shutil
import socket
import sys
import time
import zipfile
import configparser
import tempfile
import psutil
import sys
from datetime import datetime

silent_mode = len(sys.argv) > 1

if silent_mode:
    silent = dict()
    silent['target'] = sys.argv[1]
    silent['logcfg'] = sys.argv[2]
    silent['action'] = sys.argv[3]
    silent['letter_of_disk'] = sys.argv[4]
    if silent['action'] == '-run':
        silent['action_with_log'] = sys.argv[5]


new_log = f'{os.getcwd()}{os.sep}log.txt'
path_to_archives = f'{os.getcwd()}{os.sep}archives'
path_to_xml = f'{os.getcwd()}{os.sep}logcfg'
path_to_settings = f'{os.getcwd()}{os.sep}settings.ini'


if not os.path.exists(path_to_archives):
    os.mkdir(path_to_archives)


if not os.path.exists(path_to_xml):
    os.mkdir(path_to_xml)


def logging(message, error=False):
    with open(new_log, 'a') as log:
        text = f'{datetime.now()} : {message}'
        print(text)
        log.write(f'{text}\n')

config_file = configparser.ConfigParser()

try:
    print(f'path to settings: {path_to_settings}')
    if not os.path.exists(path_to_settings):
        config_file['DEFAULT']['prefix_archive_name'] = socket.gethostname()
        config_file['DEFAULT']['pause_to_unlock'] = '30'
        config_file['DEFAULT']['path_to_archives'] = path_to_archives
        with open(path_to_settings, 'w') as configfile:
            config_file.write(configfile)

    config_file.read(path_to_settings)
    prefix_archive_name = config_file['DEFAULT']['prefix_archive_name']
    pause_to_unlock = int(config_file['DEFAULT']['pause_to_unlock'])
    path_to_archives = config_file['DEFAULT']['path_to_archives']

except Exception as e:
    error_exc = str(type(e)) + str(e)
    logging(f'Error read [settings.ini]. You may delete this file for default settings: {error_exc}')
    input(f'File reading error [settings.ini]. You can delete this file to restore the stage settings. {error_exc}')
    sys.exit()

actions_for_an_existing = [
    'Delete a file logcfg.xml and remove the archive of the collected data',
    'Replace logcfg.xml with another one',
    'Only delete logcfg.xml and exit.',
    'Exit'
]


def get_tempfile_name():
    return os.path.join(tempfile.gettempdir(), next(tempfile._get_candidate_names()))


def do_archivation(destinations):
    logging('Archiving in progress...')

    name_archive = f'{path_to_archives}{os.sep}{prefix_archive_name}_archive_logs_{datetime.now().strftime("%d-%m-%Y-%H-%M")}.zip'
    reserve_name_archive = f'{os.getcwd()}{os.sep}{prefix_archive_name}_archive_logs_{datetime.now().strftime("%d-%m-%Y-%H-%M")}.zip'

    name_archive_tmp = get_tempfile_name()
    error_archive = False
    archiving_done = False
    while True:
        try:
            with zipfile.ZipFile(f'{name_archive_tmp}', 'w') as myzip:
                for dest in destinations:
                    for root, dirs, files in os.walk(dest):  # Список всех файлов и папок в директории folder
                        for file in files:
                            myzip.write(os.path.join(root, file), compress_type=zipfile.ZIP_DEFLATED)

            logging(f'Archive record on a temp file on {name_archive_tmp}')
            archiving_done = True
            shutil.move(name_archive_tmp, name_archive)
            logging(f'Previous logs are archived in {name_archive}')
            print(f'Successfully archived in {name_archive}, you can take it.')
            break
        except PermissionError as e:
            print('The data was not unblocked. Repeat pause for 10 seconds.')
            time.sleep(10)
        except Exception as e:
            error_exc = str(type(e)) + str(e)
            logging(f'Archiving failed with an error: {error_exc}')
            input(f'Archiving error. The program will be closed. {error_exc}')
            error_archive = True
            if archiving_done:
                shutil.move(name_archive_tmp, reserve_name_archive)
                logging(f'Archive moved to {reserve_name_archive}')
            break

    return name_archive, error_archive


def delete_files(tree_dir, is_file=False):
    logging(f'Deleting files on {tree_dir}')

    while True:
        try:
            if is_file:
                if os.path.exists(tree_dir):
                    shutil.os.remove(tree_dir)
                else:
                    logging(f'Deleting. The file [{tree_dir}] does not exist. Skipped')
                print(f'File {tree_dir} successfully deleted.')
            else:
                for destination in tree_dir:
                    if os.path.exists(destination):
                        shutil.rmtree(destination)
                    else:
                        logging(f'Deleting. The directory [{destination}] does not exist. Skipped')
                print('Log files have been successfully deleted.')
            logging('Deletion completed')
            return False
        except PermissionError as e:
            print('Deletion error, data was not unblocked. Pause for 10 seconds...')
            logging('Permission error. 10 second pause...')
            time.sleep(10)
            continue
        except Exception as e:
            error_exc = str(type(e)) + str(e)
            logging(f'Deleting failed with an error: {error_exc}')
            input(f'Deletion error. The program will be closed. {error_exc}')
            return True


def get_purpose_path():

    list_of_mount = re.findall(r"[A-Z]+:.*$", os.popen("mountvol /").read(), re.MULTILINE)

    mas_of_path = []

    for proc in psutil.win_service_iter():
        if proc.status() == 'running':
            binpath = proc.binpath()
            finded = re.findall("([\w]:.*?)\\\\bin\\\\ragent.exe", binpath)
            if finded:
                mas_of_path.append(finded[0])

    if silent_mode:
        if len(mas_of_path) == 1:
            return f'{mas_of_path[0]}{os.sep}bin{os.sep}conf{os.sep}logcfg.xml'
        else:
            return silent['target']


    if len(mas_of_path) > 1:
        logging(f'Find {len(mas_of_path) - 1} paths of platforms 1C')
        print('==================================================')
        print('Several 1C paths were found. Select the target folder:')
        for i in mas_of_path:
            print(f'[{mas_of_path.index(i)}] {i}')
        print('===================================================')

        choice = int(input())

        if choice > len(mas_of_path) - 1:
            input('Selection error. The work of the program is over.')
        else:
            gl_choice = choice
    else:
        gl_choice = 0

    return f'{mas_of_path[gl_choice]}{os.sep}bin{os.sep}conf{os.sep}logcfg.xml'


try:

    logging('START PROGRAMM')
    user = os.environ['userdomain'] + '\\' + os.getlogin()
    logging(f'Current user: {user}')

    purpose = get_purpose_path()
    logging(f'Destination : {purpose}')
    print(f'Target path [{purpose}]')

    if os.path.exists(purpose):
        logging('[logcfg.xml] was posted earlier')
        print(f'File logcfg.xml already exists in the destination path: {purpose}.')
        for action in actions_for_an_existing:
            print(f'[{actions_for_an_existing.index(action) + 1}] {action}')

        while True:
            if silent_mode and silent['action'] == '-stop':
                choice = '1'
            elif silent_mode and silent['action'] == 'run':
                choice = '2'
            else:
                choice = input('Select an action: ')

                if choice not in ('1', '2', '3', '4'):
                    logging(f'Bad number action for existing file. Input : [{choice}]')
                    input('Input error. Try again.')
                    continue

            choice = int(choice)

            logging(f'User choice [{choice}] action for existing file [logcfg.xml]')

            if choice == 3:
                delete_files(purpose, True)
                logging('THE PROGRAM WAS CLOSED')
                sys.exit()
            elif choice == 4:
                logging('THE PROGRAM WAS CLOSED')
                sys.exit()
            elif choice == 2:
                delete_files(purpose, True)
                break
            elif choice == 1:

                with open(purpose, 'r', encoding='utf-8') as flog:
                    all_text = flog.read()
                    logs_destination = re.findall(r'log location="([^"]*)"', all_text)

                delete_files(purpose, True)
                print(f'A pause of {pause_to_unlock} seconds is performed to unlock the collected logs...')
                time.sleep(pause_to_unlock)
                logging(f'Pause to unlock logs [{pause_to_unlock} seconds] ...')

                name_archive, error_a = do_archivation(logs_destination)

                if not error_a:
                    error_d = delete_files(logs_destination)

                if error_d or error_a:
                    sys.exit()
                else:
                    logging('THE PROGRAM WAS CLOSED')
                    if not silent_mode:
                        input('The program is finished. Press [Enter] to close.')
                    sys.exit()

    mas_logcfg_files = []

    with os.scandir(path_to_xml) as directories:
        for dir in directories:
            mas_logcfg_files.append(dir.name)
    
    if len(mas_logcfg_files) == 0:
        message = f'No log settings file was found in the {path_to_xml} folder. Press [Enter] to exit.'
        logging(message)
        if not silent_mode:
            input(message)
        sys.exit()
    
    while True:

        if silent_mode:
            logcfg_exist = silent['logcfg'] in mas_logcfg_files
            if logcfg_exist:
                choice = int(mas_logcfg_files.index(silent['logcfg'])) + 1
                logging(f"index {mas_logcfg_files.index(silent['logcfg'])}")
            else:
                message = f'Error placement. File {silent["logcfg"]} not exists.'
                print(message)
                logging(message)
                sys.exit(404)
        else:

            print('Which settings file to place?')
            for name_log in mas_logcfg_files:
                print(f'[{mas_logcfg_files.index(name_log) + 1}] {name_log}')
            choice = int(input('Enter a number: '))
        try:
            if choice > len(mas_logcfg_files) or choice == '0':
                choice = input('Input error. Enter a number: ')
                continue
            else:
                name_logcfg = f'logcfg{os.sep}{mas_logcfg_files[choice - 1]}'
                logging(f'Selected logcfg file [{name_logcfg}]')
                break

        except Exception as e:
            error_exc = str(type(e)) + str(e)
            choice = input('Input error. Enter a number: ')

    previously_created_logs = []

    with open(name_logcfg, 'r', encoding='utf-8') as flog:
        all_text = flog.read()
        logs_destination = re.findall(r'log location="([^"]*)"', all_text)

        for dest in logs_destination:
            if os.path.exists(dest):
                previously_created_logs.append(dest)

    if len(previously_created_logs) > 0:
        logging('old logs found')
        print('\nPreviously created log collection destination folders were found.')
        for dest in previously_created_logs:
            print(f'{dest}')

        if silent_mode:
            if silent['action_with_log'] == '-delete':
                choice = '3'
            elif silent['action_with_log'] == '-archive':
                choice = '1'
        else:
            choice = input('''What to do with them?
     1 - archive. 
     2 - archive and exit.
     3 - delete.
     4 - ignore.
     5 - exit\n''')
        while True:
            if choice == '5':
                logging('[5] the work of the program is completed without result')
                sys.exit()
            elif choice == '1' or choice == '2':
                logging(f'[{choice}] archiving')
                name_archive, error_a = do_archivation(previously_created_logs)

                if not error_a:
                    error_d = delete_files(previously_created_logs)

                if error_a or error_d:
                    sys.exit()

                if choice == '2':
                    logging('THE PROGRAM WAS CLOSED')
                    input('The work of the program is completed. Press [Enter] to exit.')
                    sys.exit()

                break
            elif choice == '3':
                logging(f'[{choice}] deleting old logs')
                error_d = delete_files(previously_created_logs)
                if error_d:
                    sys.exit()
                break
            elif choice == '4':
                logging(f'[{choice}] ignoring old logs')
                break
            else:
                choice = input('Selection error.\What to do with them? 1 - archive. 2 - delete, 3 - exit')

    try:
        if silent_mode:
            with open(f'{os.getcwd()}{os.sep}{name_logcfg}', 'r', encoding='utf-8') as flog:
                all_text = flog.read()

            current_letter = set(re.findall('log location=["\']([\w]:\\\\).*?[\'"]', all_text))

            if list(current_letter)[0][0].lower() != silent['letter_of_disk'].lower():
                logging(f"Change letter of disk destination on [{list(current_letter)[0][0]}] to [{silent['letter_of_disk'].lower()}]")

                all_text = all_text.replace(list(current_letter)[0], f"{silent['letter_of_disk']}:\\")
                with open(f'{os.getcwd()}{os.sep}{name_logcfg}', 'w', encoding='utf-8') as flog:
                    flog.write(all_text)
        # edit log location for silent

        shutil.copyfile(f'{os.getcwd()}{os.sep}{name_logcfg}', purpose)
        logging('logcfg.xml successfully placed')
        if not silent_mode:
            input('logcfg has been successfully placed. Press [Enter] to exit')
    except Exception as e:
        error = str(type(e)) + str(e)
        logging(f'Placement error. {error}')
        if not silent_mode:
            input(error)

    logging('THE PROGRAM WAS CLOSED')

except Exception as e:
    error = str(type(e)) + str(e)
    logging(f'FATAL ERROR. {error}')