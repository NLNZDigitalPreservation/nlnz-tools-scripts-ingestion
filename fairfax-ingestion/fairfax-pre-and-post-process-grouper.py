#!/usr/bin/env python
# SunOS:
#!/usr/bin/python2.7

# fairfax-pre-and-post-process-grouper.py
# Group source files by date and titleCode.
# Determines if the source files have been processed by looking for 'done' file.
# If processing has taken place, then move to post-process location and mimic file structure.
# If no 'done' file, determine if files have already been processed by matching filename
# and md5 hash to post-process location. If no post-process then files go to pre-process location.
# Pre-process output is used by readyForIngestion.
# Requires source_folder, target_pre_process_folder, target_post_process_folder, for_review_folder.
# Uses starting_date, ending_date.
# Optional createDestination, moveFiles, verbose, test.

import datetime
import argparse
import os
import sys
import platform
import subprocess
import re

move_or_copy_flags = ""
is_sun_os = False
unacceptable_parameters = False
source_folder = ""
target_pre_process_folder = ""
target_post_process_folder = ""
for_review_folder = ""
starting_date = None
ending_date = None

create_targets = False
move_files = False

DATE_PARSE_FORMAT = "%Y%m%d"
DATE_DISPLAY_FORMAT = "%Y-%m-%d"
DATE_TIME_DISPLAY_FORMAT = "%Y-%m-%d %H:%M:%S"

PDF_FILENAME_REGEX_PATTERN = "(.*)(\\.pdf)"
PDF_FILENAME_REGEX = re.compile(PDF_FILENAME_REGEX_PATTERN)

PDF_COMPONENT_REGEX_PATTERN = "(.*?)\\/(\\w{5,7})-([0-9]{8})(-\\w{3,4}.*?\\.pdf)"
PDF_COMPONENT_REGEX = re.compile(PDF_COMPONENT_REGEX_PATTERN)

FAIRFAX_PDF_FILE_REGEX_PATTERN = "(?P<titleCode>[a-zA-Z0-9]{3,4})(?P<editionCode>[a-zA-Z0-9]{2,3})-(?P<date>\\d{8})-" +\
                                 "(?P<qualifier>.*?)(?P<extension>\\.[pP]{1}[dD]{1}[fF]{1})"
FAIRFAX_PDF_FILE_REGEX = re.compile(FAIRFAX_PDF_FILE_REGEX_PATTERN)

FAIRFAX_PDF_FILE_FULL_REGEX_PATTERN = "(?<titleCode>[a-zA-Z0-9]{3,4})(?<editionCode>[a-zA-Z0-9]{2,3})" +\
                                      "-(?<date>\\d{8})-(?<sequenceLetter>[A-Za-z]{0,2})(?<sequenceNumber>\\d{1,4})" +\
                                      "(?<qualifier>.*?)\\.[pP]{1}[dD]{1}[fF]{1}"

print("Python version: " + platform.python_version() + ", complete: " + str(sys.version_info))


class FairfaxFile:
    is_fairfax_file = False

    def __init__(self, file_name):
        self.file_name = file_name
        match = FAIRFAX_PDF_FILE_REGEX.search(file_name)
        if match is not None:
            self.is_fairfax_file = True
            self.title_code = match.group("titleCode")
            self.edition_code = match.group("editionCode")
            self.file_date_string = match.group("date")
            self.file_date = convert_string_to_date(self.file_date_string)
            self.qualifier = match.group("qualifier")
            self.extension = match.group("extension")
            if len(self.title_code) == 4 and len(self.edition_code) == 2:
                self.edition_code = self.title_code[3:4] + self.edition_code
                self.title_code = self.title_code[0:3]

    def show_values(self):
        print("FairfaxFile, file_name=" + self.file_name)
        print("\tis_fairfax_file=" + str(self.is_fairfax_file))
        if self.is_fairfax_file:
            print("\ttitle_code=" + self.title_code)
            print("\tedition_code=" + self.edition_code)
            print("\tfile_date=" + self.file_date.strftime(DATE_DISPLAY_FORMAT) +
                  ", file_date_string=" + self.file_date_string)
            print("\tqualifier=" + self.qualifier)
            print("\textension=" + self.extension)


def convert_string_to_date(date_string):
    try:
        return datetime.datetime.strptime(date_string, DATE_PARSE_FORMAT).date()
    except ValueError:
        raise argparse.ArgumentTypeError(date_string + " is not a proper date string in the format 'yyyyMMdd'")


