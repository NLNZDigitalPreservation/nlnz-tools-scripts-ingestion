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
# One or the other: do_pre_processing, do_post_processing
# Optional create_targets, move_files, verbose, test.

import argparse
import datetime
import os
import re
import platform
import subprocess
import sys
import time

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

FILENAME_UNSAFE_CHARACTERS = " *$"
REPLACEMENT_FILENAME_SAFE_CHARACTER = "-"
FILE_PATH_SEPARATORS = "/\\"
REPLACEMENT_FILE_PATH_SEPARATOR = "_"

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

EXISTS_IN_POST_PROCESSING_BUT_NOT_THE_SAME_FILE_FOLDER_NAME = "EXISTS-IN-POST-PROCESSING-BUT-NOT-THE-SAME-FILE"

print("Python version: " + platform.python_version() + ", complete: " + str(sys.version_info))


class FairfaxFile:
    is_fairfax_pdf_file = False
    is_done_file = False
    is_mets_xml_file = False
    is_other_file = False

    def __init__(self, file_path):
        self.file_name = os.path.basename(file_path)
        self.dirname = os.path.dirname(file_path)
        self.full_path = file_path
        match = FAIRFAX_PDF_FILE_REGEX.search(self.file_name)
        if match is None:
            if self.file_name == "done":
                self.is_done_file = True
            elif self.file_name == "mets.xml":
                self.is_mets_xml_file = True
            else:
                self.is_other_file = True
        else:
            self.is_fairfax_pdf_file = True
            self.title_code = match.group("titleCode")
            self.edition_code = match.group("editionCode")
            self.file_date_string = match.group("date")
            self.file_date = convert_string_to_date(self.file_date_string)
            self.qualifier = match.group("qualifier")
            self.extension = match.group("extension")
            if len(self.title_code) == 4 and len(self.edition_code) == 2:
                self.edition_code = self.title_code[3:4] + self.edition_code
                self.title_code = self.title_code[0:3]

    def __lt__(self, other):
        if isinstance(other, FairfaxFile):
            return self.full_path < other.full_path
        else:
            return self.full_path < other

    def __hash__(self):
        return hash(self.full_path)

    def show_values(self):
        print("FairfaxFile, file_name=" + self.file_name)
        print("    dirname=" + self.dirname)
        print("    is_fairfax_pdf_file=" + str(self.is_fairfax_pdf_file))
        print("    is_done_file=" + str(self.is_done_file))
        print("    is_mets_xml_file=" + str(self.is_mets_xml_file))
        print("    is_other_file=" + str(self.is_other_file))
        if self.is_fairfax_pdf_file:
            print("    title_code=" + self.title_code)
            print("    edition_code=" + self.edition_code)
            print("    file_date=" + self.file_date.strftime(DATE_DISPLAY_FORMAT) +
                  ", file_date_string=" + self.file_date_string)
            print("    qualifier=" + self.qualifier)
            print("    extension=" + self.extension)


