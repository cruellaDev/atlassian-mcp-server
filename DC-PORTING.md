# Data Center 이식 계획 — 공식 스킬을 사내 Jira/Confluence DC에 붙이기

> **이 문서를 읽는 Claude에게:** 이 문서는 인터넷이 차단된 폐쇄망에서 당신이 혼자 일할 수 있도록 쓰였다.
> 당신은 웹 검색·GitHub 접근이 불가능하다. 모르는 것은 **추측하지 말고 사용자에게 물어라.** 사용자는 프롬프트로 답할 수 있다.
> 무엇을 물어야 하는지는 **섹션 1에 전부 있다. 거기부터 시작하라.**
>
> 작성 2026-07-17 / 작성 시점 검증 기준: `sooperset/mcp-atlassian` main 브랜치

---

## 0. 30초 요약

**공식 Atlassian MCP 서버는 Data Center를 지원하지 않는다.** 앞으로도 미정이다 (근거: 섹션 5).
대신 서드파티 `sooperset/mcp-atlassian`을 PAT로 붙이고, **이 레포의 공식 스킬 6개는 그대로 재사용**한다.

스킬은 마크다운이고 서버와 분리돼 있다. 내용의 99%는 워크플로 산문(5단계 프로세스, 인용 형식, 출력 템플릿)이라 서버가 뭐든 무관하다. **툴 이름 몇 개만 치환하면 된다.** 그게 이 작업의 전부다.

| | |
|---|---|
| 버릴 것 | 공식 MCP **서버** (`.mcp.json` 한 줄) |
| 지킬 것 | 공식 **스킬** `skills/` 6개 ← 이 레포의 유일한 실속 |
| 대체할 것 | `sooperset/mcp-atlassian` + DC PAT |
| 실제 작업 | **스킬의 툴 이름 치환 + cloudId 단계 제거** (섹션 3) |

---

## 1. ⚠️ 먼저 물어볼 것 — 아무것도 건드리기 전에

**이 섹션을 건너뛰지 마라.** 아래 답 없이는 어떤 파일도 수정하면 안 된다.
이 문서는 공개 레포에 있어서 회사 정보가 하나도 안 적혀 있다. 전부 물어서 채워야 한다.

### Q1. (분기) 사내 MCP 서버가 이미 붙어 있는가?

> "지금 Claude Code에 Atlassian MCP 서버가 이미 연결돼 있나요? `/mcp` 쳐서 나오는 결과를 알려주세요."

| 답 | 다음 |
|---|---|
| **붙어 있다** (`mcp-atlassian` 등이 보임) | → Q2로. **주 경로다.** |
| **안 붙어 있다 / 설치부터 해야 한다** | → **부록 A(섹션 6)** 먼저. 폐쇄망 설치 절차가 거기 있다. |

> 사람마다 설정이 다르다. 이미 쓰던 사람도 있고 처음인 사람도 있다. **반드시 물어서 확인하라.**

### Q2. (필수) 실제 툴 목록 — 가장 중요

> "`/mcp` 에서 `mcp-atlassian` 서버의 툴 목록 전체를 붙여넣어 주세요."

**섹션 3의 치환표는 2026-07-17 main 브랜치 소스 기준이다.** 사내 설치본은 버전이 다를 수 있고, 그러면 툴 이름이 다르다.
**받은 실제 목록으로 치환표를 검증한 뒤 작업하라.** 이 문서 표를 그대로 믿고 치환하면 안 된다.

### Q3. (필수) 툴 이름 prefix

> "MCP 서버 이름이 `.mcp.json`에서 뭐로 등록돼 있나요? (PAT는 가리고 서버 이름 부분만)"

MCP 툴의 실제 호출명은 **`mcp__<서버이름>__<툴이름>`** 이다.
서버를 `mcp-atlassian`으로 등록했으면 → `mcp__mcp-atlassian__jira_search`.
`atlassian`으로 등록했으면 → `mcp__atlassian__jira_search`.
**prefix를 모르면 치환을 못 한다.** Q2 목록에서 보이면 그걸 쓰고, 안 보이면 물어라.

### Q4. (필수) Confluence도 붙어 있는가?

> "Confluence도 연결돼 있나요? 아니면 Jira만인가요?"