def parse_parameters():
    parser = argparse.ArgumentParser(description="Process pre-and-post processed Fairfax files by grouping them by " +
                                                 "date and titleCode in appropriate pre-process and " +
                                                 "post-process folders.")
    parser.add_argument('--source_folder', type=str, required=True,
        help='The source-folder for the files for processing')
    parser.add_argument('--target_pre_process_folder', type=str, required=True,
        help='The target folder for pre-processed files')
    parser.add_argument('--target_post_process_folder', type=str, required=True,
        help='The target folder for post-processed files')
    parser.add_argument('--for_review_folder', type=str, required=True,
        help='The target folder for unrecognized files')
    parser.add_argument('--starting_date', type=convert_string_to_date, default=datetime.date(2014, 1, 1),
        help='The starting-date, format is yyyyMMdd')
    parser.add_argument('--ending_date', type=convert_string_to_date, default=datetime.date(2019, 06, 30),
        help='The ending date, format is yyyyMMdd')
    parser.add_argument('--create_targets', dest='create_targets', action='store_true',
        help='Indicates that the target folders will be created if they do not already exist')
    parser.add_argument('--move_files', dest='move_files', action='store_true',
        help='Indicates that files will be moved to the target folder instead of copied')
    parser.add_argument('--verbose', dest='verbose', action='store_true',
        help='Indicates that operations will be done in a verbose manner')
    parser.add_argument('--test', dest='test', action='store_true',
        help='Indicates that only tests will be run')

    parser.set_defaults(create_targets=False, move_files=False, verbose=False, test=False)

    args = parser.parse_args()

    return args


def determine_if_sun_os():
    global is_sun_os
    output = subprocess.check_output(["uname"])
    is_sun_os = "sunos" in str(output).lower()
    print("is_sun_os=" + str(is_sun_os))


def is_directory(directory_path):
    return os.path.exists(directory_path) and not os.path.isfile(directory_path)


def is_file(file_path):
    return os.path.exists(file_path) and os.path.isfile(file_path)


def is_file_or_directory(file_path):
    return os.path.exists(file_path)


def make_directory_path(directory_path):
    if not is_directory(directory_path):
        os.makedirs(directory_path)


def display_parameter_values():
    print("")
    print("Parameters as set:")
    print("\tsource_folder=" + source_folder)
    print("\ttarget_pre_process_folder=" + target_pre_process_folder)
    print("\ttarget_post_process_folder=" + target_post_process_folder)
    print("\tfor_review_folder=" + for_review_folder)
    print("\tstarting_date=" + starting_date.strftime(DATE_DISPLAY_FORMAT))
    print("\tending_date=" + ending_date.strftime(DATE_DISPLAY_FORMAT))
    print("\tcreate_targets=" + str(create_targets))
    print("\tmove_files=" + str(move_files))
    print("\tverbose=" + str(verbose))
    print("\ttest=" + str(test))
    print("")


def process_parameters(parsed_arguments):
    global source_folder
    source_folder = parsed_arguments.source_folder
    global target_pre_process_folder
    target_pre_process_folder = parsed_arguments.target_pre_process_folder
    global target_post_process_folder
    target_post_process_folder = parsed_arguments.target_post_process_folder
    global for_review_folder
    for_review_folder = parsed_arguments.for_review_folder
    global starting_date
    starting_date = parsed_arguments.starting_date
    global ending_date
    ending_date = parsed_arguments.ending_date
    global create_targets
    create_targets = parsed_arguments.create_targets
    global move_files
    move_files = parsed_arguments.move_files
    global verbose
    verbose = parsed_arguments.verbose
    global test
    test = parsed_arguments.test

    global move_or_copy_flags
    global unacceptable_parameters

    display_parameter_values()

    if starting_date > ending_date:
        print("")
        print("\tERROR starting_date=" + starting_date.strftime(DATE_DISPLAY_FORMAT) +
              " must be BEFORE ending_date=" + ending_date.strftime(DATE_DISPLAY_FORMAT))
        unacceptable_parameters = True

    print("")

    if verbose and not is_sun_os:
        move_or_copy_flags = "-v"
    else:
        move_or_copy_flags = ""

    if is_directory(source_folder):
        print("\tsource_folder=" + source_folder + " exists and is directory, processing can take place.")
    else:
        print("\tERROR source_folder=" + source_folder + " does not exist or is not a directory. It must exist!")
        unacceptable_parameters = True

    print("")

    if is_directory(target_pre_process_folder):
        print("\ttarget_pre_process_folder=" + target_pre_process_folder + " exists and is directory.")
    else:
        if create_targets:
            print("\tCreating " + target_pre_process_folder)
            make_directory_path(target_pre_process_folder)
        else:
            print("\tERROR createTargets=" + create_targets + ", therefore target_pre_process_folder=" +
                  target_pre_process_folder + " must exist!")
            unacceptable_parameters = True

    print("")

    if is_directory(target_post_process_folder):
        print("\ttarget_post_process_folder=" + target_post_process_folder + " exists and is directory.")
    else:
        if create_targets:
            print("\tCreating " + target_post_process_folder)
            make_directory_path(target_post_process_folder)
        else:
            print("\tERROR createTargets=" + create_targets + ", therefore target_post_process_folder=" +
                  target_post_process_folder + " must exist!")
            unacceptable_parameters = True

    print("")

    if is_directory(for_review_folder):
        print("\tfor_review_folder=" + for_review_folder + " exists and is directory.")
    else:
        if create_targets:
            print("\tCreating " + for_review_folder)
            make_directory_path(for_review_folder)
        else:
            print("\tERROR createTargets=" + create_targets + ", therefore for_review_folder=" +
                  for_review_folder + " must exist!")
            unacceptable_parameters = True

    print("")

    if unacceptable_parameters:
        print("")
        print("Parameters are incomplete or incorrect. Please try again.")
        print("")


