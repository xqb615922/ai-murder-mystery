"""AI 剧本杀 - 线索管理（轻量关键词匹配，无需 ChromaDB）"""
from __future__ import annotations
import re
from typing import Optional


class ClueManager:
    """基于关键词匹配的线索检索（云端友好，零外部依赖）"""

    # 内存存储：game_id -> {"clues": [...], "scenario": str}
    _store: dict = {}

    def index_clues(self, game_id: str, clues: list[dict], scenario_text: str):
        """将线索和场景信息存入内存"""
        self._store[game_id] = {
            "clues": clues,
            "scenario": scenario_text,
        }

    def search_clues(self, game_id: str, query: str, top_k: int = 3) -> list[dict]:
        """关键词匹配检索线索"""
        game_data = self._store.get(game_id)
        if not game_data:
            return []

        query_words = set(re.findall(r"\w+", query.lower()))
        scored = []
        for clue in game_data["clues"]:
            desc_words = set(re.findall(r"\w+", clue["description"].lower()))
            # 也匹配 location 和 related_suspect
            loc_words = set(re.findall(r"\w+", clue.get("location", "").lower()))
            suspect_words = set(re.findall(r"\w+", clue.get("related_suspect", "").lower()))
            all_words = desc_words | loc_words | suspect_words

            overlap = len(query_words & all_words)
            if overlap > 0:
                scored.append((overlap, clue))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {"description": clue["description"], "metadata": {
                "location": clue.get("location", ""),
                "related_suspect": clue.get("related_suspect", ""),
                "is_red_herring": clue.get("is_red_herring", False),
            }}
            for _, clue in scored[:top_k]
        ]

    def discover_clue(self, game_id: str, query: str, threshold: float = 0.3):
        """玩家搜索线索（匹配度阈值控制发现难度）"""
        game_data = self._store.get(game_id)
        if not game_data:
            return None

        query_words = set(re.findall(r"\w+", query.lower()))
        best_score = 0.0
        best_clue = None

        for clue in game_data["clues"]:
            desc_words = set(re.findall(r"\w+", clue["description"].lower()))
            loc_words = set(re.findall(r"\w+", clue.get("location", "").lower()))
            suspect_words = set(re.findall(r"\w+", clue.get("related_suspect", "").lower()))
            all_words = desc_words | loc_words | suspect_words

            if not all_words:
                continue
            overlap = len(query_words & all_words)
            score = overlap / max(len(query_words), 1)
            if score > best_score:
                best_score = score
                best_clue = clue

        if best_clue and best_score >= threshold:
            return {
                "found": True,
                "description": best_clue["description"],
                "metadata": {
                    "location": best_clue.get("location", ""),
                    "related_suspect": best_clue.get("related_suspect", ""),
                    "is_red_herring": best_clue.get("is_red_herring", False),
                },
            }
        return None

    def get_all_clues(self, game_id: str) -> list[dict]:
        """获取某局游戏所有线索"""
        game_data = self._store.get(game_id)
        if not game_data:
            return []
        return game_data["clues"]

    def get_scenario(self, game_id: str) -> Optional[str]:
        """获取场景信息"""
        game_data = self._store.get(game_id)
        if not game_data:
            return None
        return game_data["scenario"]

    def delete_game(self, game_id: str):
        """清理游戏数据"""
        self._store.pop(game_id, None)


clue_manager = ClueManager()