`CONFLUENCE_URL` / `CONFLUENCE_PERSONAL_TOKEN`을 설정 안 했으면 `confluence_*` 툴이 아예 없다.
그 경우 `search-company-knowledge`, `generate-status-report`(Confluence 발행) 같은 스킬이 반쪽이 된다. **먼저 확인하고 스킬 범위를 조정하라.**

### Q5. (필수) 어떤 스킬이 필요한가?

> "이 레포 스킬 6개 중 실제로 쓰실 게 뭔가요? 안 쓸 건 안 고치겠습니다."

```
search-company-knowledge          Confluence/Jira 통합 검색·인용        읽기 전용
triage-issue                      버그 중복 확인 후 티켓 생성            읽기+생성
generate-status-report            Jira → 상태 리포트 → Confluence 발행   읽기+생성
spec-to-backlog                   Confluence 스펙 → Epic/티켓 대량 생성  대량 생성 ⚠️
capture-tasks-from-meeting-notes  회의록 → 액션아이템 → 티켓             생성
jira-sprint-dashboard-canvas      스프린트 대시보드 시각화               읽기
```

**전부 고치지 마라.** 안 쓸 스킬 이식은 순수 낭비다.

### Q6. (필수) 쓰기 가능한 상태인가?

> "`READ_ONLY_MODE`가 켜져 있나요?"

켜져 있으면 `jira_create_issue` 등 쓰기 툴이 차단된다. 생성 계열 스킬은 테스트가 불가능하니 **읽기 전용 스킬부터** 이식하라.

### Q7. (테스트용) 실존하는 프로젝트/스페이스 하나

> "테스트에 써도 되는 Jira 프로젝트 키 하나랑, 실제로 있는 걸 아시는 Confluence 검색어 하나만 알려주세요."

검증(섹션 4)에 필요하다. **운영 프로젝트 말고 테스트 프로젝트를 요청하라.**

### Q8. (필요시) 커스텀 필드 ID

> "`jira_search_fields` 툴로 필드 목록 한 번 뽑아주실 수 있나요?"

**Cloud와 DC는 `customfield_XXXXX` 번호가 다르다.** 스킬이나 JQL에 하드코딩된 게 있으면 전부 틀린 값이고, 조용히 실패한다. 스킬에서 `customfield_` 를 grep해서 나오면 이 질문을 반드시 하라.

### Q9. (필요시) Jira DC 버전

> "Jira / Confluence DC 버전이 몇인가요? (우하단 또는 관리 → 시스템 정보)"

섹션 7의 Cloud 전용 툴 판별에 쓴다. 스킬이 그 툴을 부르면 그 단계를 들어내야 한다.

### Q10. (필요시) 스킬을 어디에 둘 것인가

> "스킬을 개인용(`~/.claude/skills/`)으로 둘까요, 프로젝트용(`.claude/skills/`)으로 둘까요, 팀 배포용인가요?"

팀 배포면 개인 설정 의존을 없애고 문서화를 더 해야 한다.

---

## 2. 확정 사항 (다시 논의하지 말 것)

- **서버는 `sooperset/mcp-atlassian`.** MIT, 소스 공개, 로컬 stdio 프로세스, 외부 통신 없음(사내 Jira/Confluence만 호출). DC를 PAT로 지원한다.
- **인증은 PAT.** Cloud의 API token과 다르다. DC PAT는 `Authorization: Bearer <PAT>`.
- **공식 서버는 대안이 아니다.** 섹션 5 참고. 기다리는 건 계획이 아니다.
- **스킬은 유지한다.** 이 레포에서 가치 있는 건 `skills/`뿐이다. 서버는 `.mcp.json` 한 줄이었다.

---

## 3. 주 작업 — 스킬 이식

### 3.1 사실 확인 (이 레포 grep 결과)

`mcp__atlassian__` prefix 하드코딩: **0곳.** 스킬은 툴 이름을 산문으로만 언급한다. 등장 전체:

```
4  search                            2  getConfluencePage
4  createJiraIssue                   2  getAccessibleAtlassianResources
2  searchJiraIssuesUsingJql          1  createConfluencePage
2  getVisibleJiraProjects
```

**7개다.** 이게 작업의 전체 규모다.

### 3.2 치환표

