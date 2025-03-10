from setuptools import setup, find_packages

setup(
    name='rtWebsocket',  # パッケージ名
    version="0.0.1",  # バージョン
    description="test",  # 説明
    author='ota',  # 作者名
    package_dir={"": "src"},  # src以下をpacakgeとして指定
    packages=find_packages(where="src"),  # パッケージの指定
    install_requires=[  # 必要なパッケージを指定
        "fastapi",
        "uvicorn",
        "websockets",
        "pypcd",
        "pytest",
        "pytest-asyncio",
        "httpx",
        "opencv-python",
        "pypcd4",
        "bson"
    ],
    include_package_data=True,
    license='MIT'  # ライセンス
)