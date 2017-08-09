#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    BTC: 13MXa7EdMYaXaQK6cDHqd4dwr2stBK3ESE
#    LTC: LfxwJHNCjDh2qyJdfu22rBFi2Eu8BjQdxj
#
#    https://github.com/s4w3d0ff/marconibot
#
#    Copyright (C) 2017  https://github.com/s4w3d0ff
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
from setuptools import setup
from marconi import __version__
setup(name='marconi',
      version=__version__,
      description='Poloniex API trader for Python 3',
      url='https://github.com/s4w3d0ff/marconibot',
      author='s4w3d0ff',
      license='GPL v3',
      packages=['marconi',
                'marconi.tools',
                'marconi.tools.poloniex',
                'marconi.tools.brain',
                'marconi.tools.indicators',
                'marconi.tools.plotting',
                'marconi.tools.minion',
                'marconi.tools.trading'],
      scripts=['bin/poloaner'],
      setup_requires=['numpy'],
      install_requires=[
          'requests',
          'bokeh',
          'pymongo',
          'scikit-learn',
          'numpy',
          'pandas',
          'scipy',
          'websocket-client',
      ],
      zip_safe=False)