> ⚠️ **Q2에서 받은 실제 툴 목록으로 먼저 검증하라.** 아래는 2026-07-17 main 소스에서 함수 정의를 직접 추출한 것이며, 사내 설치본 버전이 다르면 틀릴 수 있다.
> ⚠️ 실제 호출 시엔 Q3의 prefix를 붙여라: `mcp__<서버이름>__jira_search`

| 공식 스킬 | → mcp-atlassian |
|---|---|
| `searchJiraIssuesUsingJql` | `jira_search` |
| `searchConfluenceUsingCql` | `confluence_search` |
| `getConfluencePage` | `confluence_get_page` |
| `createJiraIssue` | `jira_create_issue` |
| `createConfluencePage` | `confluence_create_page` |
| `getVisibleJiraProjects` | `jira_get_all_projects` |
| `addCommentToJiraIssue` | `jira_add_comment` |
| `getJiraIssue` | `jira_get_issue` |
| `transitionJiraIssue` | `jira_transition_issue` |
| `getTransitionsForJiraIssue` | `jira_get_transitions` |
| `lookupJiraAccountId` | `jira_search_assignable_users` ⚠️ 아래 3.4 |
| `search` (크로스 검색) | `jira_search` + `confluence_search` 병렬 |
| `getAccessibleAtlassianResources` | **삭제** |

### 3.3 반드시 같이 제거할 것

**1) `getAccessibleAtlassianResources` 호출 단계를 통째로 삭제.**
cloudId를 받아오는 툴인데 **DC엔 cloudId가 없다.** URL이 env var에 박혀 있다. 이 단계는 사라진다 — 즉 **단계가 줄어드는 방향이다.**

**2) 모든 코드 예제에서 `cloudId=...` 파라미터 제거.**

```
# 변경 전 (공식 스킬)
searchConfluenceUsingCql(cloudId="...", cql="text ~ '검색어'")

# 변경 후
confluence_search(query="text ~ '검색어'")
```

**3) `search`(크로스) 자리는 `jira_search` + `confluence_search` 병렬로.**
스킬이 이미 "Execute Parallel Search"라고 병렬 검색을 지시하고 있다. **원래 의도와 같으니 구조는 안 바꿔도 된다.**

### 3.4 주의 — 사용자 식별

DC는 `accountId`가 없다. `username` / `userKey`를 쓴다.
`capture-tasks-from-meeting-notes`가 담당자를 찾아 배정하는데, 여기가 갈라진다. mcp-atlassian이 내부적으로 분기 처리하지만(`query_param = "query" if is_cloud else "username"`), **스킬 산문에 "accountId를 조회한다"고 쓰여 있으면 그 표현을 고쳐라.** 안 그러면 당신(모델)이 없는 개념을 찾으려 든다.

### 3.5 권장 순서

| 순서 | 스킬 | 이유 |
|---|---|---|
| **1** | `search-company-knowledge` | **읽기 전용. 여기부터. 안전하다** |
| 2 | `triage-issue` | 읽기 + 생성 |
| 3 | `generate-status-report` | Confluence 발행 (Q4 확인 필수) |
| 4 | `spec-to-backlog` | **대량 생성. 마지막. 테스트 프로젝트에서만** |
| — | 나머지 | Q5에서 필요하다고 한 것만 |

---

## 4. 검증 — 인터넷 없이

웹으로 확인할 수 없다. **실제 툴 호출로만 검증한다.**

### Step 1. 연결
```
/mcp
```
→ 서버가 connected이고 툴 목록이 보이는가?

### Step 2. 읽기 전용 스킬
사용자에게 요청:
> "우리 회사 문서에서 [Q7에서 받은 검색어] 찾아줘"

- `search-company-knowledge`가 발동하는가?
- `jira_search` / `confluence_search`가 실제로 호출되는가?
- **툴 이름 에러가 나면** → 치환이 덜 된 것. 에러 메시지에 찾던 이름이 그대로 찍힌다. 그걸 단서로 남은 곳을 고쳐라.

### Step 3. 쓰기 (Q6에서 READ_ONLY가 꺼져 있을 때만)
**Q7의 테스트 프로젝트에서만.** 운영 프로젝트에 티켓을 만들지 마라.

### 실패했을 때
추측으로 두 번째 수정을 하지 마라. **에러 원문을 사용자에게 보여주고 물어라.** 폐쇄망에선 당신이 검색해서 확인할 방법이 없다.

---

## 5. 배경 — 왜 공식은 안 되는가 (근거)

