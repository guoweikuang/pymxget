import setuptools

import mxget

required = [
    'aiofiles',
    'aiohttp',
    'click',
    'cryptography',
    'mutagen',
]


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
        'Environment :: Console',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Internet',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Multimedia',
        'Topic :: Multimedia :: Sound/Audio',
        'Topic :: Software Development',
        'Topic :: Terminals',
        'Topic :: Utilities',
    ],
)
