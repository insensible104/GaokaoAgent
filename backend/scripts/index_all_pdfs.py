"""
批量索引招生简章PDF到RAG系统

用法：
    python scripts/index_all_pdfs.py

要求：
    - PDF文件存放在 data/pdfs/ 目录下
    - 文件命名格式：{school_code}_{school_name}.pdf
    - 例如：10001_北京大学.pdf
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.engines.rag_enrollment_checker import get_rag_checker


def parse_filename(filename: str) -> tuple:
    """
    解析文件名获取院校代码和名称

    Args:
        filename: 文件名，格式 {code}_{name}.pdf

    Returns:
        (school_code, school_name) 或 (None, None)
    """
    if not filename.endswith(".pdf"):
        return None, None

    name_without_ext = filename[:-4]  # 去掉 .pdf

    # 尝试按 _ 分割
    parts = name_without_ext.split("_", 1)
    if len(parts) == 2:
        code, name = parts
        return code.strip(), name.strip()
    else:
        # 如果没有下划线，使用文件名作为院校名，代码为unknown
        return f"unknown_{name_without_ext}", name_without_ext.strip()


def main():
    print("=" * 60)
    print("招生简章PDF批量索引工具")
    print("=" * 60)

    # 1. 初始化RAG检查器
    print("\n[1/4] 初始化RAG系统...")
    rag_checker = get_rag_checker()

    if not rag_checker.is_available:
        print("❌ RAG系统不可用，请检查依赖是否安装：")
        print("   uv pip install --index-url https://pypi.tuna.tsinghua.edu.cn/simple chromadb sentence-transformers")
        return 1

    # 显示当前状态
    stats = rag_checker.get_stats()
    print(f"   当前已索引：{stats['schools_indexed']}所院校，{stats['total_rules']}条规则")

    # 2. 扫描PDF目录
    pdf_dir = project_root / "data" / "pdfs"
    print(f"\n[2/4] 扫描PDF目录：{pdf_dir}")

    if not pdf_dir.exists():
        print(f"⚠️  PDF目录不存在，正在创建：{pdf_dir}")
        pdf_dir.mkdir(parents=True, exist_ok=True)
        print(f"   请将招生简章PDF文件放入该目录，格式：院校代码_院校名称.pdf")
        print(f"   例如：10001_北京大学.pdf")
        return 0

    pdf_files = list(pdf_dir.glob("*.pdf"))
    print(f"   发现 {len(pdf_files)} 个PDF文件")

    if len(pdf_files) == 0:
        print("   目录为空，请添加PDF文件后重新运行")
        return 0

    # 3. 解析文件列表
    print("\n[3/4] 解析文件名...")
    schools_to_index = []

    for pdf_file in pdf_files:
        code, name = parse_filename(pdf_file.name)
        if code and name:
            schools_to_index.append({
                "code": code,
                "name": name,
                "path": str(pdf_file)
            })
            print(f"   ✓ {code} - {name}")
        else:
            print(f"   ✗ 跳过无效文件名：{pdf_file.name}")

    if len(schools_to_index) == 0:
        print("   未找到有效的PDF文件")
        return 1

    # 4. 批量索引
    print(f"\n[4/4] 开始索引 {len(schools_to_index)} 所院校...")
    success_count = 0
    failed_count = 0

    for i, school in enumerate(schools_to_index, 1):
        print(f"\n[{i}/{len(schools_to_index)}] {school['name']}")

        success = rag_checker.index_enrollment_document(
            school_code=school["code"],
            school_name=school["name"],
            pdf_path=school["path"],
            chunk_size=500,
            chunk_overlap=100
        )

        if success:
            success_count += 1
        else:
            failed_count += 1

    # 5. 总结
    print("\n" + "=" * 60)
    print("索引完成")
    print("=" * 60)
    print(f"✅ 成功：{success_count} 所")
    print(f"❌ 失败：{failed_count} 所")

    # 显示最终状态
    final_stats = rag_checker.get_stats()
    print(f"\n最终状态：")
    print(f"  已索引院校数：{final_stats['schools_indexed']}")
    print(f"  总规则数：{final_stats['total_rules']}")

    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
