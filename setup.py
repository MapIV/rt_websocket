from setuptools import setup, find_packages

setup(
    name='rtWebsocket',  # パッケージ名
    version="0.0.1",  # バージョン
    description="",  # 説明
    author='ota',  # 作者名
    package_dir={"": "src"},  # src以下をpacakgeとして指定
    packages=find_packages(where="src"),  # パッケージの指定
    license='MIT'  # ライセンス
)