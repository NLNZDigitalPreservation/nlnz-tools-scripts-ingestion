#!/usr/bin/env python
# SunOS:
#!/usr/bin/python2.7

# daily-file-usage-report.py
# Requires source_folder, reports_folder.
# Uses number_previous_days.
# Optional create_reports_folder, include_file_details_in_console_output, verbose, test, debug.

import argparse
import datetime
import os
import platform
import subprocess
import sys
import time

is_sun_os = False
unacceptable_parameters = False
source_folder = ""
reports_folder = ""

DATE_PARSE_FORMAT = "%Y%m%d"
DATE_DISPLAY_FORMAT = "%Y-%m-%d"
DATE_TIME_DISPLAY_FORMAT = "%Y-%m-%d %H:%M:%S"

FILENAME_UNSAFE_CHARACTERS = " *$"
REPLACEMENT_FILENAME_SAFE_CHARACTER = "-"
FILE_PATH_SEPARATORS = "/\\"
REPLACEMENT_FILE_PATH_SEPARATOR = "_"

ZERO_LENGTH_FILE_MD5_HASH = "d41d8cd98f00b204e9800998ecf8427e"

CSV_COLUMN_SEPARATOR_CHARACTER = "|"
CSV_COLUMN_SEPARATOR = CSV_COLUMN_SEPARATOR_CHARACTER + " "

DIRECTORY_DETAILS_CSV_TITLE = "Root directory details"
DIRECTORY_DETAILS_CSV_HEADER = "directory path" + CSV_COLUMN_SEPARATOR + "root folder name" + CSV_COLUMN_SEPARATOR +\
                               "date (yyyy-MM-dd)"
SUBDIRECTORY_STATISTICS_CSV_TITLE = "Subdirectory statistics"
SUBDIRECTORY_STATISTICS_CSV_HEADER = "subdirectory name" + CSV_COLUMN_SEPARATOR + "date (yyyy-MM-dd)" +\
                                     CSV_COLUMN_SEPARATOR + "total size" + CSV_COLUMN_SEPARATOR + "number of folders" +\
                                     CSV_COLUMN_SEPARATOR + "number of files"

DIRECTORY_STATISTICS_COMPARISON_CSV_TITLE = "Subdirectory statistics comparisons with previous dates"
DIRECTORY_STATISTICS_COMPARISON_CSV_HEADER = "subdirectory name" + CSV_COLUMN_SEPARATOR + "date (yyyy-MM-dd)" +\
                                             CSV_COLUMN_SEPARATOR + "total size" + CSV_COLUMN_SEPARATOR +\
                                             "change in size" + CSV_COLUMN_SEPARATOR + "number of folders" +\
                                             CSV_COLUMN_SEPARATOR + "change in number of folders" +\
                                             CSV_COLUMN_SEPARATOR + "number of files" + CSV_COLUMN_SEPARATOR +\
                                             "change in number of files"
FILE_STATISTICS_CSV_TITLE = "File statistics"
FILE_STATISTICS_CSV_HEADER = "file path" + CSV_COLUMN_SEPARATOR + "file name" + CSV_COLUMN_SEPARATOR + "file size" +\
                             CSV_COLUMN_SEPARATOR + "last modification date" + CSV_COLUMN_SEPARATOR + "md5 hash" +\
                             CSV_COLUMN_SEPARATOR + "notes"

print("Python version: " + platform.python_version() + ", complete: " + str(sys.version_info))


def determine_if_sun_os():
    global is_sun_os
    output = subprocess.check_output(["uname"])
    is_sun_os = "sunos" in str(output).lower()
    print("is_sun_os=" + str(is_sun_os))