class FileComparison:
    def __init__(self, source_file, target_file, is_target_a_file, are_files_the_same):
        self.source_file = source_file
        self.target_file = target_file
        self.is_target_a_file = is_target_a_file
        self.are_files_the_same = are_files_the_same


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
    parser.add_argument('--do_pre_processing', dest='do_pre_processing', action='store_true',
                        help="Do pre-processing. The source folder is unprocessed files " +
                             "(they will be checked against processed)")
    parser.add_argument('--do_post_processing', dest='do_post_processing', action='store_true',
                        help="Do post-processing. The source folder contains processed files with a" +
                             "'done' file for each group")
    parser.add_argument('--do_list_unique_files', dest='do_list_unique_files', action='store_true',
                        help='List all files with unique filenames. The source folder is unprocessed files')
    parser.add_argument('--create_targets', dest='create_targets', action='store_true',
                        help='Indicates that the target folders will be created if they do not already exist')
    parser.add_argument('--pre_process_include_non_pdf_files', dest='pre_process_include_non_pdf_files',
                        action='store_true',
                        help='Indicates that non-pdf files will be processed. By default only PDF files are processed.')
    parser.add_argument('--move_files', dest='move_files', action='store_true',
                        help='Indicates that files will be moved to the target folder instead of copied')
    parser.add_argument('--verbose', dest='verbose', action='store_true',
                        help='Indicates that operations will be done in a verbose manner')
    parser.add_argument('--test', dest='test', action='store_true',
                        help='Indicates that only tests will be run')

    parser.set_defaults(do_pre_processing=False, do_post_processing=False, do_list_unique_files=False,
                        create_targets=False, pre_process_include_non_pdf_files=False, move_files=False,
                        verbose=False, test=False)

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
    print("    source_folder=" + source_folder)
    print("    target_pre_process_folder=" + target_pre_process_folder)
    print("    target_post_process_folder=" + target_post_process_folder)
    print("    for_review_folder=" + for_review_folder)
    print("    starting_date=" + starting_date.strftime(DATE_DISPLAY_FORMAT))
    print("    ending_date=" + ending_date.strftime(DATE_DISPLAY_FORMAT))
    print("    do_pre_processing=" + str(do_pre_processing))
    print("    do_post_processing=" + str(do_post_processing))
    print("    do_list_unique_files=" + str(do_list_unique_files))
    print("    create_targets=" + str(create_targets))
    print("    pre_process_include_non_pdf_files=" + str(pre_process_include_non_pdf_files))
    print("    move_files=" + str(move_files))
    print("    verbose=" + str(verbose))
    print("    test=" + str(test))
    print("")


def display_processing_legend():
    print("")
    print("Processing legend:")
    print("    .  -- indicates a file has been processed (either moved or copied)")
    print("    :  -- indicates a folder has been processed (either moved or copied)")
    print("    +  -- indicates a duplicate pre-process file has been detected and is exactly the same as")
    print("          the target file. If --move_files has been specified the source file is deleted.")
    print("    #  -- indicates a duplicate folder has been detected and will be copied or moved with the name of the")
    print("          folder with a '-<number>' appended to it.")
    print("    *  -- indicates that a pre-process file already exists (and is the same) in the post-processing")
    print("          target directory. In this case, the file is either not processed (if a copy) or deleted in the")
    print("          source folder (if --move_files).")
    print("    ?  -- indicates that a pre-process file already exists (and is NOT the same) in the post-processing")
    print("          target directory. In this case, the file is either copied or moved to the for_review_folder")
    print("    -  -- indicates that a source file has been deleted. This can happen when:")
    print("              - When pre-processing and the file already exists and --move_files is specified.")
    print("    =  -- indicates that a source folder has been deleted. This can happen when:")
    print("              - When post-processing and --move_files, the parent folder of the 'done' file deleted.")
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
    global do_pre_processing
    do_pre_processing = parsed_arguments.do_pre_processing
    global do_post_processing
    do_post_processing = parsed_arguments.do_post_processing
    global do_list_unique_files
    do_list_unique_files = parsed_arguments.do_list_unique_files
    global create_targets
    create_targets = parsed_arguments.create_targets
    global pre_process_include_non_pdf_files
    pre_process_include_non_pdf_files = parsed_arguments.pre_process_include_non_pdf_files
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
        print("    ERROR starting_date=" + starting_date.strftime(DATE_DISPLAY_FORMAT) +
              " must be BEFORE ending_date=" + ending_date.strftime(DATE_DISPLAY_FORMAT))
        unacceptable_parameters = True

    print("")

    if verbose and not is_sun_os:
        move_or_copy_flags = "-v"
    else:
        move_or_copy_flags = ""

    if is_directory(source_folder):
        print("    source_folder=" + source_folder + " exists and is directory, processing can take place.")
    else:
        print("    ERROR source_folder=" + source_folder + " does not exist or is not a directory. It must exist!")
        unacceptable_parameters = True

    print("")

    if is_directory(target_pre_process_folder):
        print("    target_pre_process_folder=" + target_pre_process_folder + " exists and is directory.")
    else:
        if create_targets:
            print("    Creating " + target_pre_process_folder)
            make_directory_path(target_pre_process_folder)
        else:
            print("    ERROR createTargets=" + create_targets + ", therefore target_pre_process_folder=" +
                  target_pre_process_folder + " must exist!")
            unacceptable_parameters = True

    print("")

    if is_directory(target_post_process_folder):
        print("    target_post_process_folder=" + target_post_process_folder + " exists and is directory.")
    else:
        if create_targets:
            print("    Creating " + target_post_process_folder)
            make_directory_path(target_post_process_folder)
        else:
            print("    ERROR createTargets=" + create_targets + ", therefore target_post_process_folder=" +
                  target_post_process_folder + " must exist!")
            unacceptable_parameters = True

    print("")

    if is_directory(for_review_folder):
        print("    for_review_folder=" + for_review_folder + " exists and is directory.")
    else:
        if create_targets:
            print("    Creating " + for_review_folder)
            make_directory_path(for_review_folder)
        else:
            print("    ERROR createTargets=" + create_targets + ", therefore for_review_folder=" +
                  for_review_folder + " must exist!")
            unacceptable_parameters = True

    print("")

    do_command_count = 0
    if do_pre_processing:
        do_command_count += 1
    if do_post_processing:
        do_command_count += 1
    if do_list_unique_files:
        do_command_count += 1
    if not do_command_count == 1:
        print("    Only ONE of do_pre_processing=" + str(do_pre_processing) + " AND do_post_processing=" +
              str(do_post_processing) + " AND do_list_unique_files=" + str(do_list_unique_files) + " MUST be set.")
        unacceptable_parameters = True

    if unacceptable_parameters:
        print("")
        print("Parameters are incomplete or incorrect. Please try again.")
        print("")


