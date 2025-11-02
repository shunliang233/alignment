from typing import List, Iterator

class RawList:
    """
    处理原始文件编号字符串的类，支持单个文件和范围格式

    >>> RawList('400')
    RawList('400')
    >>> str(RawList('400'))
    '400'
    >>> RawList('400-402')
    RawList('400-402')
    >>> str(RawList('400-402'))
    '400-402'
    >>> list(RawList('400-402'))
    ['00400', '00401']
    """
    
    # 构造函数
    def __init__(self, file_str: str):
        """
        初始化原始文件列表
        Args:
            file_str (str): 文件编号字符串，支持格式：
                           - 单个文件: "400"
                           - 范围格式: "400-500" 或 "400:500"
        """
        self.file_str: str = file_str.strip()
        self.raw_files: List[str] = self._parse_string()
    def _parse_string(self) -> List[str]:
        """解析文件字符串，返回宽度为5的字符串编号列表"""
        if '-' in self.file_str and ':' not in self.file_str:
            # 格式: 400-500
            start, end = map(int, self.file_str.split('-'))
            return [str(i).zfill(5) for i in range(start, end)]
        elif ':' in self.file_str:
            # 格式: 400:500
            start, end = map(int, self.file_str.split(':'))
            return [str(i).zfill(5) for i in range(start, end)]
        else:
            # 单个文件: 400
            try:
                return [str(int(self.file_str)).zfill(5)]
            except ValueError:
                raise ValueError(f"Invalid file format: '{self.file_str}'. Use '400', '400-500' or '400:500'")
    
    def get_nums(self) -> List[str]:
        """返回原始文件编号列表"""
        return self.raw_files
    def count(self) -> int:
        """返回文件数量"""
        return len(self.raw_files)
    def is_single(self) -> bool:
        """检查是否为单个文件"""
        return len(self.raw_files) == 1
    
    # Magic methods
    def __str__(self) -> str:
        """字符串表示"""
        if len(self.raw_files) == 1:
            return str(int(self.raw_files[0]))
        else:
            return f"{int(self.raw_files[0])}-{int(self.raw_files[-1]) + 1}"
    def __repr__(self) -> str:
        return f"RawList({self.file_str!r})"
    def __len__(self) -> int:
        """返回文件数量"""
        return len(self.raw_files)
    def __iter__(self) -> Iterator[str]:
        """支持迭代"""
        return iter(self.raw_files)
