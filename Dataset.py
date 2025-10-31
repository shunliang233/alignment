import os
import sys
from typing import Optional
from RawList import RawList
from collections import namedtuple

IterDir = namedtuple("IterDir", ["num", "dir"])

class Dataset:
    """
    >>> d1 = Dataset('2023', '11705', '400')
    >>> print(d1)
    Y2023_R011705_F400
    >>> d2 = Dataset('2022', '123', '400-450')
    >>> print(d2)
    Y2022_R000123_F400-450
    >>> d2
    Dataset(year='2022', run='000123', files='400-450')
    """

    def __init__(self, year: str, run: str, files: str,
                 base_dir: Optional[str] = None) -> None:
        self.year: str = str(year).zfill(4)
        self.run: str = str(run).zfill(6)
        self.files: RawList = RawList(files)
        self.name: str = f"Y{self.year}_R{self.run}_F{self.files}"
        if base_dir is None:
            base_dir = self._default_base_dir()
        self.data_dir: str = os.path.join(base_dir, self.name)

    # 类方法
    @staticmethod
    def _default_base_dir() -> str:
        """获取入口脚本所在的绝对目录"""
        return os.path.abspath(os.path.dirname(sys.modules['__main__'].__file__))
    @staticmethod
    def _is_iter_dir(parent: str, name: str) -> bool:
        """判断目录名是否为 iter+整数，且为目录。"""
        return (
            name.startswith("iter")
            and name[4:].isdigit()
            and os.path.isdir(os.path.join(parent, name))
        )

    # 内部方法
    def _check_data_dir(self) -> None:
        """Check directory iter* existence."""
        if not os.path.isdir(self.data_dir):
            raise FileNotFoundError(f"No directory: {self.data_dir}")
        iter_dirs = [name for name in os.listdir(self.data_dir)
                     if self._is_iter_dir(self.data_dir, name)]
        if not iter_dirs:
            raise FileNotFoundError(f"No iter* directories in: {self.data_dir}")

    def iter_dirs(self) -> list["IterDir"]:
        """返回每个 iterXX 目录的 IterDir(num, dir)，num为数字，dir为绝对路径。"""
        self._check_data_dir()
        result = []
        for name in os.listdir(self.data_dir):
            if self._is_iter_dir(self.data_dir, name):
                num = int(name[4:])
                path = os.path.join(self.data_dir, name)
                result.append(IterDir(num=num, dir=path))
        result.sort(key=lambda x: x.num)
        return result

    # Magic methods
    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"Dataset(year={self.year!r}, run={self.run!r}, files='{self.files}')"