def timestamp_message(message_string):
    current_time = datetime.datetime.now()
    print(current_time.strftime(DATE_TIME_DISPLAY_FORMAT) + ": " + message_string)
    sys.stdout.flush()


def convert_to_filename(file_path_string):
    safe_filename = file_path_string
    if safe_filename.startswith("/"):
        safe_filename = safe_filename[1:]
    for file_path_separator_character in FILE_PATH_SEPARATORS:
        safe_filename = safe_filename.replace(file_path_separator_character, REPLACEMENT_FILE_PATH_SEPARATOR)
    for unsafe_character in FILENAME_UNSAFE_CHARACTERS:
        safe_filename = safe_filename.replace(unsafe_character, REPLACEMENT_FILENAME_SAFE_CHARACTER)

    return safe_filename


def get_all_suffixed_files(root_directory_path, suffix):
    all_files = []
    timestamp_message("finding all files with case-insensitive suffix='" + suffix + "' on path=" + root_directory_path)
    lower_suffix = suffix.lower()
    for root, dirs, files in os.walk(root_directory_path):
        for file_name in files:
            if file_name.lower().endswith(lower_suffix):
                all_files.append(FairfaxFile(os.path.join(root, file_name)))
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
                all_files.append(FairfaxFile(os.path.join(root, file_name)))
    timestamp_message(str(len(all_files)) + " files found with case-insensitive name='" + filename + "' on path=" +
                      root_directory_path)

    all_files.sort()
    return all_files


def get_all_files(root_directory_path):
    all_files = []
    timestamp_message("finding all files on path=" + root_directory_path)
    for root, dirs, files in os.walk(root_directory_path):
        for file_name in files:
            all_files.append(FairfaxFile(os.path.join(root, file_name)))
    timestamp_message(str(len(all_files)) + " files found on path=" + root_directory_path)

    all_files.sort()
    return all_files


