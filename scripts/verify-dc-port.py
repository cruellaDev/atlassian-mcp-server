#!/usr/bin/env python3
"""
skills/ 가 sooperset/mcp-atlassian 에 맞게 이식됐는지 기계적으로 검증한다.

왜 필요한가:
  손으로 대조하면 놓친다. 실제로 놓쳤다. 이 스크립트의 1차 버전은
  (a) jira_*/confluence_* 패턴만 봐서 이식 안 된 camelCase 툴을 통째로 못 봤고
  (b) 파라미터 이름만 보고 타입을 안 봐서 fields=[...] / additional_fields={...} 를 통과시켰다.
  둘 다 런타임에만 깨진다. 그래서 이 버전은 이름·타입·URL을 전부 본다.

사용법:
  python3 scripts/verify-dc-port.py <mcp-atlassian 소스 경로>

소스 경로 구하기 (셋 중 아무거나):
  1. pip show -f mcp-atlassian        → site-packages 안에 소스가 그대로 있다
  2. git clone https://github.com/sooperset/mcp-atlassian
  3. 사내 Artifactory 경유 설치본의 site-packages

  ※ "폐쇄망이라 소스를 못 본다"는 틀린 전제다. 설치했으면 소스는 이미 디스크에 있다.

소스를 정말 못 구하면:
  /mcp 로 실제 툴 목록을 받아 HANDOVER.md 4번 표와 눈으로 대조하는 수밖에 없다.
  그건 최후 수단이다.

종료 코드: 0 = 통과, 1 = 문제 발견
"""
import ast
import glob
import os
import re
import sys

# 공식 Cloud 스킬에 등장하던 툴들. 이식 후엔 하나도 남아있으면 안 된다.
CLOUD_TOOLS = [
    "search", "searchJiraIssuesUsingJql", "searchConfluenceUsingCql",
    "getConfluencePage", "createConfluencePage", "updateConfluencePage",
    "createJiraIssue", "getJiraIssue", "editJiraIssue", "addCommentToJiraIssue",
    "getVisibleJiraProjects", "lookupJiraAccountId", "getAccessibleAtlassianResources",
    "getConfluenceSpaces", "getJiraIssueTypeMetaWithFields",
    "getJiraProjectIssueTypesMetadata", "getTransitionsForJiraIssue",
    "transitionJiraIssue", "createIssueLink", "getIssueLinkTypes",
    "addWorklogToJiraIssue", "getJiraIssueRemoteIssueLinks",
    "getConfluencePageFooterComments", "createConfluenceFooterComment",
    "atlassianUserInfo", "getPagesInConfluenceSpace",
]

# DC 에 존재하지 않는 URL 형태. 4번은 이식 중 sed 가 만들어낸 가짜다.
BAD_URLS = [
    (r"atlassian\.net", "Cloud 호스트. DC 아님"),
    (r"rest/api/3", "Cloud v3 API. DC 는 v2"),
    (r"/wiki/spaces/", "Cloud Confluence 경로"),
    (r"/display/[^/\s\]]+/pages/", "존재하지 않는 형태. DC 는 /display/SPACE/Page+Title 또는 /pages/viewpage.action?pageId=N"),
    (r"\[사내jira\][^\s\)\]]*/wiki/", "Confluence 경로가 Jira 호스트에 붙어있다"),
]


def extract_args(src, open_paren):
    """여는 괄호 위치에서 짝이 맞는 닫는 괄호까지의 인자 문자열을 돌려준다.

    단순히 [^)]* 로 잡으면 JQL 안의 `(text ~ "x" OR ...)` 에서 잘려서
    뒤에 오는 fields=[...] 같은 진짜 인자를 못 본다. 실제로 그렇게 놓쳤다.
    문자열 리터럴 안의 괄호는 세지 않는다.
    """
    depth, i, quote = 0, open_paren, None
    while i < len(src):
        c = src[i]
        if quote:
            if c == quote and src[i - 1] != "\\":
                quote = None
        elif c in "\"'":
            quote = c
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return src[open_paren + 1:i]
        elif c == "\n" and depth == 1 and src[i - 1] == "\n":
            return None  # 빈 줄이 나오면 코드 블록이 아니다
        i += 1
    return None


def real_tools(src_root):
    """mcp-atlassian 소스에서 툴 이름과 파라미터 타입을 추출한다."""
    tools = {}
    for fname, prefix in [("jira.py", "jira_"), ("confluence.py", "confluence_")]:
        path = os.path.join(src_root, "src/mcp_atlassian/servers", fname)
        if not os.path.exists(path):
            sys.exit(f"소스를 찾을 수 없다: {path}\n경로가 mcp-atlassian 루트인지 확인하라.")
        tree = ast.parse(open(path).read())
        for node in ast.walk(tree):
            if not isinstance(node, ast.AsyncFunctionDef):
                continue
            params = {}
            for arg in node.args.args:
                if arg.arg == "ctx" or arg.annotation is None:
                    continue
                # Annotated[TYPE, Field(...)] 에서 TYPE 만 꺼낸다
                sl = getattr(arg.annotation, "slice", arg.annotation)
                try:
                    ty = ast.unparse(sl.elts[0]) if hasattr(sl, "elts") else ast.unparse(sl)
                except Exception:
                    ty = "?"
                params[arg.arg] = ty
            tools[prefix + node.name] = params
    return tools


