"""
Created by Shane Jansen on 1/26/17

ANDROID_HOME environment variable must be set.

Ask for package name of tests
Remove imports from tests containing the package name
Add espreso packages to gradle
"""

import os
import sys
import shutil
import subprocess

DEPENDENCIES = ['com.android.support:support-annotations:25.1.0',
                'com.android.support.test:runner:0.5',
                'com.android.support.test:rules:0.5',
                'com.android.support.test.espresso:espresso-core:2.2.2',
                'com.android.support.test.espresso:espresso-intents:2.2.2']


class AndroidProject:
    title = ''
    path = ''
    package_name = ''
    did_pass_tests = False
    comments = ''
    did_edit_project_files = False

    def __init__(self, title, path, package_name):
        self.title = title
        self.path = path
        self.package_name = package_name


def list_all_java_files(root_path):
    """
    Returns a list of all Java files in the given directory and all subdirectories.
    :param root_path: Path to begin search
    :return: a list Java files
    """
    java_files = []
    for path, sub_dirs, all_files in os.walk(root_path):
        for all_file in all_files:
            if all_file.find('.java') is not -1:
                java_files.append(path + '/' + all_file)
    return java_files


def list_directories(path):
    """
    Returns a list of directories in a given path.
    :param path: Path to the initial directory
    :return: None if the path does not exist
    """
    try:
        return os.walk(path).next()[1]
    except StopIteration:
        pass


def silent_remove(file_path):
    """
    Removes a file without throwing an exception if it does not exist.
    :param file_path: Path to the file to remove
    :return:
    """
    try:
        os.remove(file_path)
    except OSError:
        pass


def get_directory_path(message):
    """
    Returns a valid path specified by the user.
    :param message: Message to display before user input
    :return: A valid path as specified by the user
    """
    is_valid_path = False
    supplied_path = ''
    while not is_valid_path:
        supplied_path = raw_input(message).strip()
        is_valid_path = os.path.isdir(supplied_path)
        if not is_valid_path: print('Invalid directory')
    return supplied_path


def get_android_projects(path):
    """
    Returns a list of AndroidProject objects based on the given initial directory.
    :param path: Path to the directory containing the Android projects
    :return: A list of paths to Android projects
    """
    directories = list_directories(path)
    projects = []
    for directory in directories:
        path_to_manifest = path + '/' + directory + '/app/src/main/AndroidManifest.xml'
        if os.path.isfile(path_to_manifest):
            manifest = open(path_to_manifest).read()
            package_search_text = 'package="'
            current_index = manifest.find(package_search_text) + len(package_search_text)
            package_name = ''
            while manifest[current_index] is not '"':
                package_name += manifest[current_index]
                current_index += 1
            projects.append(AndroidProject(directory, path + '/' + directory, package_name))
    return projects


def add_required_gradle_dependencies(project):
    """
    Adds all of specified Gradle dependencies to the specified project path
    :param project_path: The Android project
    :return:
    """
    f = open(project.path + '/app/build.gradle', 'r+')
    lines = f.readlines()
    for idx, line in enumerate(lines):
        if line.find('dependencies {') is not -1:
            for idx2, dependency in enumerate(DEPENDENCIES):
                lines.insert(idx + idx2 + 1, 'androidTestCompile \'' + dependency + '\'\n')
    f.seek(0)
    for line in lines:
        f.write(line)
    f.truncate()
    f.close()


def construct_instrumentation_tests(android_project, project_files, tests_files):
    # Construct the import statements from each project file
    new_imports = ['import ' + android_project.package_name + '.*;\n']
    for project_file in project_files:
        new_import = project_file.split(android_project.package_name.replace('.', '/'))
        new_import = 'import ' + android_project.package_name + new_import[1].replace('/', '.')
        if new_import.endswith('.java'):
            new_import = new_import[:-5] + ';\n'
        new_imports.append(new_import)
    # Construct each Instrumentation Test
    for tests_file in tests_files:
        f = open(tests_file, 'r+')
        lines = f.readlines()
        # Insert new imports after the package
        for new_import in new_imports:
            lines.insert(1, new_import)
        f.seek(0)
        for idx, line in enumerate(lines):
            # Do not remove the first line
            if idx is 0 or line.find(tests_package_name) is -1:
                f.write(line)
        f.truncate()
        f.close()
        raw_input('Open ' + tests_file + ' in Android Studio and fix the ids/classes.  Press ENTER to continue: ')

# MAIN
if len(sys.argv) is 4:
    # Get needed input from command line arguments
    instrumented_tests_path = sys.argv[1]
    projects_path = sys.argv[2]
    tests_package_name = sys.argv[3]
else:
    # Ask for needed paths
    instrumented_tests_path = get_directory_path('Enter the path to the Instrumented Tests (androidTest): ')
    projects_path = get_directory_path('Enter the path to the projects under test: ')
    tests_package_name = raw_input('Enter the package name used to create the Instrumented Tests: ')

android_projects = get_android_projects(projects_path)

# Run each Instrumented Test
current_project_index = 0
while current_project_index is not len(android_projects):
    android_project = android_projects[current_project_index]
    print('Testing: ' + android_project.title)
    if not android_project.did_edit_project_files:
        # Remove the project's local.properties
        silent_remove(android_project.path + '/local.properties')
        # Remove the original Instrumented Tests
        shutil.rmtree(android_project.path + '/app/src/androidTest', True)
        # Copy the supplied Instrumented Tests
        shutil.copytree(instrumented_tests_path, android_project.path + '/app/src/androidTest')
        # Get the test and project files
        tests_files = list_all_java_files(android_project.path + '/app/src/androidTest')
        project_files = list_all_java_files(
            android_project.path + '/app/src/main/java/' + android_project.package_name.replace('.', '/'))
        # Add required Gradle dependencies
        add_required_gradle_dependencies(android_project)
        # Construct Instrumentation Tests
        construct_instrumentation_tests(android_project, project_files, tests_files)
        android_project.did_edit_project_files = True
    # Run the tests until the build passes
    execution_code = subprocess.call("./gradlew connectedAndroidTest", cwd=android_project.path, shell=True)
    if execution_code is 0:
        print(android_project.title + ' passed all tests!')
        android_project.did_pass_tests = True
        current_project_index += 1
    else:
        grade = raw_input('Build failed.  Type a grade with reasoning or press ENTER to retry: ')
        if len(grade) is not 0:
            android_project.comments = grade
            current_project_index += 1

# Generate results
results_path = projects_path + '/TestResults.txt'
# Delete old results
silent_remove(results_path)
# Create results file
results = open(results_path, 'w')
for android_project in android_projects:
    if android_project.did_pass_tests:
        pass_result = 'Passed'
    else:
        pass_result = 'Failed - ' + android_project.comments
    results.write(android_project.title + ' - ' + pass_result + '\n')
results.close()

print('Finished testing all projects.  Results are here: ' + projects_path + '/TestResults.txt')