def timestamp_message(message_string):
    current_time = datetime.datetime.now()
    print(current_time.strftime(DATE_TIME_DISPLAY_FORMAT) + ": " + message_string)


def get_all_suffixed_files(root_directory_path, suffix):
    all_files = []
    timestamp_message("finding all files with case-insensitive suffix='" + suffix + "' on path=" + root_directory_path)
    lower_suffix = suffix.lower()
    for root, dirs, files in os.walk(root_directory_path):
        for file_name in files:
            if file_name.lower().endswith(lower_suffix):
                all_files.append(os.path.join(root, file_name))
    timestamp_message(str(len(all_files)) + " files found with case-insensitive suffix='" + suffix + "' on path=" +
                      root_directory_path)

    all_files.sort()
    return all_files


def get_all_named_files(root_directory_path, filename):
    all_files = []
    timestamp_message("finding all files with case-insensitive name='" + filename + "' on path=" + root_directory_path)
    lower_filename = filename.lower()
    for root, dirs, files in os.walk(root_directory_path):
        for file_name in files:
            if file_name.lower() == lower_filename:
                all_files.append(os.path.join(root, file_name))
    timestamp_message(str(len(all_files)) + " files found with case-insensitive name='" + filename + "' on path=" +
                      root_directory_path)

    all_files.sort()
    return all_files


def get_all_files(root_directory_path):
    all_files = []
    timestamp_message("finding all files on path=" + root_directory_path)
    for root, dirs, files in os.walk(root_directory_path):
        for file_name in files:
            all_files.append(os.path.join(root, file_name))
    timestamp_message(str(len(all_files)) + " files found on path=" + root_directory_path)

    all_files.sort()
    return all_files


def get_md5_sum(the_file):
    if is_sun_os:
        output = subprocess.check_output(["digest", "-a", "md5", "-v", the_file])
        md5sum = str(output).split(" ")[3]
    else:
        output = subprocess.check_output(["md5sum", the_file])
        md5sum = str(output).split(" ")[0]

    return md5sum


def are_files_the_same(first_file_path, second_file_path):
    first_file_md5 = get_md5_sum(first_file_path)
    second_file_md5 = get_md5_sum(second_file_path)

    is_same_file = first_file_md5 == second_file_md5

    if verbose:
        if is_same_file:
            print("Same files, first=" + first_file_path + ", second=" + second_file_path)
        else:
            print("Different files, first=" + first_file_path + ", second=" + second_file_path)

    return is_same_file


def non_duplicate_filename(file_path):
    file_name = os.path.basename(file_path)
    file_path_root = os.path.dirname(file_path)
    # print("original=" + file_path + ", file_path_root=" + file_path_root + ", file_name=" + file_name)
    regex = PDF_FILENAME_REGEX.search(file_name)
    file_name_root = regex.group(1)
    extension = regex.group(2)
    # print("file_name_root=" + file_name_root + ", extension=" + extension)
    # print("")
    file_name_exists = True
    duplicate_index = 0
    while file_name_exists:
        candidate_file_name = file_name_root + "-DUPLICATE-" + str(duplicate_index) + extension
        candidate_full_file_path = os.path.join(file_path_root, candidate_file_name)
        file_name_exists = is_file_or_directory(candidate_full_file_path)
        duplicate_index += 1

    return candidate_full_file_path