def check(skills_glob, tools):
    problems = []

    def add(path, line, kind, msg):
        problems.append((path, line, kind, msg))

    for path in sorted(glob.glob(skills_glob[0]) + glob.glob(skills_glob[1])):
        src = open(path).read()
        rel = os.path.relpath(path)

        def lineno(pos):
            return src.count("\n", 0, pos) + 1

        # 1) 이식 안 된 Cloud 툴이 남아있는가
        for t in CLOUD_TOOLS:
            for m in re.finditer(r"\b" + re.escape(t) + r"\s*\(", src):
                add(rel, lineno(m.start()), "이식누락", f"Cloud 툴 `{t}(` 이 그대로 남아있다")

        # 2) 부르는 mcp-atlassian 툴이 실재하는가 + 3) 파라미터 이름/타입
        for m in re.finditer(r"\b((?:jira|confluence)_[a-z_]+)\s*\(", src):
            tool = m.group(1)
            ln = lineno(m.start())
            if tool not in tools:
                add(rel, ln, "없는툴", f"`{tool}` 은 mcp-atlassian 에 존재하지 않는다")
                continue
            raw = extract_args(src, m.end() - 1)
            if raw is None:
                continue  # 호출이 아니라 산문 속 언급
            # JQL/CQL 문자열 안의 `project = "X"` 를 kwarg 로 오인하지 않도록 문자열을 먼저 지운다.
            args = re.sub(r"(['\"]).*?\1", '""', raw, flags=re.S)
            for pm in re.finditer(r"(\w+)\s*=(?!=)\s*([^,\n]*)", args):
                p, val = pm.group(1), pm.group(2).strip()
                if p not in tools[tool]:
                    add(rel, ln, "없는파라미터",
                        f"`{tool}({p}=...)` — 실제: {', '.join(sorted(tools[tool])) or '(없음)'}")
                    continue
                # 타입 검사: str 을 받는데 리스트/딕셔너리를 넘기는가
                ty = tools[tool][p]
                if "str" in ty and "list" not in ty and "dict" not in ty:
                    orig = re.search(re.escape(p) + r"\s*=\s*(.)", raw)
                    if orig and orig.group(1) in "[{":
                        add(rel, ln, "타입불일치",
                            f"`{tool}({p}=...)` 에 {'리스트' if orig.group(1)=='[' else '딕셔너리'}를 넘긴다. "
                            f"실제 타입은 `{ty}`")

        # 3-b) 툴 호출 밖에 단독으로 나오는 인자 블록.
        #      예: "3. Include in `additional_fields` when creating:" 아래의 additional_fields={...}
        #      호출 안이 아니라서 위 검사가 못 본다. 문자열이어야 하는 인자는 어디에 있든 잡는다.
        for p, opener, want in [("additional_fields", "{", "JSON 문자열"),
                                ("fields", "[", "콤마 구분 문자열")]:
            for m in re.finditer(r"^\s*" + p + r"\s*=\s*" + re.escape(opener), src, re.M):
                add(rel, lineno(m.start()), "타입불일치",
                    f"`{p}=` 에 {'딕셔너리' if opener == '{' else '리스트'}를 넘긴다. {want}여야 한다")

        # 4) DC 에 없는 URL 형태
        lines = src.split("\n")
        for pat, why in BAD_URLS:
            for m in re.finditer(pat, src):
                ln = lineno(m.start())
                line = lines[ln - 1]
                # Cloud 와의 차이를 설명하는 주석 자체는 Cloud URL 을 인용할 수밖에 없다.
                # 줄 전체를 봐야 판별된다 — 좁은 문맥 창으로는 "아니다"를 놓친다.
                if any(k in line for k in ("아니다", "대응 없음", "존재하지 않는", "형태가 아님")):
                    continue
                add(rel, ln, "잘못된URL", f"{why} — {line.strip()[:90]}")

    return problems


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    tools = real_tools(sys.argv[1])
    problems = check(("skills/*/SKILL.md", "skills/*/references/*.md"), tools)

    print(f"mcp-atlassian 툴 {len(tools)}개 로드됨\n")
    if not problems:
        print("✅ 통과 — 이식 누락·없는 툴·파라미터·타입·URL 문제 없음")
        return 0

    by_kind = {}
    for p in problems:
        by_kind.setdefault(p[2], []).append(p)
    for kind in sorted(by_kind):
        print(f"━━ {kind} ({len(by_kind[kind])}건)")
        for path, ln, _, msg in by_kind[kind]:
            print(f"  {path}:{ln}\n    {msg}")
        print()
    print(f"❌ 총 {len(problems)}건")
    return 1


if __name__ == "__main__":
    sys.exit(main())
