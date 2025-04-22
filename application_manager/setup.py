import os
from glob import glob
from setuptools import setup, find_packages

package_name = 'application_manager'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(include=[package_name, package_name + ".*"]),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        (os.path.join('share', package_name), ['package.xml']),
        (os.path.join('share', package_name,
                        'launch'), glob('launch/*launch.[pxy][yma]*')),
        (os.path.join('share', package_name,
                        'config'), glob('config/*.json') + glob('config/*.yml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Lukas Zanger',
    maintainer_email='lukas.zanger@rwth-aachen.de',
    description='Application Manager',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'application_manager = application_manager.application_manager:main'
        ],
    },
)