def move_or_copy(source_file_path, target_file_or_folder):
    command_list = []
    if move_files:
        command_list.append("mv")
        if not is_sun_os:
            # SunOS 5.10 does not have a noclobber option for move
            command_list.append("-n")
    else:
        command_list.append("cp")
        if is_sun_os:
            command_list.append("-p")
        else:
            command_list.append("-a")
    if len(move_or_copy_flags) > 0:
        command_list.append(move_or_copy_flags)

    command_list.append(source_file_path)
    command_list.append(target_file_or_folder)

    output = subprocess.check_output(command_list)
    if verbose:
        print(output)


def process_for_given_file(current_file_path, unprocessed_folder):
    file_name = os.path.basename(current_file_path)
    file_path_root = os.path.dirname(current_file_path)
    fairfax_file = FairfaxFile(file_name)
    if fairfax_file.is_fairfax_file:
        title_code = fairfax_file.title_code
        file_date = fairfax_file.file_date
        if verbose:
            fairfax_file.show_values()
        target_file_name = fairfax_file.file_name
        target_folder_for_file = target_pre_process_folder + "/" + fairfax_file.file_date_string + "/" + title_code
        if verbose:
            print("target_folder_for_file=" + target_folder_for_file)

        process_file = False
        if starting_date <= file_date <= ending_date:
            if verbose:
                print(starting_date.strftime(DATE_DISPLAY_FORMAT) + " <= " +
                      file_date.strftime(DATE_DISPLAY_FORMAT) + " < =" + ending_date.strftime(DATE_DISPLAY_FORMAT))
            make_directory_path(target_folder_for_file)
            candidate_target_name = target_folder_for_file + "/" + target_file_name
            target_file_name = candidate_target_name
            if is_file_or_directory(candidate_target_name):
                if are_files_the_same(current_file_path, candidate_target_name):
                    process_file = False
                    if verbose:
                        print("File already exists and same (no overwrite), file=" + current_file_path)
                    else:
                        sys.stdout.write('+')
                else:
                    process_file = True
                    target_file_name = non_duplicate_filename(candidate_target_name)
                    print("")
                    print("WARNING Duplicate file=" + candidate_target_name + " renamed to=" + target_file_name)
            else:
                process_file = True
        else:
            if verbose:
                print(starting_date.strftime(DATE_DISPLAY_FORMAT) + " not <= " +
                      file_date.strftime(DATE_DISPLAY_FORMAT) + " not < =" + ending_date.strftime(DATE_DISPLAY_FORMAT))

        if process_file:
            if candidate_target_name == target_file_name:
                actual_target = target_folder_for_file
            else:
                actual_target = target_file_name
            if verbose:
                print("Processing file=" + current_file_path)
            else:
                sys.stdout.write('.')
            move_or_copy(current_file_path, actual_target)
    else:
        # TODO There's no file structure associated with for_review, although when moving processed files, they are
        #      part of an existing folder structure
        move_or_copy(current_file_path, unprocessed_folder)


def process_via_going_through_all_files(all_files):
    unprocessed_folder = for_review_folder + "/UNPROCESSED"
    make_directory_path(unprocessed_folder)

    current_file_count = 0
    total_files = len(all_files)
    for current_file_path in all_files:
        process_for_given_file(current_file_path, unprocessed_folder)

        current_file_count += 1
        if current_file_count % 5000 == 0:
            print("")
            timestamp_message("Processing status: " + str(current_file_count) + "/" + str(total_files))

def processing_loop():
    all_files = get_all_files(source_folder)

    #all_pdf_files = get_all_suffixed_files(source_folder, ".pdf")

    #all_done_files = get_all_named_files(source_folder, "done")

    # for index in range(0, 5):
    #    print("Getting md5sum for file=" + all_files[index] + ", type=" + str(type(all_files[index])))
    #    get_md5_sum(all_files[index])
    #    print("Non-duplicate for file=" + non_duplicate_filename(all_files[index]))

    process_via_going_through_all_files(all_files)


def do_tests():

    test_fairfax_file_names = ["DOMED1-20181222-L04-and-more.PDF", "JAZZABC-20181222-L04.pdf", "not-a-valid-name",
                               "done", "mets.xml", "BA1ODF-20140302-and-more.Pdf"]
    for test_file_name in test_fairfax_file_names:
        test_fairfax_file = FairfaxFile(test_file_name)
        test_fairfax_file.show_values()


def main():
    determine_if_sun_os()
    parsed_arguments = parse_parameters()
    process_parameters(parsed_arguments)

    timestamp_message("STARTED")

    if test:
        do_tests()
    elif not unacceptable_parameters:
        processing_loop()

    print("")
    timestamp_message("ENDED")


main()


