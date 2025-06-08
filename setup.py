from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name='train_tools',
    version='1.0.0',
    description='训练辅助工具',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='leletxh',
    author_email='wanyouximc@outlook.com',
    url='https://github.com/leletxh/train-tools/',
    install_requires=[
        "flask",
        "flask_socketio",
        "psutil",
        "GPUtil",
        "requests"
    ],
    license='MIT',
    packages=find_packages(),
    platforms=["any"],
    classifiers=[
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Natural Language :: Chinese (Simplified)',
        'Programming Language :: Python :: 3.8',
        'Topic :: Software Development :: Libraries',
        'License :: OSI Approved :: MIT License',
    ],
)
