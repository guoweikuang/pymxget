import os
import shutil
import sys

import setuptools

import mxget

here = os.path.abspath(os.path.dirname(__file__))

required = [
    'aiofiles',
    'aiohttp',
    'click',
    'cryptography',
    'mutagen',
]


class TestCommand(setuptools.Command):
    """Support setup.py test."""

    description = 'Run unit tests.'
    user_options = []

    @staticmethod
    def status(msg):
        """Prints things in bold."""
        print('\033[1m{0}\033[0m'.format(msg))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        self.status('Running unit tests…')
        os.system('{} -m unittest discover -s {} -v'.format(sys.executable, os.path.join(here, "tests")))
        sys.exit(0)


class PublishCommand(setuptools.Command):
    """Support setup.py publish."""

    description = 'Build and publish the package.'
    user_options = []

    @staticmethod
    def status(msg):
        """Prints things in bold."""
        print('\033[1m{0}\033[0m'.format(msg))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status('Removing previous builds…')
            shutil.rmtree(os.path.join(here, "dist"))
        except FileNotFoundError:
            pass
        self.status('Building Source distribution…')
        os.system('{} setup.py sdist bdist_wheel'.format(sys.executable))
        self.status("Uploading the package to PyPI via Twine…")
        os.system("twine upload dist/*")
        self.status("Pushing git tags…")
        os.system("git tag v{0}".format(mxget.__version__))
        os.system("git push --tags")
        sys.exit(0)


def long_description():
    with open('README.md', encoding='utf-8') as f:
        return f.read()


setuptools.setup(
    name='mxget',
    version=mxget.__version__,
    description=mxget.__doc__.strip(),
    long_description=long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/winterssy/pymxget",
    author=mxget.__author__,
    author_email="winterssy@foxmail.com",
    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': [
            'mxget = mxget.__main__:cli',
        ],
    },
    install_requires=required,
    python_requires='>=3.5.3',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console'
        'Environment :: Web Environment'
        'Intended Audience :: Developers'
        'Intended Audience :: End Users/Desktop'
        'License :: OSI Approved :: GNU Affero General Public License v3'
        'Operating System :: OS Independent'
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3 :: Only'
        'Topic :: Internet'
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Multimedia'
        'Topic :: Multimedia :: Sound/Audio'
        'Topic :: Software Development',
        'Topic :: Terminals',
        'Topic :: Utilities'
    ],
    cmdclass={
        "test": TestCommand,
        "publish": PublishCommand,
    },
)