def parse_parameters():
    parser = argparse.ArgumentParser(description="daily-file-usage-report.py: Daily file usage report.")
    parser.add_argument('--source_folder', type=str, required=True,
                        help='The root source-folder for the report.')
    parser.add_argument('--reports_folder', type=str, required=True,
                        help='The folder where reports exist and get written.')
    parser.add_argument('--number_previous_days', type=int, default=0,
                        help='The number of previous days to include in the report. The default is 0.')
    parser.add_argument('--create_reports_folder', dest='create_reports_folder', action='store_true',
                        help='Indicates that the reports folder will get created. Otherwise it must already exist.')
    parser.add_argument('--include_file_details_in_console_output', dest='include_file_details_in_console_output',
                        action='store_true', help='Indicates that individual file details will output to the ' +
                                                  'console as well as the reports file.')
    parser.add_argument('--calculate_md5_hash', dest='calculate_md5_hash',
                        action='store_true', help='Calculate and report the md5 hash of individual files ' +
                                                  '(this is a very intensive I/O operation).')
    parser.add_argument('--include_dot_directories', dest='include_dot_directories',
                        action='store_true', help="Include first-level root subdirectories that start with a '.'")
    parser.add_argument('--verbose', dest='verbose', action='store_true',
                        help='Indicates that operations will be done in a verbose manner. ' +
                             'NOTE: This means that no csv report file will be generated.')
    parser.add_argument('--debug', dest='debug', action='store_true',
                        help='Indicates that operations will include debug output.')
    parser.add_argument('--test', dest='test', action='store_true',
                        help='Indicates that only tests will be run.')

    parser.set_defaults(create_reports_folder=False, include_file_details_in_console_output=False,
                        calculate_md5_hash=False, verbose=False, debug=False, test=False)

    args = parser.parse_args()

    return args


def display_parameter_values():
    print("")
    print("Parameters as set:")
    print("    source_folder=" + source_folder)
    print("    reports_folder=" + reports_folder)
    print("    number_previous_days=" + str(number_previous_days))
    print("    create_reports_folder=" + str(create_reports_folder))
    print("    include_file_details_in_console_output=" + str(include_file_details_in_console_output))
    print("    include_dot_directories=" + str(include_dot_directories))
    print("    calculate_md5_hash=" + str(calculate_md5_hash))
    print("    verbose=" + str(verbose))
    print("    debug=" + str(debug))
    print("    test=" + str(test))


# There is no processing legend for this reporting
def display_processing_legend():
    pass


def process_parameters(parsed_arguments):
    global source_folder
    source_folder = parsed_arguments.source_folder
    global reports_folder
    reports_folder = parsed_arguments.reports_folder
    global number_previous_days
    number_previous_days = parsed_arguments.number_previous_days
    global create_reports_folder
    create_reports_folder = parsed_arguments.create_reports_folder
    global include_file_details_in_console_output
    include_file_details_in_console_output = parsed_arguments.include_file_details_in_console_output
    global calculate_md5_hash
    calculate_md5_hash = parsed_arguments.calculate_md5_hash
    global include_dot_directories
    include_dot_directories = parsed_arguments.include_dot_directories
    global verbose
    verbose = parsed_arguments.verbose
    global debug
    debug = parsed_arguments.debug
    global test
    test = parsed_arguments.test

    global move_or_copy_flags
    global unacceptable_parameters

    display_parameter_values()

    if number_previous_days < 0:
        print("")
        print("ERROR number_previous_days=" + str(number_previous_days) + " must be >= 0")
        unacceptable_parameters = True

    print("")

    if verbose and not is_sun_os:
        move_or_copy_flags = "-v"
    else:
        move_or_copy_flags = ""

    if is_directory(source_folder):
        print("source_folder=" + source_folder + " exists and is directory, processing can take place.")
    else:
        print("ERROR source_folder=" + source_folder + " does not exist or is not a directory. It must exist!")
        unacceptable_parameters = True

    print("")

    if is_directory(reports_folder):
        print("reports_folder=" + reports_folder + " exists and is directory.")
    else:
        if create_reports_folder:
            print("Creating " + reports_folder)
            make_directory_path(reports_folder)
        else:
            print("ERROR create_reports_folder=" + create_reports_folder + ", therefore reports_folder=" +
                  reports_folder + " must exist!")
            unacceptable_parameters = True

    print("")

    if unacceptable_parameters:
        print("")
        print("Parameters are incomplete or incorrect. Please try again.")
        print("")


