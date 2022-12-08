import sys
import re
import os
import fnmatch
import importlib

def main(argv):
    # parse python file in app name specified
    relevant_path = argv[0] if len(argv) > 0 else "pod"
    files_names = fnmatch.filter(os.listdir("pod/" + relevant_path), '*.py')
    """
    char_to_remove = ["\"", ",", "=", "\n", "\r", ":", "(", ")", ".", ";"]
    global_settings_list = []
    for f in files_names:
        print(" - %s" % f)
        file_one = open(os.path.join("pod", relevant_path, f), "r")
        settings_list = []
        for line in file_one:
            line = line.replace("]", "")
            words = re.sub('[%s]' % ''.join(char_to_remove), '', line).split(" ")
            my_list = [
                i.split("[")[0] for i in words if i.isupper() and len(i.split("[")[0]) > 1
            ]
            settings_list += my_list
        print(list(dict.fromkeys(settings_list)))
        global_settings_list += settings_list
    """
    global_settings_list = []
    for f in files_names:
        print(" - %s" % f)
        mod = importlib.import_module('.'.join(['pod', relevant_path, f.replace(".py","")]))
        data = dir(mod)
        settings_list = []
        for d in data:
            if d.isupper() and len(d) > 1:
                settings_list.append(d)
        global_settings_list += settings_list
    global_settings_list = list(dict.fromkeys(global_settings_list))
    global_settings_list.sort()
    print(20 * "-")
    print(relevant_path + " :")
    print("\n    - " + "\n    - ".join(global_settings_list))
    print(20 * "-")
    mk_file = open(os.path.join("pod", "custom", "ConfigurationPod.md"), "r")
    mk_settings = []
    for line in mk_file:
        match = re.search(r'- (?P<set>\w+) = .*', line)
        if match:
            settings = match.group('set')
            if settings not in mk_settings:
                mk_settings.append(settings)
            else:
                print("%s is already in config file")
    mk_settings.sort()
    print("Configuration settings :")
    print("\n    - " + "\n    - ".join(mk_settings))
    new_settings = list(set(global_settings_list) - set(mk_settings))
    new_settings.sort()
    print(20 * "-")
    print("New settings :")
    print("\n    - " + "\n    - ".join(new_settings))
    print(20 * "-")


if __name__ == "__main__":
    # Call python file with name of app to parse
    # i.e.: to parse authentication app, just do :
    # podv3$ python get_settings_by_app.py authentication
    main(sys.argv[1:])
