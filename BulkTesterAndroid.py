'''
Created by Shane Jansen on 1/26/17

ANDROID_HOME environment variable must be set.

Ask for package name of tests
Remove imports from tests containing the package name
Add espreso packages to gradle
Remove local.properties
Store package name
import package name . *
'''

import os
import shutil
import subprocess

class AndroidProject:
    title = ''
    path = ''
    passed_tests = False

    def __init__(self, title, path):
        self.title = title
        self.path = path

'''
Returns a list of directories only in a given path.
'''
def list_directories(path):
    return os.walk(path).next()[1]

'''
Returns a valid path specified by the user.
'''
def get_directory_path(message):
    is_valid_path = False
    while not is_valid_path:
        input = raw_input(message).strip()
        is_valid_path = os.path.isdir(input)
        if not is_valid_path: print('Invalid directory')
    return input

'''
Returns a list of AndroidProject objects based on the given initial directory.
'''
def get_android_projects(path):
    directories = list_directories(path)
    android_projects = []
    for directory in directories:
        contents = list_directories(path + '/' + directory)
        android_project = AndroidProject(directory, path + '/' + directory)
        if 'app' in contents: android_projects.append(android_project)
    return android_projects


instrumented_tests_path = get_directory_path('Enter the path to the Instrumented Tests (androidTest): ')
projects_path = get_directory_path('Enter the path to the projects under test: ')
android_projects = get_android_projects(projects_path)

# Run each Instrumented Test
for android_project in android_projects:
    # Remove the original Instrumented Tests
    shutil.rmtree(android_project.path + '/app/src/androidTest', True)
    # Copy the supplied Instrumented Tests
    shutil.copytree(instrumented_tests_path, android_project.path + '/app/src/androidTest')
    # Run the tests
    print('Running: ' + android_project.title)
    return_code = subprocess.call("./gradlew connectedAndroidTest", cwd=android_project.path, shell=True)
    print(return_code)

# Generate results
results_path = projects_path + '/TestResults.txt'
# Delete old results
os.remove(results_path)
# Create results file
results = open(results_path, 'w')
results.write('this is a test')
results.close()