def get_md5_sum(the_file):
    max_attempts = 6
    attempt_count = 0
    time_delay_factors = [0.0, 0.3, 0.9, 4.0, 60.0, 120.0]
    is_successful_md5 = False
    md5sum = ""

    # We'll try 5 times
    while not is_successful_md5 and attempt_count < max_attempts:
        attempt_count += 1
        output = "<no-output-provided>"
        try:
            if is_sun_os:
                output = subprocess.check_output(["digest", "-a", "md5", "-v", the_file])
                md5sum = str(output).split(" ")[3]
            else:
                output = subprocess.check_output(["md5sum", the_file])
                md5sum = str(output).split(" ")[0]

            is_successful_md5 = True

        except subprocess.CalledProcessError:
            print("")
            timestamp_message("WARNING md5 sum (attempt " + str(attempt_count) + "/" + str(max_attempts) +
                              " FAILED for file=" + the_file)
            timestamp_message("    output=" + output)
            if attempt_count < max_attempts:
                delay = time_delay_factors[attempt_count]
                timestamp_message("    delaying next md5 sum attempt for " + str(delay) + " seconds.")
                time.sleep(delay)

    if is_successful_md5 and attempt_count > 1:
        timestamp_message("md5 sum attempt=" + str(attempt_count) + " SUCCEEDED for file=" + the_file)

    if not is_successful_md5:
        # re-throw the last exception -- there's something more serious happening
        raise

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


def non_duplicate_directory(file_path):
    directory_name_exists = True
    duplicate_index = 0
    while directory_name_exists:
        candidate_directory_name = file_path + "-" + str(duplicate_index)
        directory_name_exists = is_file_or_directory(candidate_directory_name)
        duplicate_index += 1

    return candidate_directory_name


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

    full_command = ""
    for argument in command_list:
        full_command += " " + argument

    full_command += " \"" + source_file_path + "\""
    full_command += " \"" + target_file_or_folder + "\""

    # Note that using shell=True has security implications (as there is no python checking of the full_command itself)
    output = subprocess.check_output(full_command, shell=True)
    if verbose:
        print(output)


def delete_file(file_to_delete):
    if is_file(file_to_delete):
        command_list = ["rm", file_to_delete]
        output = subprocess.check_output(command_list)
        sys.stdout.write('-')
        sys.stdout.flush()
        if verbose:
            print(output)
    else:
        print("")
        timestamp_message("WARNING: Not deleting, not a file=" + file_to_delete)


def delete_folder(folder_to_delete):
    if is_directory(folder_to_delete):
        command_list = ["rm", "-rf", folder_to_delete]
        output = subprocess.check_output(command_list)
        sys.stdout.write('=')
        sys.stdout.flush()
        if verbose:
            print(output)
    else:
        print("")
        timestamp_message("WARNING: Not deleting, not a directory=" + folder_to_delete)


