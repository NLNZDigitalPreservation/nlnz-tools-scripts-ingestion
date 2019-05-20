#!/usr/bin/env python
# SunOS:
#!/usr/bin/python2.7

# bulk-file-rename.py
# Requires source_folder, file_name_portion_to_replace, file_name_portion_replacement.
# Optional verbose, test, debug.

import argparse
import datetime
import os
import platform
import subprocess
import sys

is_sun_os = False
unacceptable_parameters = False
source_folder = ""

DATE_PARSE_FORMAT = "%Y%m%d"
DATE_DISPLAY_FORMAT = "%Y-%m-%d"
DATE_TIME_DISPLAY_FORMAT = "%Y-%m-%d %H:%M:%S"

print("Python version: " + platform.python_version() + ", complete: " + str(sys.version_info))


def determine_if_sun_os():
    global is_sun_os
    output = subprocess.check_output(["uname"])
    is_sun_os = "sunos" in str(output).lower()
    print("is_sun_os=" + str(is_sun_os))


def parse_parameters():
    parser = argparse.ArgumentParser(description="bulk-file-rename.py: Bulk filename replacement.")
    parser.add_argument('--source_folder', type=str, required=True,
                        help='The root source-folder for the report.')
    parser.add_argument('--file_name_portion_to_replace', type=str, required=True,
                        help='The portion of the filename that will be replacement.')
    parser.add_argument('--file_name_portion_replacement', type=str, required=True,
                        help='The replacement portion of the filename.')
    parser.add_argument('--verbose', dest='verbose', action='store_true',
                        help='Indicates that operations will be done in a verbose manner. ' +
                             'NOTE: This means that no csv report file will be generated.')
    parser.add_argument('--debug', dest='debug', action='store_true',
                        help='Indicates that operations will include debug output.')
    parser.add_argument('--test', dest='test', action='store_true',
                        help='Indicates that only tests will be run.')

    parser.set_defaults(verbose=False, debug=False, test=False)

    args = parser.parse_args()

    return args


def display_parameter_values():
    print("")
    print("Parameters as set:")
    print("    source_folder=" + source_folder)
    print("    file_name_portion_to_replace=" + file_name_portion_to_replace)
    print("    file_name_portion_replacement=" + file_name_portion_replacement)
    print("    verbose=" + str(verbose))
    print("    debug=" + str(debug))
    print("    test=" + str(test))


# There is no processing legend for this processing
def display_processing_legend():
    pass


def process_parameters(parsed_arguments):
    global source_folder
    source_folder = parsed_arguments.source_folder
    global file_name_portion_to_replace
    file_name_portion_to_replace = parsed_arguments.file_name_portion_to_replace
    global file_name_portion_replacement
    file_name_portion_replacement = parsed_arguments.file_name_portion_replacement
    global verbose
    verbose = parsed_arguments.verbose
    global debug
    debug = parsed_arguments.debug
    global test
    test = parsed_arguments.test

    global move_or_copy_flags
    global unacceptable_parameters

    display_parameter_values()

    if verbose and not is_sun_os:
        move_or_copy_flags = "-v"
    else:
        move_or_copy_flags = ""

    if is_directory(source_folder):
        print("source_folder=" + source_folder + " exists and is directory, processing can take place.")
    else:
        print("ERROR source_folder=" + source_folder + " does not exist or is not a directory. It must exist!")
        unacceptable_parameters = True

    if file_name_portion_to_replace:
        print("file_name_portion_to_replace='" + file_name_portion_to_replace + "' is a non-empty string")
    else:
        print("file_name_portion_to_replace='" + file_name_portion_to_replace + "' cannot be an empty string")
        unacceptable_parameters = True

    if unacceptable_parameters:
        print("")
        print("Parameters are incomplete or incorrect. Please try again.")
        print("")


def is_directory(directory_path):
    return os.path.exists(directory_path) and not os.path.isfile(directory_path)


def is_file(file_path):
    return os.path.exists(file_path) and os.path.isfile(file_path)


def is_file_or_directory(file_path):
    return os.path.exists(file_path)


def timestamp_message(message_string):
    current_time = datetime.datetime.now()
    print(current_time.strftime(DATE_TIME_DISPLAY_FORMAT) + ": " + message_string)
    sys.stdout.flush()


def get_all_files(root_directory_path):
    all_files = []
    timestamp_message("finding all files on path=" + root_directory_path)
    for root, dirs, files in os.walk(root_directory_path):
        for file_name in files:
            all_files.append(os.path.join(root, file_name))
    timestamp_message(str(len(all_files)) + " files found on path=" + root_directory_path)

    all_files.sort()
    return all_files


def print_debug(message):
    if debug:
        print("D E B U G " + message)


def new_name_for_file(file_name, to_replace, replacement):
    new_name = file_name
    if to_replace in file_name:
        new_name = file_name.replace(to_replace, replacement)
    return new_name


def processing_loop():
    all_files = get_all_files(source_folder)
    for full_file_path in all_files:
        file_name = os.path.basename(full_file_path)
        file_root = os.path.dirname(full_file_path)
        new_filename = new_name_for_file(file_name, file_name_portion_to_replace, file_name_portion_replacement)
        if file_name != new_filename:
            new_file = os.path.join(file_root, new_filename)
            print("Renaming " + full_file_path + " to " + new_filename)
            os.rename(full_file_path, new_file)


def test_replacement(file_name, to_replace, replacement, expected_new_filename):
    new_filename = new_name_for_file(file_name, to_replace, replacement)
    if new_filename == expected_new_filename:
        pass_or_fail = "PASSED"
    else:
        pass_or_fail = "FAILED"
    print("test " + pass_or_fail + ": file_name=" + file_name + ", to_replace=" + to_replace + ", replacement=" +
          replacement + ", expected_new_filename=" + expected_new_filename)


def do_tests():
    test_replacement("abc_def_ghi.pdf", "_def_", "", "abcghi.pdf")
    test_replacement("abc_def_ghi.pdf", "_def_", "BIG", "abcBIGghi.pdf")
    test_replacement("abc_pdf_ghi.pdf", "pdf", "BIG", "abc_BIG_ghi.BIG")
    test_replacement("abc_pdf_ghi.pdf", ".pdf", "BIG", "abc_pdf_ghiBIG")


def main():
    determine_if_sun_os()
    parsed_arguments = parse_parameters()
    process_parameters(parsed_arguments)

    display_processing_legend()

    timestamp_message("STARTED")

    if test:
        do_tests()
    elif not unacceptable_parameters:
        processing_loop()

    timestamp_message("ENDED")


main()