class DirectoryDetails:
    def __init__(self, name, path, date, directory_statistics_collection):
        self.name = name
        self.path = path
        self.date = date
        self.directory_statistics_collection = directory_statistics_collection

    @classmethod
    def for_directory(cls, root_directory):
        directory_name = os.path.basename(root_directory)
        directory_root = os.path.dirname(root_directory)
        directory_statistics_collection = []
        the_subdirectories = immediate_subdirectories(root_directory)
        for subdirectory in the_subdirectories:
            directory_statistics = DirectoryStatistics.calculate_for_directory(subdirectory)
            directory_statistics_collection.append(directory_statistics)

        the_date = datetime.datetime.now()
        return cls(directory_name, directory_root, the_date, directory_statistics_collection)

    @classmethod
    def from_file(cls, report_date, root_directory, report_file):
        directory_name = os.path.basename(root_directory)
        directory_root = os.path.dirname(root_directory)
        directory_statistics_collection = DirectoryStatistics.load_collection_from_file(root_directory, report_file)

        return cls(directory_name, directory_root, report_date, directory_statistics_collection)

    def total_size(self):
        total_for_all_directories = 0
        for directory_statistics in self.directory_statistics_collection:
            total_for_all_directories += directory_statistics.total_size

        return total_for_all_directories

    def formatted_output(self):
        the_output = "" + self.path + "/" + self.name + ":\n"
        for directory_statistics in self.directory_statistics_collection:
            the_output += directory_statistics.formatted_output() + "\n"

        the_output += "total size=" + format_storage_size(self.total_size()) + "\n"

        return the_output

    def csv_output(self, include_directory_path):
        the_output = ""
        if include_directory_path:
            the_output += self.path + CSV_COLUMN_SEPARATOR
        the_output += self.name + CSV_COLUMN_SEPARATOR + self.date.strftime(DATE_DISPLAY_FORMAT)

        return the_output


class DirectoryStatistics:
    def __init__(self, root_directory, date, number_of_files, number_of_folders, total_size, all_files):
        self.directory_name = os.path.basename(root_directory)
        self.directory_root = os.path.dirname(root_directory)
        self.date = date
        self.number_of_files = number_of_files
        self.number_of_folders = number_of_folders
        self.total_size = total_size
        self.all_files = all_files

    @classmethod
    def calculate_for_directory(cls, root_directory):
        the_date = datetime.datetime.now()
        the_size = 0
        the_number_of_files = 0
        files_list = []
        the_number_of_folders = 0
        for dirpath, dirnames, filenames in os.walk(root_directory):
            the_number_of_folders += 1
            for the_filename in filenames:
                the_number_of_files += 1
                file_path = os.path.join(dirpath, the_filename)
                file_size = os.path.getsize(file_path)
                file_creation_date = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                file_md5_hash = get_md5_sum(file_path) if calculate_md5_hash else "<not-calculated>"
                file_statistics = FileStatistics(the_filename, dirpath, file_size, file_creation_date, file_md5_hash)
                files_list.append(file_statistics)
                the_size += file_size
        return cls(root_directory, the_date, the_number_of_files, the_number_of_folders, the_size, files_list)

    @classmethod
    def load_from_line(cls, directory_root, report_line):
        try:
            components = [component.strip() for component in report_line.split(CSV_COLUMN_SEPARATOR_CHARACTER)]
            print_debug("components=" + str(components))
            directory_name = components[0]
            the_date = convert_string_to_date(components[1], DATE_DISPLAY_FORMAT)
            the_size = extract_storage_size(components[2])
            the_number_of_folders = int(components[3].replace(",", "").strip())
            the_number_of_files = int(components[4].replace(",", "").strip())
            # Don't try to recreate the files list
            files_list = []
        except argparse.ArgumentTypeError:
            raise ValueError
        root_directory = os.path.join(directory_root, directory_name)
        return cls(root_directory, the_date, the_number_of_files, the_number_of_folders, the_size, files_list)

    @staticmethod
    def load_collection_from_file(directory_root, report_file_path):
        print_debug("loading from: " + report_file_path)
        report_file = open(report_file_path)
        directory_statistics_started = False
        directory_statistics_ended = False
        directory_statistics_list = []
        report_file_lines = report_file.readlines()
        for report_file_line in report_file_lines:
            if report_file_line.startswith(SUBDIRECTORY_STATISTICS_CSV_HEADER):
                directory_statistics_started = True
            elif directory_statistics_started and not directory_statistics_ended:
                print_debug("loading from: " + report_file_path + " with report_file_line=" + report_file_line)
                try:
                    directory_statistics = DirectoryStatistics.load_from_line(directory_root, report_file_line)
                    print_debug("extracted directory_statistics=" + directory_statistics.csv_output())
                    directory_statistics_list.append(directory_statistics)
                except (ValueError, IndexError) as e:
                    print_debug("exception=" + str(e) + ", Unable to load line=" + report_file_line + ", from: " +
                                report_file_path)
                    directory_statistics_ended = True
        return directory_statistics_list

    def formatted_output(self):
        the_output = "directory_root=" + self.directory_root + ", directory_name=" + self.directory_name +\
                     "date=" + self.date.strftime(DATE_DISPLAY_FORMAT) + CSV_COLUMN_SEPARATOR + "total size=" +\
                     format_storage_size(self.total_size) + ", number of folders=" +\
                     "{:,}".format(self.number_of_folders) + ", number of files=" +\
                     "{:,}".format(self.number_of_files)

        return the_output

    def csv_output(self):
        the_output = "" + self.directory_name + CSV_COLUMN_SEPARATOR + self.date.strftime(DATE_DISPLAY_FORMAT) +\
                     CSV_COLUMN_SEPARATOR + format_storage_size(self.total_size) +\
                     CSV_COLUMN_SEPARATOR + "{:,}".format(self.number_of_folders) + CSV_COLUMN_SEPARATOR +\
                     "{:,}".format(self.number_of_files)

        return the_output

    def csv_output_comparison(self, current_directory_details):
        print_debug("comparing self=" + self.csv_output() + " WITH current=" + current_directory_details.csv_output())
        change_in_number_files = current_directory_details.number_of_files - self.number_of_files
        change_in_number_folders = current_directory_details.number_of_folders - self.number_of_folders
        change_in_total_size = current_directory_details.total_size - self.total_size
        include_positive_sign = True
        the_output = "" + self.directory_name + CSV_COLUMN_SEPARATOR + self.date.strftime(DATE_DISPLAY_FORMAT) +\
                     CSV_COLUMN_SEPARATOR + format_storage_size(self.total_size) + CSV_COLUMN_SEPARATOR +\
                     format_storage_size(change_in_total_size, include_positive_sign) + CSV_COLUMN_SEPARATOR +\
                     "{:,}".format(self.number_of_folders) + CSV_COLUMN_SEPARATOR +\
                     "{:+,}".format(change_in_number_folders) + CSV_COLUMN_SEPARATOR +\
                     "{:,}".format(self.number_of_files) + CSV_COLUMN_SEPARATOR + "{:+,}".format(change_in_number_files)

        return the_output