# file structure for post-processing is the following:
# <magazines|newspapers>/<title_code>/<year>/<file_date_string>/
#                                                       |- done
#                                                       |- content/
#                                                               |- mets.xml
#                                                               |- streams/
#                                                                       |- <pdf-files>
def file_exists_post_processing(fairfax_file, post_processing_folder):
    target_file_post_type = fairfax_file.title_code + "/" + str(fairfax_file.file_date.year) + "/" +\
                       fairfax_file.file_date_string + "/content/streams/" + fairfax_file.file_name
    target_file_path_newspapers = "" + post_processing_folder + "/newspapers/" + target_file_post_type

    post_processing_file_exists = is_file(target_file_path_newspapers)
    if post_processing_file_exists:
        same_file = are_files_the_same(fairfax_file.full_path, target_file_path_newspapers)
        file_comparison = FileComparison(fairfax_file.full_path, target_file_path_newspapers,
                                         post_processing_file_exists, same_file)
    else:
        target_file_path_magazines = "" + post_processing_folder + "/magazines/" + target_file_post_type
        post_processing_file_exists = is_file(target_file_path_magazines)
        if post_processing_file_exists:
            same_file = are_files_the_same(fairfax_file.full_path, target_file_path_magazines)
            file_comparison = FileComparison(fairfax_file.full_path, target_file_path_magazines,
                                             post_processing_file_exists, same_file)
        else:
            file_comparison = FileComparison(fairfax_file.full_path, None, False, False)

    # TODO What if it's the same-named file BUT NOT the same md5 hash? What do we do then?
    # Actually, we are probably better off assuming that if the same-named file is processed then
    # it won't be processed again, no matter if it's the same file or not.
    if file_comparison.is_target_a_file and not file_comparison.are_files_the_same:
        print("")
        timestamp_message("WARNING: same named files in source and post-processing are NOT the same:")
        timestamp_message("    source file=" + file_comparison.source_file)
        timestamp_message("    post-processing file=" + file_comparison.target_file)

    return file_comparison


# file structure for post-processing is the following:
# <newspapers|magazines>/<title_code>/<year>/<file_date_string>/
#                                                       |- done
#                                                       |- content/
#                                                               |- mets.xml
#                                                               |- streams/
#                                                                       |- <file_name>
def post_process_for_given_done_file(fairfax_file, post_processing_folder):
    if fairfax_file.is_done_file:
        done_parent_path = os.path.abspath(os.path.join(fairfax_file.full_path, os.pardir))
        done_parent_name = os.path.basename(done_parent_path)
        newspapers_or_magazines_path = os.path.abspath(os.path.join(done_parent_path, os.pardir))
        newspapers_or_magazines_name = os.path.basename(newspapers_or_magazines_path)
        if "_" in done_parent_name:
            title_and_date = done_parent_name.split("_")
            title_code = title_and_date[0]
            file_date_string = title_and_date[1]
            file_date = convert_string_to_date(file_date_string)
            file_date_year_string = str(file_date.year)
        else:
            title_code = done_parent_name
            file_date_string = "UNKNOWN-DATE"
            file_date_year_string = "UNKNOWN-YEAR"
        if verbose:
            fairfax_file.show_values()

        # TODO This won't copy files that start with '.'
        done_source = fairfax_file.dirname + "/*"
        target_folder = post_processing_folder + "/" + newspapers_or_magazines_name + "/" + title_code +\
                        "/" + file_date_year_string + "/" + file_date_string
        if is_file_or_directory(target_folder):
            # TODO it already exists, make duplicate
            target_folder = non_duplicate_directory(target_folder)
            sys.stdout.write('#')
            sys.stdout.flush()

        make_directory_path(target_folder)
        move_or_copy(done_source, target_folder)
        sys.stdout.write(':')
        sys.stdout.flush()
        # The parent folder should now contain no files if a move took place
        if move_files:
            delete_folder(fairfax_file.dirname)


def post_process_via_going_through_all_done_files(all_done_files):
    current_file_count = 0
    total_files = len(all_done_files)
    for fairfax_done_file in all_done_files:
        post_process_for_given_done_file(fairfax_done_file, target_post_process_folder)

        current_file_count += 1
        if current_file_count % 100 == 0:
            print("")
            timestamp_message("Processing 'done' files, status: " + str(current_file_count) + "/" + str(total_files))

    print("")
    timestamp_message("Processing completed for 'done' files, status: " + str(current_file_count) + "/" + str(total_files))


