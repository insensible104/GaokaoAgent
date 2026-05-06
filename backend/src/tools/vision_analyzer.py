"""Vision 工具（图表识别，基于 Ollama llava）"""
import os
import base64
from typing import List, Dict, Optional
from pathlib import Path

try:
    from langchain_ollama import ChatOllama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    print("[WARN] langchain-ollama not installed")

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


class VisionAnalyzer:
    """
    视觉分析器（基于 Ollama llava 模型）

    功能：
    1. 从 PDF 提取图片
    2. 使用 Vision 模型识别图表内容
    3. 专用：体检限制表格识别
    """

    def __init__(
        self,
        model_name: str = "llava:7b",
        base_url: str = "http://localhost:11434"
    ):
        """
        初始化 Vision 分析器

        Args:
            model_name: Ollama Vision 模型名称
            base_url: Ollama 服务地址
        """
        if not OLLAMA_AVAILABLE:
            raise ImportError("langchain-ollama not installed")

        self.model_name = model_name
        self.base_url = base_url
        self.llm = ChatOllama(
            model=model_name,
            base_url=base_url,
            temperature=0
        )

        print(f"[Vision] 初始化完成：{model_name} @ {base_url}")

    def extract_images_from_pdf(
        self,
        pdf_path: str,
        page_numbers: Optional[List[int]] = None
    ) -> List[Dict]:
        """
        从 PDF 提取图片

        Args:
            pdf_path: PDF 文件路径
            page_numbers: 要提取的页码列表（None表示全部）

        Returns:
            [
                {
                    'page': 1,
                    'image_index': 0,
                    'image_bytes': bytes,
                    'bbox': [x0, y0, x1, y1]
                }
            ]
        """
        if not PYMUPDF_AVAILABLE:
            return []

        doc = fitz.open(pdf_path)
        images = []

        for page_num, page in enumerate(doc):
            # 跳过不需要的页面
            if page_numbers is not None and (page_num + 1) not in page_numbers:
                continue

            # 提取页面上的所有图片
            image_list = page.get_images(full=True)

            for img_index, img_info in enumerate(image_list):
                xref = img_info[0]  # 图片引用号

                # 提取图片数据
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]

                # 获取图片位置
                rects = page.get_image_rects(xref)
                bbox = rects[0] if rects else None

                images.append({
                    'page': page_num + 1,
                    'image_index': img_index,
                    'image_bytes': image_bytes,
                    'bbox': list(bbox) if bbox else None
                })

        doc.close()
        return images

    def analyze_image(
        self,
        image_bytes: bytes,
        prompt: str
    ) -> str:
        """
        使用 Vision 模型分析图片

        Args:
            image_bytes: 图片二进制数据
            prompt: 提示词

        Returns:
            分析结果
        """
        # 将图片编码为 base64
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        image_url = f"data:image/jpeg;base64,{image_base64}"

        # 构建多模态消息
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ]

        try:
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            return f"分析失败：{e}"

    def analyze_health_restriction_table(
        self,
        pdf_path: str,
        page_numbers: Optional[List[int]] = None,
        target_condition: Optional[str] = None
    ) -> Dict:
        """
        分析体检限制表格（专用方法）

        Args:
            pdf_path: PDF 文件路径
            page_numbers: 要分析的页码（None表示全部）
            target_condition: 目标体检条件（如"色弱"）

        Returns:
            {
                'found_tables': int,
                'restrictions': [
                    {
                        'page': 1,
                        'content': '表格内容描述',
                        'contains_target': bool
                    }
                ]
            }
        """
        # 提取图片
        images = self.extract_images_from_pdf(pdf_path, page_numbers)

        if not images:
            return {
                'found_tables': 0,
                'restrictions': [],
                'message': '未找到图片'
            }

        # 分析每张图片
        restrictions = []

        for img in images:
            # 构建提示词
            prompt = f"""请分析这张图片，判断它是否是体检限制表格。

如果是体检限制表格，请提取以下信息：
1. 表格中列出了哪些体检条件（如色盲、色弱、视力、身高等）
2. 每个条件对应的受限专业
3. 是否提到"{target_condition or '任何特殊条件'}"

请用以下格式回答：
- 是否为体检表格：是/否
- 包含的体检条件：[列表]
- {target_condition or '目标条件'}的限制：[具体说明]

如果不是体检表格，直接回答"不是体检表格"。
"""

            result = self.analyze_image(img['image_bytes'], prompt)

            # 判断是否包含目标条件
            contains_target = False
            if target_condition and target_condition in result:
                contains_target = True

            restrictions.append({
                'page': img['page'],
                'image_index': img['image_index'],
                'content': result,
                'contains_target': contains_target
            })

        return {
            'found_tables': len(restrictions),
            'restrictions': restrictions,
            'message': f'分析了 {len(restrictions)} 张图片'
        }

    def extract_table_text(
        self,
        image_bytes: bytes
    ) -> str:
        """
        提取表格文本（OCR）

        Args:
            image_bytes: 图片二进制数据

        Returns:
            表格文本
        """
        prompt = """请识别这张图片中的表格内容，将其转换为纯文本格式。

要求：
1. 保持表格结构（使用 Markdown 表格格式）
2. 准确提取所有文字
3. 如果有多个表格，分别提取

请直接输出表格内容，无需其他说明。
"""
        return self.analyze_image(image_bytes, prompt)


# === 工具函数 ===
def check_health_restriction_with_vision(
    pdf_path: str,
    condition: str,
    page_numbers: Optional[List[int]] = None
) -> Dict:
    """
    使用 Vision 检查体检限制（工具函数）

    Args:
        pdf_path: PDF 文件路径
        condition: 体检条件（如"色弱"）
        page_numbers: 页码列表

    Returns:
        {
            'has_restriction': bool,
            'details': str,
            'sources': List[int]  # 页码
        }
    """
    try:
        vision_model = os.environ.get("VISION_MODEL", "llava:7b")
        base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

        analyzer = VisionAnalyzer(model_name=vision_model, base_url=base_url)

        result = analyzer.analyze_health_restriction_table(
            pdf_path,
            page_numbers,
            target_condition=condition
        )

        # 汇总结果
        has_restriction = False
        details = []
        sources = []

        for restriction in result['restrictions']:
            if restriction['contains_target']:
                has_restriction = True
                details.append(restriction['content'])
                sources.append(restriction['page'])

        return {
            'has_restriction': has_restriction,
            'details': '\n\n'.join(details) if details else '未找到相关限制',
            'sources': sources,
            'total_analyzed': result['found_tables']
        }

    except Exception as e:
        return {
            'has_restriction': False,
            'details': f"Vision 分析失败：{e}",
            'sources': [],
            'total_analyzed': 0
        }