class FileStatistics:
    def __init__(self, name, path, size, modification_date, md5_hash):
        self.name = name
        self.path = path
        self.size = size
        self.modification_date = modification_date
        self.md5_hash = md5_hash

    def formatted_output(self):
        the_output = "" + self.path + "/" + self.name + ", size=" + format_storage_size(self.size) +\
                     ", modification date=" + self.modification_date.strftime(DATE_TIME_DISPLAY_FORMAT) +\
                     ", md5 hash=" + self.md5_hash
        if self.md5_hash == ZERO_LENGTH_FILE_MD5_HASH:
            the_output += " -- WARNING: zero-length MD5 hash!"

        return the_output

    def csv_output(self, directory_path_to_strip=""):
        path_to_show = self.path.replace(directory_path_to_strip, ".")
        the_output = "" + path_to_show + CSV_COLUMN_SEPARATOR + self.name + CSV_COLUMN_SEPARATOR +\
                     format_storage_size(self.size) + CSV_COLUMN_SEPARATOR +\
                     self.modification_date.strftime(DATE_TIME_DISPLAY_FORMAT) + CSV_COLUMN_SEPARATOR + self.md5_hash
        if self.md5_hash == ZERO_LENGTH_FILE_MD5_HASH:
            the_output += CSV_COLUMN_SEPARATOR + "WARNING: zero-length MD5 hash!"

        return the_output


class FileDetails:
    def __init__(self, name, path, size, creation_date, md5_hash):
        self.name = name
        self.path = path
        self.size = size
        self.creation_date = creation_date
        self.md5_hash = md5_hash

    @classmethod
    def create_from_file(cls, source_file):
        return cls(source_file.name, source_file.path, source_file.size, source_file.creation_date,
                   get_md5_sum(source_file))


def is_directory(directory_path):
    return os.path.exists(directory_path) and not os.path.isfile(directory_path)


def is_file(file_path):
    return os.path.exists(file_path) and os.path.isfile(file_path)


def is_file_or_directory(file_path):
    return os.path.exists(file_path)


def make_directory_path(directory_path):
    if not is_directory(directory_path):
        os.makedirs(directory_path)


