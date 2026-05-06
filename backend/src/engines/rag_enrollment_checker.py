"""
RAG招生简章检查器
用于从PDF招生简章中提取硬性规则并验证志愿合规性
"""
import os
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import json

try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("[警告] ChromaDB或sentence-transformers未安装，RAG功能将被禁用")

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("[警告] PyMuPDF未安装，PDF解析功能将被禁用")

from langchain_core.messages import HumanMessage, SystemMessage
from ..utils.llm_factory import get_llm


class RAGEnrollmentChecker:
    """
    基于RAG的招生简章规则检查器

    功能：
    1. 索引招生简章PDF文档
    2. 向量检索相关规则
    3. LLM判断志愿是否违规

    优雅降级：当ChromaDB不可用时，返回空结果不报错
    """

    def __init__(
        self,
        persist_directory: str = "./data/chroma_db",
        collection_name: str = "enrollment_rules",
        embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"
    ):
        """
        初始化RAG检查器

        Args:
            persist_directory: ChromaDB持久化目录
            collection_name: 集合名称
            embedding_model: 嵌入模型名称
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model

        # 初始化状态标志
        self.is_available = False
        self.client = None
        self.collection = None
        self.embedding_model = None

        # 尝试初始化ChromaDB
        if CHROMADB_AVAILABLE:
            try:
                # 创建持久化目录
                os.makedirs(persist_directory, exist_ok=True)

                # 初始化ChromaDB客户端
                self.client = chromadb.PersistentClient(
                    path=persist_directory,
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )

                # 获取或创建集合
                self.collection = self.client.get_or_create_collection(
                    name=collection_name,
                    metadata={"hnsw:space": "cosine"}
                )

                # 初始化嵌入模型
                self.embedding_model = SentenceTransformer(embedding_model)

                self.is_available = True
                print(f"[RAG] 初始化成功，集合文档数：{self.collection.count()}")

            except Exception as e:
                print(f"[RAG] 初始化失败（优雅降级）：{e}")
                self.is_available = False
        else:
            print("[RAG] ChromaDB不可用，RAG功能已禁用")

    def index_enrollment_document(
        self,
        school_code: str,
        school_name: str,
        pdf_path: str,
        chunk_size: int = 500,
        chunk_overlap: int = 100
    ) -> bool:
        """
        索引单个招生简章PDF

        Args:
            school_code: 院校代码
            school_name: 院校名称
            pdf_path: PDF文件路径
            chunk_size: 分块大小（字符数）
            chunk_overlap: 分块重叠（字符数）

        Returns:
            是否索引成功
        """
        if not self.is_available:
            print(f"[RAG] 跳过索引 {school_name}（RAG不可用）")
            return False

        if not PYMUPDF_AVAILABLE:
            print(f"[RAG] 跳过索引 {school_name}（PyMuPDF不可用）")
            return False

        if not os.path.exists(pdf_path):
            print(f"[RAG] PDF文件不存在：{pdf_path}")
            return False

        try:
            # 1. 提取PDF文本
            print(f"[RAG] 正在解析PDF：{school_name}")
            full_text = self._extract_pdf_text(pdf_path)

            if not full_text or len(full_text) < 50:
                print(f"[RAG] PDF内容过少，跳过：{school_name}")
                return False

            # 2. 分块
            chunks = self._chunk_text(full_text, chunk_size, chunk_overlap)
            print(f"[RAG] 分块完成，共{len(chunks)}块")

            # 3. 分类规则类型并过滤
            classified_chunks = []
            for chunk in chunks:
                rule_type = self._classify_rule_type(chunk)
                if rule_type != "irrelevant":
                    classified_chunks.append((chunk, rule_type))

            print(f"[RAG] 过滤后保留{len(classified_chunks)}个有效规则块")

            if len(classified_chunks) == 0:
                print(f"[RAG] 未发现有效规则，跳过：{school_name}")
                return False

            # 4. 生成嵌入并存储
            documents = []
            metadatas = []
            ids = []

            for idx, (chunk, rule_type) in enumerate(classified_chunks):
                doc_id = f"{school_code}_{idx}"
                documents.append(chunk)
                metadatas.append({
                    "school_code": school_code,
                    "school_name": school_name,
                    "rule_type": rule_type,
                    "chunk_index": idx
                })
                ids.append(doc_id)

            # 批量生成嵌入
            embeddings = self.embedding_model.encode(
                documents,
                normalize_embeddings=True,
                show_progress_bar=False
            ).tolist()

            # 存储到ChromaDB
            self.collection.upsert(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )

            print(f"[RAG] ✅ 索引完成：{school_name}（{len(documents)}条规则）")
            return True

        except Exception as e:
            print(f"[RAG] 索引失败：{school_name} - {e}")
            return False

    def check_volunteer(
        self,
        school_code: str,
        school_name: str,
        major_name: str,
        user_profile: Dict,
        top_k: int = 5
    ) -> Dict:
        """
        检查单个志愿是否违反招生规则

        Args:
            school_code: 院校代码
            school_name: 院校名称
            major_name: 专业名称
            user_profile: 用户画像（包含选科、分数、体检等）
            top_k: 检索top-k相关规则

        Returns:
            {
                "has_violations": bool,
                "violations": [{"rule_type": str, "rule_text": str, "reason": str}],
                "checked": bool  # 是否成功检查
            }
        """
        if not self.is_available:
            # 优雅降级：RAG不可用时返回空结果
            return {
                "has_violations": False,
                "violations": [],
                "checked": False,
                "message": "RAG系统不可用"
            }

        try:
            # 1. 构建查询
            query = self._build_query(school_name, major_name, user_profile)

            # 2. 向量检索
            relevant_rules = self._retrieve_rules(
                query=query,
                school_code=school_code,
                top_k=top_k
            )

            if not relevant_rules:
                # 没有找到相关规则，返回通过
                return {
                    "has_violations": False,
                    "violations": [],
                    "checked": True,
                    "message": f"未找到{school_name}的招生规则"
                }

            # 3. LLM判断是否违规
            violations = []
            for rule in relevant_rules:
                violation = self._judge_rule_compliance(
                    rule_text=rule["text"],
                    rule_type=rule["type"],
                    user_profile=user_profile,
                    school_name=school_name,
                    major_name=major_name
                )

                if violation:
                    violations.append(violation)

            return {
                "has_violations": len(violations) > 0,
                "violations": violations,
                "checked": True,
                "message": f"检查完成，发现{len(violations)}处违规" if violations else "检查通过"
            }

        except Exception as e:
            print(f"[RAG] 检查失败：{school_name} - {e}")
            return {
                "has_violations": False,
                "violations": [],
                "checked": False,
                "message": f"检查出错：{str(e)}"
            }

    def _extract_pdf_text(self, pdf_path: str) -> str:
        """提取PDF全文"""
        doc = fitz.open(pdf_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        doc.close()
        return full_text

    def _chunk_text(
        self,
        text: str,
        chunk_size: int,
        chunk_overlap: int
    ) -> List[str]:
        """
        滑动窗口分块

        Args:
            text: 全文
            chunk_size: 块大小
            chunk_overlap: 重叠大小

        Returns:
            文本块列表
        """
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + chunk_size
            chunk = text[start:end]

            # 跳过过短的块
            if len(chunk.strip()) > 50:
                chunks.append(chunk)

            start += (chunk_size - chunk_overlap)

        return chunks

    def _classify_rule_type(self, text: str) -> str:
        """
        分类规则类型（基于关键词）

        Returns:
            rule_type: subject_requirement | subject_score | physical_exam |
                      gender_limit | age_limit | other | irrelevant
        """
        text_lower = text.lower()

        # 选科要求
        if any(kw in text for kw in ["选考科目", "选科要求", "首选科目", "再选科目", "必选", "物理", "历史", "化学", "生物", "政治", "地理"]):
            return "subject_requirement"

        # 单科分数要求
        if any(kw in text for kw in ["单科成绩", "外语成绩", "数学成绩", "语文成绩", "单科不低于", "英语要求"]):
            return "subject_score"

        # 体检要求
        if any(kw in text for kw in ["体检", "身体条件", "色盲", "色弱", "视力", "身高", "体重"]):
            return "physical_exam"

        # 性别限制
        if any(kw in text for kw in ["只招男生", "只招女生", "性别要求", "男女比例"]):
            return "gender_limit"

        # 年龄限制
        if any(kw in text for kw in ["年龄要求", "不超过", "周岁"]):
            return "age_limit"

        # 其他可能的限制
        if any(kw in text for kw in ["要求", "限制", "条件", "不得", "不允许", "禁止"]):
            return "other"

        return "irrelevant"

    def _build_query(
        self,
        school_name: str,
        major_name: str,
        user_profile: Dict
    ) -> str:
        """构建查询文本"""
        query_parts = [
            f"院校：{school_name}",
            f"专业：{major_name}",
        ]

        if "selected_subjects" in user_profile:
            subjects = "、".join(user_profile["selected_subjects"])
            query_parts.append(f"选科：{subjects}")

        if "total_score" in user_profile:
            query_parts.append(f"总分：{user_profile['total_score']}")

        return " ".join(query_parts)

    def _retrieve_rules(
        self,
        query: str,
        school_code: str,
        top_k: int = 5
    ) -> List[Dict]:
        """
        向量检索相关规则

        Returns:
            [{"text": str, "type": str, "distance": float}]
        """
        if not self.is_available:
            return []

        try:
            # 生成查询嵌入
            query_embedding = self.embedding_model.encode(
                [query],
                normalize_embeddings=True,
                show_progress_bar=False
            ).tolist()

            # 检索
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=top_k,
                where={"school_code": school_code}  # 过滤该院校
            )

            # 解析结果
            rules = []
            if results and results["documents"] and len(results["documents"]) > 0:
                for i in range(len(results["documents"][0])):
                    rules.append({
                        "text": results["documents"][0][i],
                        "type": results["metadatas"][0][i]["rule_type"],
                        "distance": results["distances"][0][i] if "distances" in results else 0.0
                    })

            return rules

        except Exception as e:
            print(f"[RAG] 检索失败：{e}")
            return []

    def _judge_rule_compliance(
        self,
        rule_text: str,
        rule_type: str,
        user_profile: Dict,
        school_name: str,
        major_name: str
    ) -> Optional[Dict]:
        """
        使用LLM判断用户是否违反规则

        Returns:
            如果违规，返回 {"rule_type": str, "rule_text": str, "reason": str}
            如果不违规，返回 None
        """
        try:
            llm = get_llm()

            # 构建用户信息摘要
            user_info = f"""
