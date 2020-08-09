from setuptools import setup, find_packages
import env

setup(name='ShowMeYourMoney',
      version=env.VERSION,
      description='A CLI based money management application for scotiabank',
      author='Christian Boin',
      author_email='cboin1996@gmail.com',
      packages=find_packages(),
      install_requires=['pandas', 'numpy', 'matplotlib', 'pyautogui'],
     )