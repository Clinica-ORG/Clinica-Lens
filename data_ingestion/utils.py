import re
from langchain_core.documents import Document


def is_table_of_contents_page(text_lines: list[str], max_lines_check=5) -> bool:
    """
    Detects if a PDF page is a Table of Contents
    args:
        text_lines: List of lines in string
    output:
        True if the page contains Table of contents
    """
    lines = [line.strip() for line in text_lines if line.strip()]

    if not lines:
        return False

    # Check top k lines that have text
    header_text = " ".join(lines[:max_lines_check]).lower()
    list_toc_name = ["contents", "table of contents", "toc", "summary", "index"]
    has_toc_keyword = any(kw in header_text for kw in list_toc_name)
    return has_toc_keyword


def format_table_of_contents(text_lines: list[str]) -> list[list]:
    """Reformat the table of contents (toc) extracted by chandra
    Chandra models mostly put toc as same level, so post-processing
    by rules are needed to have a format for downstream tasks
    args:
        markdown_lines: List of lines in string
    output:
        List of lines in string, each of them is in format (level, content, page)
    """
    if not isinstance(text_lines, list):
        raise TypeError("text_lines must have list as type")
    toc = []
    list_toc_name = ["contents", "table of contents", "toc", "summary", "index"]
    # top level are often in bold

    bold_match_compile = re.compile(r"\*\*([\w\s\.\-]+?)\*\*")
    title_match_compile = re.compile(r"^(#{1,6})\s+([\w\s]+)$")
    section_and_page_compile = re.compile(
        r"^\s*([^\n]+?)(?:[\t\.\-\_\s]{2,}|\t)\b(I{1,3}V?X?|VI{0,3}|XI{0,3}V?|XVI{0,3}|\d+)\b\s*$",
        re.IGNORECASE,
    )
    begin_with_number = re.compile(r"^[\d\.]+\s[^\n]+?$")
    has_bold = False
    top_level = 1
    for line in text_lines:
        stripped = line.replace(
            "|", ""
        ).strip()  # remove |, VLM often put in table form
        # if empty line -> skip
        if stripped == "":
            continue
        # Skip the title of ToC
        title_match = title_match_compile.match(string=stripped)
        if title_match and title_match.group(2).strip().lower() in list_toc_name:
            continue
        # check if there is bold format in toc (some toc doesnt use numbering)
        has_bold_match = bold_match_compile.findall(string=stripped)
        if len(has_bold_match) == 2:
            extracted_section_name, extracted_section_page = has_bold_match
            if not has_bold:
                has_bold = True
            toc.append([top_level, extracted_section_name, extracted_section_page])
        else:
            extract_s_p = section_and_page_compile.findall(string=stripped)
            if extract_s_p and len(extract_s_p[0]) == 2:
                extracted_section_name, extracted_section_page = extract_s_p[0]
                toc.append(
                    [
                        top_level
                        + int(has_bold)
                        + (
                            extracted_section_name.count(
                                "."
                            )  # h_n becomes h_n+1 is still acceptable
                            if begin_with_number.match(
                                extracted_section_name
                            )  # if annex we dont count dot
                            else 0
                        ),
                        extracted_section_name,
                        extracted_section_page,
                    ]
                )
    return toc


def fix_page_header_using_toc(
    text: str, toc: list[list], metadata_page_num: int
) -> str:
    """
    args:
        text: the text in markdown of the page
        toc: List of lines in ToC, each of them is in format [level, content, page]
        metadata_page_num: the number of the page to search in toc
    output:
        The Markdown text of the page with header corrected by the table of contents
    """
    concerned_page = [p for p in toc if p[-1].lower() == str(metadata_page_num).lower()]
    d_motif = {pattern: level for level, pattern, _ in concerned_page}
    res = []
    for line in text.splitlines():
        # WHO guidelines has mark in the headlines ...
        if "<mark>" in text:
            line = re.sub(
                r"^(#+)\s+.*?<mark>(.*?)</mark>\s*", r"\1 \2 ", line, flags=re.MULTILINE
            ).strip()
        for pattern, level in d_motif.items():
            if pattern in line:
                # fix heading
                replacement = "#" * level + " "
                line = re.sub(rf"^.*?(?={re.escape(pattern)})", replacement, line)
        res.append(line)
    return "\n".join(res)


def fix_doc_header_using_toc(
    toc: list[list], markdown_text: list[str], docs: list[Document]
) -> str:
    """
    args:
        toc: List of lines in ToC, each of them is in format [level, content, page]
        markdown_text: List of markdown text of each page
        docs: List of each page as Document
    output:
        The Markdown text of the document with header corrected by the table of contents
    """

    res_docs = []
    for page_md, page_pdf in zip(markdown_text, docs):
        metadata_page_num = (
            page_pdf.metadata["page_label"]
            if page_md["metadata"]["page_number"] != page_pdf.metadata["page_label"]
            else page_md["metadata"]["page_number"]
        )
        page_md_text = fix_page_header_using_toc(
            page_md["text"], toc, metadata_page_num
        )
        res_docs.append(page_md_text)
    return "".join(res_docs)
