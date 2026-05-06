"""PDF 解析工具（带语义定位）"""
import os
from typing import List, Dict, Optional
from pathlib import Path
import re


try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("[WARN] PyMuPDF not installed. Run: uv pip install pymupdf")


class PDFParser:
    """
    PDF 解析器（招生章程专用）

    功能：
    1. 文本提取
    2. 关键词语义定位（避免从头读）
    3. 分段提取（只返回相关段落）
    """

    def __init__(self, pdf_dir: str = "data/pdfs"):
        """
        初始化 PDF 解析器

        Args:
            pdf_dir: PDF 文件存储目录
        """
        self.pdf_dir = Path(pdf_dir)
        self.pdf_dir.mkdir(parents=True, exist_ok=True)

        if not PYMUPDF_AVAILABLE:
            raise ImportError("PyMuPDF not installed")

    def extract_full_text(self, pdf_path: str) -> str:
        """
        提取 PDF 全文

        Args:
            pdf_path: PDF 文件路径

        Returns:
            全文文本
        """
        if not PYMUPDF_AVAILABLE:
            return ""

        doc = fitz.open(pdf_path)
        full_text = ""

        for page_num, page in enumerate(doc):
            text = page.get_text()
            full_text += f"\n--- 第 {page_num + 1} 页 ---\n{text}"

        doc.close()
        return full_text

    def build_keyword_index(self, pdf_path: str) -> Dict[str, List[int]]:
        """
        构建关键词索引（快速定位相关页码）

        Args:
            pdf_path: PDF 文件路径

        Returns:
            {关键词: [页码列表]}
        """
        if not PYMUPDF_AVAILABLE:
            return {}

        doc = fitz.open(pdf_path)
        keyword_index = {}

        # 预定义关键词（招生章程常见）
        keywords = [
            "体检", "色盲", "色弱", "视力", "身高", "听力",
            "单科", "英语", "数学", "语文",
            "录取规则", "专业调剂", "志愿", "分数级差",
            "学费", "住宿费", "奖学金",
            "转专业", "辅修", "双学位"
        ]

        for page_num, page in enumerate(doc):
            text = page.get_text()

            for keyword in keywords:
                if keyword in text:
                    if keyword not in keyword_index:
                        keyword_index[keyword] = []
                    keyword_index[keyword].append(page_num + 1)  # 页码从1开始

        doc.close()
        return keyword_index

    def extract_sections_by_keywords(
        self,
        pdf_path: str,
        keywords: List[str],
        context_pages: int = 0
    ) -> str:
        """
        基于关键词提取相关段落（语义定位）

        Args:
            pdf_path: PDF 文件路径
            keywords: 关键词列表
            context_pages: 前后上下文页数（0表示只返回匹配页）

        Returns:
            相关段落文本
        """
        if not PYMUPDF_AVAILABLE:
            return ""

        doc = fitz.open(pdf_path)
        relevant_pages = set()

        # 第一步：找到所有包含关键词的页码
        for page_num, page in enumerate(doc):
            text = page.get_text()

            for keyword in keywords:
                if keyword in text:
                    # 添加匹配页及其上下文页
                    for offset in range(-context_pages, context_pages + 1):
                        target_page = page_num + offset
                        if 0 <= target_page < len(doc):
                            relevant_pages.add(target_page)

        # 第二步：提取相关页面文本
        result = ""
        for page_num in sorted(relevant_pages):
            page = doc[page_num]
            text = page.get_text()
            result += f"\n{'=' * 60}\n"
            result += f"第 {page_num + 1} 页（包含关键词：{keywords}）\n"
            result += f"{'=' * 60}\n"
            result += text

        doc.close()

        if not result:
            return f"未找到包含关键词 {keywords} 的内容"

        return result

    def extract_health_requirements(self, pdf_path: str) -> str:
        """
        提取体检要求（专用方法）

        Args:
            pdf_path: PDF 文件路径

        Returns:
            体检要求文本
        """
        keywords = ["体检", "色盲", "色弱", "视力", "身高", "听力"]
        return self.extract_sections_by_keywords(pdf_path, keywords, context_pages=1)

    def extract_admission_rules(self, pdf_path: str) -> str:
        """
        提取录取规则（专用方法）

        Args:
            pdf_path: PDF 文件路径

        Returns:
            录取规则文本
        """
        keywords = ["录取规则", "专业调剂", "志愿", "分数级差", "单科"]
        return self.extract_sections_by_keywords(pdf_path, keywords, context_pages=1)

    def find_school_pdf(self, school_name: str) -> Optional[str]:
        """
        根据学校名称查找 PDF 文件

        Args:
            school_name: 学校名称

        Returns:
            PDF 文件路径（如果存在）
        """
        # 尝试多种命名格式
        possible_names = [
            f"{school_name}招生章程.pdf",
            f"{school_name}.pdf",
            f"{school_name}_招生章程.pdf"
        ]

        for name in possible_names:
            pdf_path = self.pdf_dir / name
            if pdf_path.exists():
                return str(pdf_path)

        return None

    def list_available_pdfs(self) -> List[str]:
        """
        列出所有可用的 PDF 文件

        Returns:
            PDF 文件列表
        """
        if not self.pdf_dir.exists():
            return []

        return [str(p) for p in self.pdf_dir.glob("*.pdf")]


# === 工具函数 ===
def parse_health_restriction(
    school_name: str,
    pdf_dir: str = "data/pdfs"
) -> Dict[str, any]:
    """
    解析学校体检限制（工具函数）

    Args:
        school_name: 学校名称
        pdf_dir: PDF 目录

    Returns:
        {
            'found': bool,
            'content': str,
            'pdf_path': str
        }
    """
    try:
        parser = PDFParser(pdf_dir)
        pdf_path = parser.find_school_pdf(school_name)

        if not pdf_path:
            return {
                'found': False,
                'content': f"未找到 {school_name} 的招生章程 PDF",
                'pdf_path': None
            }

        health_text = parser.extract_health_requirements(pdf_path)

        return {
            'found': True,
            'content': health_text,
            'pdf_path': pdf_path
        }

    except Exception as e:
        return {
            'found': False,
            'content': f"解析失败：{e}",
            'pdf_path': None
        }
