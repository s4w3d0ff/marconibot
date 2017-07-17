from setuptools import setup
from marconi import __version__
setup(name='marconi',
      version=__version__,
      description='Poloniex API trader for Python 3',
      url='https://github.com/s4w3d0ff/marconibot',
      author='s4w3d0ff',
      license='GPL v3',
      packages=['marconi'],
      scripts=['bin/poloaner'],
      install_requires=[
          'numpy',
          'scikit-learn',
          'bokeh',
          'cherrypy',
          'beautifulsoup4',
          'pymongo',
          'pandas',
          'websocket-client',
      ],
      zip_safe=False)
