import setuptools

description = 'Class based Rabbitmq using Asyncio. Based off aioamqp.'

setuptools.setup(
    name="aiorabbitmq",
    version="0.1.0",
    author="Jared Mackey",
    author_email='jared@mackeydevelopments.com',
    url='https://github.com/mackeyja92/aiorabbitmq',
    description=description,
    download_url='https://pypi.python.org/pypi/aiorabbitmq',
    packages=[
        'aiorabbitmq',
    ],
    classifiers=[],
    platforms='all',
)