`github.com/atlassian/atlassian-mcp-server` 레포엔 **서버 코드가 없다.** 전체가 이게 다였다:

```json
{ "mcpServers": { "atlassian": {
    "type": "http",
    "url": "https://mcp.atlassian.com/v1/mcp/authv2"
}}}
```

인증·API 호출·툴 구현 전부 Atlassian 호스팅 서버에 있다. **포크해도 고칠 코드가 없다.**

**공식 입장** — issue #16, 콜라보레이터 `jatinkrmalik`, 2026-06-26:

> MCP server currently supports Atlassian Cloud only. **Connectivity is tied to Cloud sites and Cloud authentication**, so Data Center and self-managed deployments aren't supported.
> ...that's a product roadmap decision... **We don't have a timeline or commitment to share right now.**

| 이슈 등록 | 2025-11-10 |
|---|---|
| 첫 공식 답변 | 2026-06-26 (**7.5개월 후**) |
| 내용 | 확답 불가 |
| assignee / milestone | 없음 / 없음 |
| 나머지 댓글 | 외부 +1 ×3 |

라벨을 붙여 열어둔 건 작업 중이라서가 아니라 "tracking thread"라고 명시했다.

**기술적 이유:** Cloud MCP는 Jira에 직접 붙지 않고 `api.atlassian.com/ex/jira/{cloudId}/...` OAuth 게이트웨이를 경유한다. 공식 툴에 `getAccessibleAtlassianResources`(cloudId 조회)가 있는 이유다. **DC엔 그 게이트웨이가 존재하지 않는다.** URL 교체 문제가 아니라 계층이 다르다.

**나중에 공식 지원이 나오면:** `.mcp.json` 한 줄 되돌리고 툴 이름만 원복하면 된다. **스킬 본문(워크플로)은 손댈 필요 없다.** 그게 이 접근의 핵심 이점이다.

---

## 6. 부록 A — 아직 설치 안 된 경우 (폐쇄망)

> Q1에서 "안 붙어 있다"고 답한 사람용. **이미 쓰고 있으면 이 섹션 건너뛰어라.**
> 사람마다 설정이 다르다. 팀에 새로 합류한 사람에게 이 절차가 필요하다.

### 완전 폐쇄망 설치

`uvx mcp-atlassian`(PyPI)도 `docker pull ghcr.io/...`도 방화벽에서 막힌다. 먼저 사내에 뭐가 있는지 물어라:

| 사내 인프라 | 설치 |
|---|---|
| 사내 PyPI 미러 (Nexus/Artifactory) | `uv pip install --index-url https://<사내미러>/simple mcp-atlassian` |
| 사내 Docker 레지스트리 (Harbor 등) | 외부에서 `ghcr.io/sooperset/mcp-atlassian:latest` pull → 사내 push |
| 둘 다 없음 | ↓ 반입 |

**반입 절차** — 인터넷 되는 PC에서:
```bash
# 업무망 PC와 동일한 OS/아키텍처/Python 기준으로 받아야 한다
pip download mcp-atlassian -d ./wheels --python-version 3.12 --only-binary=:all:
# ./wheels 를 반입 매체로 이동

# 업무망 PC
pip install --no-index --find-links=./wheels mcp-atlassian
```
Docker면: `docker save ghcr.io/sooperset/mcp-atlassian:latest -o mcp.tar` → 반입 → `docker load -i mcp.tar`

- **Python 3.10 이상** 필요 (`pyproject.toml: requires-python = ">=3.10"`)
- 플랫폼이 안 맞으면 휠이 안 맞는다. OS·아키텍처 확인할 것.

**보안팀 반입 심사 설명용:** MIT 라이선스, 소스 전체 공개. 로컬 stdio 프로세스로 동작하며 **외부로 데이터를 보내지 않는다** — 통신 상대는 사내 Jira/Confluence뿐. 인증은 사용자 개인 PAT.

### 사전 요구사항

| 항목 | 요구 |
|---|---|
| Jira DC | **8.14 이상** (미만이면 PAT 기능 자체가 없음) |
| Confluence DC | **6.0 이상** |
| Python | **3.10 이상** |

**PAT 발급:** 프로필 아이콘 → **Personal Access Tokens** → Create token (Jira/Confluence 각각). 발급 시 1회만 보인다. 만료일 확인.