def immediate_subdirectories(root_directory):
    the_subdirectories = []
    for name in os.listdir(root_directory):
        potential_subdirectory = os.path.join(root_directory, name)
        if is_directory(potential_subdirectory):
            include_subdirectory = True
            if name.startswith("."):
                include_subdirectory = include_dot_directories
            if include_subdirectory:
                the_subdirectories.append(potential_subdirectory)

    return the_subdirectories


def convert_string_to_date(date_string, parse_format=DATE_PARSE_FORMAT):
    try:
        return datetime.datetime.strptime(date_string, parse_format).date()
    except ValueError:
        raise argparse.ArgumentTypeError(date_string + " is not a proper date string in the format 'yyyyMMdd'")


def format_storage_size(storage_size_in_bytes, include_positive_sign=False):
    if abs(storage_size_in_bytes) < 1000:
        if include_positive_sign:
            return "{:+,}".format(int(storage_size_in_bytes))
        else:
            return "{:,}".format(int(storage_size_in_bytes))

    float_size = float(storage_size_in_bytes)
    if include_positive_sign:
        formatting = "{:+,.3f}"
    else:
        formatting = "{:,.3f}"

    if abs(float_size / 1024) < 1000:
        adjusted_float_size = float_size / 1024
        units = "KB"
    elif abs(float_size / (1024**2)) < 1000:
        adjusted_float_size = float_size / (1024**2)
        units = "MB"
    elif abs(float_size / (1024**3)) < 1000:
        adjusted_float_size = float_size / (1024**3)
        units = "GB"
    else:
        adjusted_float_size = float_size / (1024**4)
        units = "TB"

    format_with_units = formatting + " " + units
    return format_with_units.format(adjusted_float_size)


def extract_storage_size(storage_size_string):
    multiplier = 1
    if storage_size_string.endswith("KB"):
        multiplier = 1024
        source_number = storage_size_string.replace("KB", "")
    elif storage_size_string.endswith("MB"):
        multiplier = 1024**2
        source_number = storage_size_string.replace("MB", "")
    elif storage_size_string.endswith("GB"):
        multiplier = 1024**3
        source_number = storage_size_string.replace("GB", "")
    elif storage_size_string.endswith("TB"):
        multiplier = 1024**4
        source_number = storage_size_string.replace("TB", "")
    else:
        source_number = storage_size_string
    source_number = source_number.strip().replace(",", "")
    return float(source_number) * multiplier


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


def print_debug(message):
    if debug:
        print("D E B U G " + message)


def print_and_report(output, output_file, include_console_output=True):
    if include_console_output:
        print(output)
        sys.stdout.flush()
    if output_file is not None:
        output_file.write(output)
        output_file.write("\n")
        output_file.flush()


def reports_file_name_for_date_and_folder(report_date, report_root_folder):
    formatted_date = report_date.strftime(DATE_DISPLAY_FORMAT)
    the_safe_folder = convert_to_filename(report_root_folder)
    report_file_name = os.path.join(reports_folder, formatted_date + "_" + the_safe_folder + ".csv")

    return report_file_name


def load_previous_report(report_date, days_offset, root_folder, the_reports_folder):
    previous_date = report_date - datetime.timedelta(days=days_offset)
    report_file_name_only = reports_file_name_for_date_and_folder(previous_date, root_folder)
    report_file_full_path = os.path.join(the_reports_folder, report_file_name_only)
    directory_details = None
    if is_file(report_file_full_path):
        directory_details = DirectoryDetails.from_file(report_date, root_folder, report_file_full_path)

    return directory_details


