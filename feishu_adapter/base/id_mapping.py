"""
业务ID <-> 飞书record_id 映射管理

维护业务ID与飞书内部record_id的映射关系，存储在本地JSON文件中。
业务代码只使用业务ID，不感知飞书record_id。
"""

import json
import os
from pathlib import Path
from typing import Optional


class IDMapping:
    """业务ID <-> 飞书record_id 映射管理"""

    def __init__(self, mapping_file: str = ".id_mapping.json"):
        """
        初始化ID映射管理器

        Args:
            mapping_file: 映射文件路径，默认为项目根目录的 .id_mapping.json
        """
        # 如果传入的是相对路径，基于项目根目录解析
        if not os.path.isabs(mapping_file):
            project_root = Path(__file__).parent.parent.parent
            self.mapping_file = project_root / mapping_file
        else:
            self.mapping_file = Path(mapping_file)

        self._mapping: dict[str, dict] = {}
        self._load()

    def _load(self):
        """从文件加载映射"""
        if self.mapping_file.exists():
            try:
                with open(self.mapping_file, 'r', encoding='utf-8') as f:
                    self._mapping = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"[WARNING] 加载ID映射文件失败: {e}，将创建新文件")
                self._mapping = {}

    def _save(self):
        """保存映射到文件"""
        try:
            # 确保目录存在
            self.mapping_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.mapping_file, 'w', encoding='utf-8') as f:
                json.dump(self._mapping, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"[ERROR] 保存ID映射文件失败: {e}")

    def _make_key(self, table: str, business_id: str) -> str:
        """生成映射键"""
        return f"{table}:{business_id}"

    def add(self, table: str, business_id: str, record_id: str):
        """
        添加映射关系

        Args:
            table: 表名
            business_id: 业务ID
            record_id: 飞书record_id
        """
        key = self._make_key(table, business_id)
        self._mapping[key] = {"record_id": record_id}
        self._save()

    def get_record_id(self, table: str, business_id: str) -> Optional[str]:
        """
        根据业务ID获取飞书record_id

        Args:
            table: 表名
            business_id: 业务ID

        Returns:
            飞书record_id，不存在则返回None
        """
        key = self._make_key(table, business_id)
        return self._mapping.get(key, {}).get("record_id")

    def get_business_id(self, table: str, record_id: str) -> Optional[str]:
        """
        根据飞书record_id获取业务ID

        Args:
            table: 表名
            record_id: 飞书record_id

        Returns:
            业务ID，不存在则返回None
        """
        for key, value in self._mapping.items():
            if key.startswith(f"{table}:") and value.get("record_id") == record_id:
                return key.split(":", 1)[1]
        return None

    def remove(self, table: str, business_id: str) -> bool:
        """
        删除映射关系

        Args:
            table: 表名
            business_id: 业务ID

        Returns:
            是否成功删除
        """
        key = self._make_key(table, business_id)
        if key in self._mapping:
            del self._mapping[key]
            self._save()
            return True
        return False

    def clear_table(self, table: str):
        """
        清空指定表的所有映射

        Args:
            table: 表名
        """
        keys_to_remove = [k for k in self._mapping.keys() if k.startswith(f"{table}:")]
        for key in keys_to_remove:
            del self._mapping[key]
        if keys_to_remove:
            self._save()

    def list_table_mappings(self, table: str) -> dict[str, str]:
        """
        列出指定表的所有映射

        Args:
            table: 表名

        Returns:
            {业务ID: record_id} 字典
        """
        result = {}
        for key, value in self._mapping.items():
            if key.startswith(f"{table}:"):
                business_id = key.split(":", 1)[1]
                result[business_id] = value.get("record_id")
        return result

    def exists(self, table: str, business_id: str) -> bool:
        """
        检查映射是否存在

        Args:
            table: 表名
            business_id: 业务ID

        Returns:
            是否存在
        """
        key = self._make_key(table, business_id)
        return key in self._mapping
