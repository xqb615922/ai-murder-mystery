"""AI 剧本杀 - 线索管理（ChromaDB 向量检索）"""
from __future__ import annotations
import chromadb
from app.core.config import settings


class ClueManager:
    """基于 ChromaDB 的线索向量检索"""

    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)

    def index_clues(self, game_id: str, clues: list[dict], scenario_text: str):
        """将线索和场景信息存入向量库"""
        collection = self.client.get_or_create_collection(
            name=f"game_{game_id}",
            metadata={"hnsw:space": "cosine"},
        )

        # 索引每条线索
        for clue in clues:
            collection.add(
                ids=[clue["id"]],
                documents=[clue["description"]],
                metadatas=[{
                    "location": clue.get("location", ""),
                    "related_suspect": clue.get("related_suspect", ""),
                    "is_red_herring": clue.get("is_red_herring", False),
                }],
            )

        # 索引场景信息
        collection.add(
            ids=["scenario_background"],
            documents=[scenario_text],
            metadatas=[{"type": "background"}],
        )

    def search_clues(self, game_id: str, query: str, top_k: int = 3) -> list[dict]:
        """语义检索线索"""
        try:
            collection = self.client.get_collection(name=f"game_{game_id}")
        except Exception:
            return []

        results = collection.query(
            query_texts=[query],
            n_results=top_k,
        )

        clues = []
        for i, doc in enumerate(results["documents"][0]):
            clues.append({
                "description": doc,
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if results.get("distances") else None,
            })
        return clues

    def discover_clue(self, game_id: str, query: str, threshold: float = 1.2):
        """玩家搜索线索（距离阈值控制发现难度）"""
        results = self.search_clues(game_id, query, top_k=1)
        if not results:
            return None

        clue = results[0]
        if clue["distance"] is not None and clue["distance"] < threshold:
            # 距离够近 → 发现线索
            return {
                "found": True,
                "description": clue["description"],
                "metadata": clue["metadata"],
            }
        return None

    def delete_game(self, game_id: str):
        """清理游戏数据"""
        try:
            self.client.delete_collection(name=f"game_{game_id}")
        except Exception:
            pass


clue_manager = ClueManager()