# Provides a report for all the directories under the root_folder.
#
# The directories report is intended to show the following:
# - The number of files in each directory.
# - The total size of the directory.
# - The change in the number of files and total size over a given period of days.
def directories_report(root_folder):
    current_directory_details = DirectoryDetails.for_directory(root_folder)
    the_date = datetime.datetime.now()

    previous_directory_details = []
    if number_previous_days > 0:
        for days_ago in range(1, number_previous_days):
            past_directory_details = load_previous_report(the_date, days_ago, root_folder, reports_folder)
            if past_directory_details is not None:
                previous_directory_details.append(past_directory_details)

    print_debug("previous_directory_details.len=" + str(len(previous_directory_details)))
    if verbose:
        report_file = None
    else:
        formatted_date = the_date.strftime(DATE_DISPLAY_FORMAT)
        formatted_date_time = the_date.strftime(DATE_TIME_DISPLAY_FORMAT)
        report_file_name_only = reports_file_name_for_date_and_folder(the_date, root_folder)
        report_file_full_name = os.path.join(reports_folder, report_file_name_only)
        report_file = open(report_file_full_name, "a+")
        print_and_report("", report_file)
        print_and_report("date=" + formatted_date, report_file)
        print_and_report("date_time=" + formatted_date_time, report_file)
        print_and_report("root_folder=" + root_folder, report_file)
        print_and_report("report_file=" + report_file_full_name, report_file)

    if verbose:
        print(current_directory_details.formatted_output())
    else:
        print_and_report("", report_file)
        print_and_report(DIRECTORY_DETAILS_CSV_TITLE, report_file)
        print_and_report(DIRECTORY_DETAILS_CSV_HEADER, report_file)
        include_directory_path = True
        print_and_report(current_directory_details.csv_output(include_directory_path), report_file)
        print_and_report("", report_file)
        print_and_report(SUBDIRECTORY_STATISTICS_CSV_TITLE, report_file)
        print_and_report(SUBDIRECTORY_STATISTICS_CSV_HEADER, report_file)
        for directory_statistics in current_directory_details.directory_statistics_collection:
            print_and_report(directory_statistics.csv_output(), report_file)
        print_and_report(CSV_COLUMN_SEPARATOR + "Total size" + CSV_COLUMN_SEPARATOR +
                         format_storage_size(current_directory_details.total_size()), report_file)
        print_and_report("", report_file)
        if len(previous_directory_details) > 0:
            print_and_report(DIRECTORY_STATISTICS_COMPARISON_CSV_TITLE, report_file)
            print_and_report(DIRECTORY_STATISTICS_COMPARISON_CSV_HEADER, report_file)
            print_debug("len(current_directory_details.directory_statistics_collection)=" +
                        str(len(current_directory_details.directory_statistics_collection)))
            for directory_statistics in current_directory_details.directory_statistics_collection:
                directory_root = directory_statistics.directory_root
                directory_name = directory_statistics.directory_name
                print_debug("len(previous_directory_details)=" + str(len(previous_directory_details)))
                for past_directory_details in previous_directory_details:
                    print_debug("len(past_directory_details.directory_statistics_collection)=" +
                                str(len(past_directory_details.directory_statistics_collection)))
                    for previous_directory_statistics in past_directory_details.directory_statistics_collection:
                        print_debug("directory_statistics.directory_root=" + directory_statistics.directory_root)
                        print_debug("previous_directory_statistics.directory_root=" +
                                    previous_directory_statistics.directory_root)
                        print_debug("directory_statistics.directory_name=" + directory_statistics.directory_name)
                        print_debug("previous_directory_statistics.directory_name=" +
                                    previous_directory_statistics.directory_name)
                        directory_root_matches = directory_root == previous_directory_statistics.directory_root
                        directory_name_matches = directory_name == previous_directory_statistics.directory_name
                        if directory_root_matches and directory_name_matches:
                            print_debug("MATCH")
                            print_and_report(previous_directory_statistics.csv_output_comparison(directory_statistics),
                                             report_file)

    print_and_report("", report_file)

    if not verbose:
        print_and_report(FILE_STATISTICS_CSV_TITLE, report_file, include_file_details_in_console_output)
        print_and_report(FILE_STATISTICS_CSV_HEADER, report_file, include_file_details_in_console_output)

    for directory_statistics in current_directory_details.directory_statistics_collection:
        for file_statistics in directory_statistics.all_files:
            if verbose:
                print(file_statistics.formatted_output())
            else:
                print_and_report(file_statistics.csv_output(root_folder), report_file,
                                 include_file_details_in_console_output)

    if not verbose:
        report_file.close()


def processing_loop():
    directories_report(source_folder)


def do_tests():
    for storage_size in [123, 123456.7891, 12345678.9012, 12345678901.2345, 123456789012345.6789,
                         -123, -123456.7891, -12345678.9012, -12345678901.2345, -123456789012345.6789]:
        print("storage_size=" + str(storage_size) + ", format_storage_size=" + format_storage_size(storage_size))
        print("storage_size=" + str(storage_size) + ", format_storage_size(+)=" +
              format_storage_size(storage_size, True))


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
