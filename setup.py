from setuptools import setup
setup(name='marconi',
      version='0.0.1',
      description='Poloniex API trader for Python 3',
      url='https://github.com/s4w3d0ff/marconibot',
      author='s4w3d0ff',
      license='GPL v3',
      packages=['marconi'],
      install_requires=[
          'requests',
          'numpy',
          'bokeh',
          'pymongo',
          'pandas',
          'autobahn[asyncio]',
          'aiohttp'
      ],
      zip_safe=False)