def pre_process_for_given_pdf_file(fairfax_file, pre_processing_folder, post_processing_folder):
    title_code = fairfax_file.title_code
    file_date = fairfax_file.file_date
    if verbose:
        fairfax_file.show_values()

    process_file = False
    if starting_date <= file_date <= ending_date:
        file_comparison = file_exists_post_processing(fairfax_file, post_processing_folder)
        if file_comparison.are_files_the_same:
            process_file = False
            if verbose:
                print("")
                print("File exists post-processing, file=" + fairfax_file.full_path)
            else:
                sys.stdout.write('*')
                sys.stdout.flush()
            if move_files:
                delete_file(fairfax_file.full_path)
        elif file_comparison.is_target_a_file and not file_comparison.are_files_the_same:
            # We have a situation where the source and target files have the same name BUT they aren't the same file
            # The warning message has already been printed by file_exists_post_processing
            # We want to either copy or move the file to for-review
            process_file = False
            if verbose:
                print("")
                print("File exists post-processing but not the same file, copying/moving to for_review_folder, file="
                      + fairfax_file.full_path)
            else:
                sys.stdout.write('?')
                sys.stdout.flush()
            move_or_copy(fairfax_file.full_path, for_review_folder + "/" +
                         EXISTS_IN_POST_PROCESSING_BUT_NOT_THE_SAME_FILE_FOLDER_NAME)
        else:
            target_file_name = fairfax_file.file_name
            target_folder_for_file = pre_processing_folder + "/" + fairfax_file.file_date_string + "/" + title_code
            if verbose:
                print("target_folder_for_file=" + target_folder_for_file)
            if verbose:
                print(starting_date.strftime(DATE_DISPLAY_FORMAT) + " <= " +
                      file_date.strftime(DATE_DISPLAY_FORMAT) + " < =" + ending_date.strftime(DATE_DISPLAY_FORMAT))
            make_directory_path(target_folder_for_file)
            candidate_target_name = target_folder_for_file + "/" + target_file_name
            target_file_name = candidate_target_name
            if is_file_or_directory(candidate_target_name):
                if are_files_the_same(fairfax_file.full_path, candidate_target_name):
                    process_file = False
                    if verbose:
                        print("")
                        print("File already exists and same (no overwrite), file=" + fairfax_file.full_path)
                    else:
                        sys.stdout.write('+')
                        sys.stdout.flush()
                    if move_files:
                        delete_file(fairfax_file.full_path)
                else:
                    process_file = True
                    target_file_name = non_duplicate_filename(candidate_target_name)
                    print("")
                    timestamp_message("WARNING Duplicate named but different md5 hash file=" + candidate_target_name +
                                      ", renamed to=" + target_file_name)
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
            print("Processing file=" + fairfax_file.full_path)
        else:
            sys.stdout.write('.')
            sys.stdout.flush()
        move_or_copy(fairfax_file.full_path, actual_target)

    return process_file


def pre_process_for_unprocessed_mets_xml_file(fairfax_file, unprocessed_mets_folder):
    # This is an unprocessed mets.xml file, which means that it wasn't ingested for some reason.
    # We assume that the pdfs associated with this file have already been pre-processed but we do want to capture
    # what the title_code and date that are associated with the file itself before we move/copy it to the
    # unprocessed_mets_folder (also because it makes the file unique)
    target_filename_prefix = fairfax_file.dirname.replace(source_folder, "")
    target_filename = convert_to_filename(target_filename_prefix) + "_" + fairfax_file.file_name
    move_or_copy(fairfax_file.full_path, unprocessed_mets_folder + "/" + target_filename)
    sys.stdout.write('.')
    sys.stdout.flush()


def pre_process_for_other_file(fairfax_file, unprocessed_other_folder):
    # This is an unprocessed file, which means that it wasn't ingested for some reason.
    # We assume that the pdfs associated with this file have already been pre-processed but we do want to capture
    # what the title_code and date that are associated with the file itself before we move/copy it to the
    # unprocessed_other_folder (also because it makes the file unique)
    target_filename_prefix = fairfax_file.dirname.replace(source_folder, "")
    target_filename = convert_to_filename(target_filename_prefix) + "_" + fairfax_file.file_name
    move_or_copy(fairfax_file.full_path, unprocessed_other_folder + "/" + target_filename)
    sys.stdout.write('.')
    sys.stdout.flush()


