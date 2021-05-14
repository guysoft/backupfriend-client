import setuptools

with open("README.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="backupfriend",
    version="0.1.0",
    description="Read the latest Real Python tutorials",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/guysoft/BackupFriend",
    author="Guy Sheffer",
    author_email="gusyoft@gmail.com",
    license="GPLv3",
    py_modules=["backupfriendclient"],
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],
    packages=setuptools.find_packages(where="src"),
    package_dir={
        "": "src",
    },
    data_files=[('images', ['src/backupfriend/images/icon.png']),
                ('config', ['src/backupfriend/config/config.yml']),
                ('res', ['src/backupfriend/res/main.xrc'])],
    include_package_data=True,
    install_requires=[
        "wxPython", "PyYAML", "schedule", 'dataclasses;python_version<"3.7"',
        "appdirs", "rdiff-backup", "cryptography"
    ],
    entry_points={"console_scripts": ["backupfriend=backupfriendclient:run"]},
)
