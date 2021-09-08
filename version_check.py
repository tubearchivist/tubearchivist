#!/usr/bin/env python
""" check requirements.txt for outdated packages """

import sys

import requests


class Requirements:
    """ handle requirements.txt """

    FILE_PATH = 'tubearchivist/requirements.txt'

    def __init__(self):
        self.all_requirements = self.get_dependencies()
        self.all_updates = self.check_packages()

    def get_dependencies(self):
        """ read out requirements.txt """

        all_requirements = []
        with open(self.FILE_PATH, 'r', encoding='utf-8') as f:
            dependencies = f.readlines()

        for dependency in dependencies:
            package, version = dependency.split('==')
            all_requirements.append((package, version.strip()))

        all_requirements.sort(key = lambda x: x[0].lower())

        return all_requirements

    def check_packages(self):
        """ compare installed with remote version """

        total = len(self.all_requirements)
        print(f'checking versions for {total} packages...')

        all_updates = {}

        for dependency in self.all_requirements:
            package, version_installed = dependency
            url = f'https://pypi.org/pypi/{package}/json'
            response = requests.get(url).json()
            version_remote = response['info']['version']
            homepage = response['info']['home_page']
            if version_remote != version_installed:
                to_update = {
                    package: {
                        "from": version_installed,
                        "to": version_remote
                    }
                }
                all_updates.update(to_update)
                message = (f'update {package} {version_installed}' +
                           f'==> {version_remote}\n    {homepage}')
                print(message)

        if not all_updates:
            print('no updates found')

        return all_updates

    def apply_updates(self):
        """ update requirements.txt file with new versions """

        to_write = []

        for requirement in self.all_requirements:
            package, old_version = requirement

            if package in self.all_updates.keys():
                package_version = self.all_updates[package]['to']
            else:
                package_version = old_version

            to_write.append(f'{package}=={package_version}\n')

        with open(self.FILE_PATH, 'w', encoding='utf-8') as f:
            f.writelines(to_write)

        print('requirements.txt updates')


if __name__ == "__main__":
    handler = Requirements()
    if handler.all_updates:
        input_response = input('\nupdate requirements.txt? [y/n] ')
        if input_response == 'y':
            handler.apply_updates()
        else:
            print('cancle update...')
            sys.exit(1)