def pre_process_via_going_through_all_files(all_files):
    unprocessed_mets_folder = for_review_folder + "/UNPROCESSED/METS"
    make_directory_path(unprocessed_mets_folder)
    unprocessed_other_folder = for_review_folder + "/UNPROCESSED/OTHER"
    make_directory_path(unprocessed_other_folder)
    exists_in_post_but_not_same_file_folder_name = for_review_folder + "/" +\
                                                   EXISTS_IN_POST_PROCESSING_BUT_NOT_THE_SAME_FILE_FOLDER_NAME
    make_directory_path(exists_in_post_but_not_same_file_folder_name)

    current_file_count = 0
    pdf_files_checked_count = 0
    pdf_files_processed_count = 0
    mets_xml_files_processed_count = 0
    other_files_processed_count = 0
    total_files = len(all_files)
    for fairfax_file in all_files:
        if fairfax_file.is_fairfax_pdf_file:
            is_processed = pre_process_for_given_pdf_file(fairfax_file, target_pre_process_folder,
                                                          target_post_process_folder)
            if is_processed:
                pdf_files_processed_count += 1
            pdf_files_checked_count += 1
        elif pre_process_include_non_pdf_files and fairfax_file.is_mets_xml_file:
            pre_process_for_unprocessed_mets_xml_file(fairfax_file, unprocessed_mets_folder)
            mets_xml_files_processed_count += 1
        elif pre_process_include_non_pdf_files:
            pre_process_for_other_file(fairfax_file, unprocessed_other_folder)
            other_files_processed_count += 1

        current_file_count += 1
        if current_file_count % 5000 == 0:
            print("")
            timestamp_message("Processing status: " + str(current_file_count) + "/" + str(total_files))

    print("")
    timestamp_message("Processing completed: " + str(current_file_count) + "/" + str(total_files))
    timestamp_message("    PDF files checked=" + str(pdf_files_checked_count) +
                      ", processed=" + str(pdf_files_processed_count))
    timestamp_message("    mets.xml files processed=" + str(mets_xml_files_processed_count))
    timestamp_message("    other files processed=" + str(other_files_processed_count))


def list_unique_files(all_files):
    unique_files = set([])
    for fairfax_file in all_files:
        if fairfax_file.is_fairfax_pdf_file and starting_date <= fairfax_file.file_date <= ending_date:
            unique_files.add(fairfax_file.file_name)

    unique_files_list = []
    for file_name in unique_files:
        unique_files_list.append(FairfaxFile(file_name))

    unique_files_list.sort(key=lambda fairfax_file: fairfax_file.file_date)

    print("")
    timestamp_message("Files by name sorted by date")
    for fairfax_file in unique_files_list:
        print(fairfax_file.file_name)
    print("")


def processing_loop():
    if do_pre_processing:
        all_files = get_all_files(source_folder)
        pre_process_via_going_through_all_files(all_files)
    elif do_post_processing:
        all_done_files = get_all_named_files(source_folder, "done")
        post_process_via_going_through_all_done_files(all_done_files)
    elif do_list_unique_files:
        # We are really only looking for unique pdf files
        all_pdf_files = get_all_suffixed_files(source_folder, ".pdf")
        list_unique_files(all_pdf_files)

    # for index in range(0, 5):
    #    print("Getting md5sum for file=" + all_files[index] + ", type=" + str(type(all_files[index])))
    #    get_md5_sum(all_files[index])
    #    print("Non-duplicate for file=" + non_duplicate_filename(all_files[index]))


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

    display_processing_legend()

    timestamp_message("STARTED")

    if test:
        do_tests()
    elif not unacceptable_parameters:
        processing_loop()

    print("")
    timestamp_message("ENDED")


main()


