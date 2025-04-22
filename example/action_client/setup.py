from setuptools import setup

package_name = 'action_client'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Lukas Zanger',
    maintainer_email='lukas.zanger@rwth-aachen.de',
    description='Example action client for the application manager',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'deployment_vehicle00_approaching = action_client.deployment_vehicle00_approaching:main',
            'deployment_vehicle01_approaching = action_client.deployment_vehicle01_approaching:main',
            'shutdown_vehicle00_leaving = action_client.shutdown_vehicle00_leaving:main',
            'shutdown_vehicle01_leaving = action_client.shutdown_vehicle01_leaving:main',
        ],
    },
)
