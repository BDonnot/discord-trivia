from setuptools import setup

setup(
    name='trivia',
    version='0.0.1',
    description='Discord bot for GoTC',
    url='https://github.com/BDonnot/discord-trivia',
    author='Einsteinium',
    author_email='benjamin.donnot@gmail.com',
    license='GPL-3.0',
    packages=['trivia'],
    scripts=[
        'bin/trivia'
    ],
    package_data={
        'trivia': [
            "data/*.csv",
            "data/*.json"
        ],
    },
    zip_safe=False,
    install_requires=[
        'docopt',
        'python-aiml',
        'discord.py',
        'requests',
        "pymongo",
        "wordpress_json",
        "argparse",
        "GitPython",
        "matplotlib",
        "pandas",
        "aiofiles",
        "aiohttp",
        "tqdm",
        "opencv-python",
        "pytesseract",
        "tweepy"
    ]
)