### 설정

```json
{
  "mcpServers": {
    "mcp-atlassian": {
      "command": "uvx",
      "args": ["mcp-atlassian"],
      "env": {
        "JIRA_URL": "https://jira.사내도메인.com",
        "JIRA_PERSONAL_TOKEN": "<Jira PAT>",
        "CONFLUENCE_URL": "https://confluence.사내도메인.com",
        "CONFLUENCE_PERSONAL_TOKEN": "<Confluence PAT>"
      }
    }
  }
}
```

- **오프라인 설치본이면** `"command": "uvx", "args": ["mcp-atlassian"]` 대신 `"command": "python", "args": ["-m", "mcp_atlassian"]` 또는 설치된 실행파일 절대경로.
- **자체 서명 인증서** (업무망에서 흔함): 사내 CA가 OS 신뢰 저장소(Windows 인증서 저장소 / macOS 키체인 / Linux system CA)에 있으면 **자동 신뢰되므로 설정 불필요.** SSL 오류가 실제로 날 때만 `"JIRA_SSL_VERIFY": "false"`, `"CONFLUENCE_SSL_VERIFY": "false"` 추가. **먼저 끄고 시작하라.**
- **PAT가 안 되면(8.14 미만)**: `"JIRA_USERNAME": "<ID>"`, `"JIRA_API_TOKEN": "<비밀번호>"`. DC에선 `JIRA_API_TOKEN` 자리에 실제 비밀번호가 들어간다 (Cloud와 다름).
- **안전장치**: 처음엔 `"READ_ONLY_MODE": "true"`로 붙여서 사고를 막아라. 익숙해진 뒤 해제.

---

## 7. 부록 B — DC에서 다르게 동작하는 것

> 출처: mcp-atlassian `docs/compatibility.mdx` (2026-07-17 기준)

### Cloud 전용 — DC에서 아예 안 되는 툴

| 툴 | 사유 |
|---|---|
| `jira_batch_get_changelogs` | Cloud 전용 changelog API |
| `jira_get_issue_proforma_forms` | Cloud 전용 (cloud_id 필요) |
| `confluence_get_page_views` | Cloud 전용 분석 API |
| `confluence_check_content_permissions` | Cloud 전용 |
| `confluence_get_space_permissions` | Cloud 전용 |

스킬이 이것들을 부르면 그 단계를 삭제하거나 대체하라.

### 동작이 다른 것

| 항목 | Cloud | DC |
|---|---|---|
| 사용자 식별 | `accountId` | **`username` / `userKey`** |
| 이슈 설명 포맷 | ADF | **wiki markup** |
| API 버전 | v2 + v3 | **v2만** |
| `confluence_search_user` | CQL | **group member API — `group_name` 지정 필요** |
| Rate limit | ~100 req/min | 인스턴스별 |

**포맷은 신경 쓰지 마라.** mcp-atlassian이 자동 변환한다 — 항상 Markdown으로 쓰면 DC엔 wiki markup으로 알아서 바꾼다.

⚠️ **커스텀 필드 ID는 Cloud와 다르다.** Q8 참고.

---

## 8. 🔒 절대 커밋하지 말 것

**이 레포는 공개 포크다** (`github.com/cruellaDev/atlassian-mcp-server`, PUBLIC).

| 절대 금지 |
|---|
| **PAT / 비밀번호 / 토큰** — 사고다. 유출 시 즉시 폐기·재발급 |
| 사내 Jira/Confluence **URL·도메인·IP** |
| **프로젝트 키, 스페이스 키, 사번, 실명, 이메일** |
| **커스텀 필드 ID** (사내 스키마 노출) |
| DC 버전 (인프라 핑거프린팅) |
| 사내 JQL/CQL 예제에 박힌 실제 값 |

**이 문서에 회사 정보가 하나도 없는 건 의도된 설계다.** 답은 문서가 아니라 **업무망에서 프롬프트로** 받는다 (섹션 1). 그 구조를 깨지 마라.

작업 중 만든 메모·로그·설정 스니펫을 커밋하기 전에 반드시 확인하라. 커밋 전 최소한:

```bash
git diff --cached | grep -iE "PAT|token|password|사내도메인|jira\.|confluence\.|customfield_"
```

무언가 걸리면 커밋하지 말고 사용자에게 물어라.