考生信息：
- 总分：{user_profile.get('total_score', '未知')}
- 选科：{', '.join(user_profile.get('selected_subjects', []))}
- 语文：{user_profile.get('chinese_score', '未知')}
- 数学：{user_profile.get('math_score', '未知')}
- 外语：{user_profile.get('english_score', '未知')}
"""

            prompt = f"""你是招生规则专家，负责判断考生是否满足院校专业的招生要求。

院校专业：{school_name} - {major_name}
规则类型：{rule_type}
招生规则：
{rule_text}

{user_info}

请判断该考生是否**违反**了上述招生规则。

输出JSON格式：
{{
    "is_violation": true/false,
    "reason": "违规原因说明（如果违规）"
}}

只输出JSON，不要其他内容。
"""

            messages = [
                SystemMessage(content="你是招生规则专家，擅长判断考生是否满足招生要求。"),
                HumanMessage(content=prompt)
            ]

            response = llm.invoke(messages, temperature=0.1)
            result_text = response.content.strip()

            # 解析JSON
            if result_text.startswith("```json"):
                result_text = result_text[7:-3].strip()
            elif result_text.startswith("```"):
                result_text = result_text[3:-3].strip()

            result = json.loads(result_text)

            if result.get("is_violation", False):
                return {
                    "rule_type": rule_type,
                    "rule_text": rule_text[:200],  # 截断过长文本
                    "reason": result.get("reason", "未说明原因")
                }
            else:
                return None

        except Exception as e:
            print(f"[RAG] LLM判断失败：{e}")
            return None

    def get_stats(self) -> Dict:
        """获取RAG系统统计信息"""
        if not self.is_available:
            return {
                "available": False,
                "total_rules": 0,
                "schools_indexed": 0
            }

        try:
            total_count = self.collection.count()

            # 统计已索引的院校数
            all_metadata = self.collection.get(include=["metadatas"])
            school_codes = set()
            if all_metadata and "metadatas" in all_metadata:
                for meta in all_metadata["metadatas"]:
                    if "school_code" in meta:
                        school_codes.add(meta["school_code"])

            return {
                "available": True,
                "total_rules": total_count,
                "schools_indexed": len(school_codes)
            }
        except Exception as e:
            print(f"[RAG] 获取统计失败：{e}")
            return {
                "available": False,
                "total_rules": 0,
                "schools_indexed": 0
            }


# 全局单例
_rag_checker_instance = None

def get_rag_checker() -> RAGEnrollmentChecker:
    """获取RAG检查器单例"""
    global _rag_checker_instance
    if _rag_checker_instance is None:
        _rag_checker_instance = RAGEnrollmentChecker()
    return _rag_checker_instance
