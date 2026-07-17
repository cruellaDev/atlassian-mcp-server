# 인계 문서 — 이 포크가 뭐고, 왜 이렇게 됐는가

> **이 문서를 읽는 Claude에게:** 당신은 이 작업의 이전 맥락이 전혀 없다. 이 문서가 그 맥락 전부다.
> 여기 적힌 사실들은 인터넷이 있는 환경에서 **실제로 소스를 읽고 실행해서** 확인한 것이다.
> 추측으로 덮어쓰지 마라. 확인 안 된 것은 **[미확인]** 으로 표시돼 있다.
>
> **단, 이 문서를 맹신하지도 마라.** 당신은 대부분 검증할 수 있다 (아래 참고).
> 이 문서는 검증을 대신하는 게 아니라 **어디를 봐야 하는지 알려주는 것**이다.
>
> 작성 2026-07-17.

## 0. 먼저 할 일 — 이 순서로

```
1. 사람에게 물어라           → 섹션 7 (Q1~Q8). 회사 정보가 이 레포에 없다
2. /mcp 로 툴 목록을 받아라   → 섹션 4 표와 대조
3. 검사기를 돌려라           → 섹션 6. 기계가 잡는다. 눈으로 대조하지 마라
4. 그 다음에 손대라
```

**섹션 1~5는 배경이다.** 왜 이렇게 됐는지 알아야 할 때만 읽어라.

---

## 1. 30초 요약

이 레포는 `atlassian/atlassian-mcp-server`의 포크다. 브랜치 **`dc-port`**가 작업본이다.

**목적:** Atlassian 공식 MCP 서버가 **Cloud 전용**이라 사내 Data Center에서 못 쓴다.
그래서 서드파티 `sooperset/mcp-atlassian`(PAT로 DC 지원)을 붙이고,
**Atlassian 공식 스킬을 그 서버에 맞게 이식**했다.

| | |
|---|---|
| 브랜치 | `dc-port` (main은 upstream 그대로 둘 것) |
| 이식 완료 | 스킬 5개. 6번째(`jira-sprint-dashboard-canvas`)는 원래 손댈 게 없었음 |
| 검증 | 툴 11개 실재 확인, 파라미터 전부 시그니처 대조 완료 |
| 관련 레포 | `company-claude-plugin` — 사내 배포용 플러그인. 문서 다수 거기 있음 |

---

## 2. 왜 공식을 못 쓰는가 (재론 금지)

**공식 레포엔 서버 코드가 없다.** 전체가 이거였다:

```json
// .mcp.json (upstream main)
{ "mcpServers": { "atlassian": {
    "type": "http", "url": "https://mcp.atlassian.com/v1/mcp/authv2" }}}
```

인증·API·툴 구현 전부 Atlassian 호스팅 서버 뒤 클로즈드 소스다. **포크해도 고칠 코드가 없다.**
이 포크에서 값어치 있는 건 **`skills/` 뿐이다.**

**공식 입장** — issue #16, 콜라보레이터 `jatinkrmalik`, 2026-06-26:

> MCP server currently supports Atlassian Cloud only. **Connectivity is tied to Cloud sites and Cloud authentication**, so Data Center and self-managed deployments aren't supported.
> ...that's a **product roadmap decision**... We don't have a timeline or commitment to share right now.

| 이슈 등록 | 2025-11-10 |
|---|---|
| 첫 공식 답변 | 2026-06-26 (**7.5개월 후**) |
| 내용 | 확답 불가 |
| assignee / milestone | 없음 / 없음 |

**막힌 게 기술이 아니라 사업 결정이다.** "product roadmap decision"이라는 표현이 그 증거다.
기술 문제였으면 "PR 환영"이라 했을 것이다. **DC 지원 PR을 보내도 머지될 이유가 없다. 시도하지 마라.**

**기술적 이유:** Cloud MCP는 Jira에 직접 붙지 않고 `api.atlassian.com/ex/jira/{cloudId}/...`
OAuth 게이트웨이를 경유한다. 공식 툴에 `getAccessibleAtlassianResources`(cloudId 조회)가 있는 이유다.
**DC엔 그 게이트웨이가 없다.** URL 교체 문제가 아니라 계층이 다르다.

---

## 3. ⚠️ 이 포크를 유지하는 이유 — 지우지 마라

**Apache 2.0이라 스킬을 복사해가도 법적으로는 문제없다.** 그런데도 포크를 쓰는 이유는 **유지보수**다.

**upstream이 살아 있다:**

| skills/ 총 커밋 | 7개 |
|---|---|
| 최근 skills/ 변경 | **2026-06-22** (약 3주 전) |
| 레포 최신 커밋 | 2026-07-09 (8일 전) |
| 최근 추가된 스킬 | `jira-sprint-dashboard-canvas` |

복사해가면 **2026-07-17에 얼어붙는다.** 포크는 `git pull upstream main`으로 개선을 계속 받는다.

### 🔑 결정적 발견 — upstream이 이식 부담을 없애주고 있다

2026-06-22 커밋 `a668374`의 제목:

> **"Add optimizations to reduce token consumption and to make the skill provider agnostic"**

**Atlassian이 스킬을 특정 MCP 제공자에서 떼어내는 작업을 하고 있다.**
그 커밋이 손댄 `jira-sprint-dashboard-canvas`를 측정한 결과:

```
jira-sprint-dashboard-canvas     툴이름  0개   cloudId 0개   ← 이식 불필요. 그냥 돈다
search-company-knowledge         툴이름 14개   cloudId 있음
spec-to-backlog                  툴이름 13개   cloudId 있음
triage-issue                     툴이름 11개   cloudId 있음
capture-tasks-from-meeting-notes 툴이름  9개   cloudId 있음
generate-status-report           툴이름  9개   cloudId 있음
```

방식은 **툴 이름 대신 JQL 같은 개념으로 말하게** 하는 것이다. JQL은 공식이든 mcp-atlassian이든 동일하게 받는다.

**즉 upstream이 스킬 하나 refactor할 때마다 이 포크의 diff가 하나씩 줄어든다.**
그 혜택은 포크한 쪽만 받는다.

### 남아있는 기회 — [미검증 아이디어]

나머지 5개를 같은 방식(provider-agnostic)으로 고쳐 **upstream에 PR**을 보낼 수 있다.
머지되면 이 포크의 diff가 **0**이 되고, Atlassian이 대신 관리하게 된다.

DC 서버 지원과 달리 이건 **사업 결정과 무관한 순수 개선**이고, Atlassian이 이미 그 방향으로 커밋했다.
거부할 이유가 적다. **단, 실제로 시도해본 적 없다. 판단은 사람에게 맡겨라.**

### 브랜치 전략

```
main       upstream 그대로. 절대 건드리지 마라 → git pull upstream main 이 항상 깨끗
dc-port    작업본. main 갱신되면 rebase 하고 아래 4번 표대로 재이식
```

---

## 4. 이식 규칙 — 재이식할 때 이 표를 쓴다

> **이 표는 `sooperset/mcp-atlassian` 소스에서 함수 정의를 직접 추출해 만들었다 (2026-07-17, main).**
> 사내 설치본 버전이 다르면 틀릴 수 있다. **`/mcp`로 실제 툴 목록을 받아 대조하라.**

### 툴 이름

| 공식 (Cloud) | mcp-atlassian |
|---|---|
| `searchJiraIssuesUsingJql` | `jira_search` |
| `searchConfluenceUsingCql` | `confluence_search` |
| `getConfluencePage` | `confluence_get_page` |
| `createConfluencePage` | `confluence_create_page` |
| `createJiraIssue` | `jira_create_issue` |
| `getJiraIssue` | `jira_get_issue` |
| `addCommentToJiraIssue` | `jira_add_comment` |
| `getVisibleJiraProjects` | `jira_get_all_projects` ⚠️ 아래 |
| `lookupJiraAccountId` | `jira_search_assignable_users` ⚠️ 아래 |
| `getJiraIssueTypeMetaWithFields` | `jira_get_create_fields` |
| `getJiraProjectIssueTypesMetadata` | `jira_get_project_issue_types` |
| `getTransitionsForJiraIssue` | `jira_get_transitions` |
| `transitionJiraIssue` | `jira_transition_issue` |
| `search` (Rovo 통합검색) | **없음** ⚠️ 아래 |
| `getConfluenceSpaces` | **없음** ⚠️ 아래 |
| `getAccessibleAtlassianResources` | **삭제** (cloudId 개념 없음) |

### 파라미터 — 이름만 바꾸면 조용히 실패한다

| 공식 | mcp-atlassian |
|---|---|
| `cloudId=...` | **줄 통째로 삭제** |
| `maxResults=` | `limit=` |
| `cql=` | `query=` |
| `issueIdOrKey=` | `issue_key=` |
| `projectKey=` / `projectIdOrKey=` | `project_key=` |
| `issueTypeName=` | `issue_type=` |
| `issueTypeId=` | `issue_type_id=` |
| `commentBody=` | `body=` |
| `pageId=` | `page_id=` |
| `contentFormat="markdown"` | `convert_to_markdown=True` |
| `spaceId=` (숫자) | `space_key=` (**키. 예: "ENG"**) |
| `body=` (confluence_create_page) | `content=` |
| `assignee_account_id=` | `assignee=` |
| `searchString=` | `query=` |

### 실제 시그니처 (소스에서 추출)

```
jira_search(jql, fields, limit, start_at, projects_filter, expand, page_token, use_display_names)
jira_get_issue(issue_key, fields, expand, comment_limit, properties, update_history, include, use_display_names)
jira_create_issue(project_key, summary, issue_type, assignee, description, components, additional_fields)
jira_add_comment(issue_key, body, visibility, public)
jira_get_all_projects(include_archived)
jira_search_assignable_users(query, project_key, issue_key, limit)
jira_get_transitions(issue_key)
jira_transition_issue(issue_key, transition_id, fields, comment)
jira_get_create_fields(project_key, issue_type_id)
jira_get_project_issue_types(project_key)
jira_search_fields(keyword, limit, refresh)
jira_link_to_epic(issue_key, epic_key)

confluence_search(query, limit, spaces_filter)
confluence_get_page(page_id, title, space_key, include_metadata, convert_to_markdown)
confluence_create_page(space_key, title, content, parent_id, content_format, ...)
confluence_add_comment(page_id, body)
```

### ⚠️ 이름 치환으로 안 끝나는 것들 — 여기서 사고가 난다

**1. `search` (Rovo 통합검색) → 대응 없음**
Confluence+Jira 동시 검색 툴이 DC엔 없다. **두 개를 병렬 호출하고 합쳐라:**
```
confluence_search(query="text ~ '검색어' OR title ~ '검색어'")
jira_search(jql="text ~ '검색어' OR summary ~ '검색어'")
```

**2. `getConfluenceSpaces` → 대응 없음**
mcp-atlassian의 Confluence 툴 35개 중 스페이스 목록 조회가 **없다.**
→ **사용자에게 스페이스 키를 물어라.** DC URL에 들어있다: `/display/<SPACEKEY>/...`

**3. `jira_create_issue`에 `parent` 없음 → 에픽 연결이 2단계**
```
jira_create_issue(...)                                    # 1) 생성
jira_link_to_epic(issue_key="새티켓", epic_key="PROJ-1")   # 2) 연결
```
연결 실패 시 티켓은 이미 생성된 상태다. **고아 티켓을 조용히 남기지 말고 사용자에게 알려라.**

**4. `jira_get_all_projects`에 `action="create"` 필터 없음**
공식은 "생성 권한 있는 프로젝트"만 줬다. mcp-atlassian은 **전부** 준다.
→ 권한 없는 프로젝트가 섞이므로 사용자 확인을 받아라.

**5. DC엔 `accountId`가 없다 → username / userKey**
다만 `jira_create_issue(assignee=...)`는 **이메일·표시이름·ID를 다 받아 서버가 해석한다.**
(`mcp-atlassian`이 내부에서 `query_param = "query" if is_cloud else "username"`으로 분기)
→ ID를 추출해 넘길 필요 없다. 조회 단계의 목적은 **실재 확인과 동명이인 판별**이다.

**6. URL 형태가 다르다**
| | Cloud | DC |
|---|---|---|
| Jira | `yoursite.atlassian.net/browse/KEY` | `[사내jira]/browse/KEY` |
| Confluence | `/wiki/spaces/SP/pages/123/title` | `/display/SP/Title` 또는 `/pages/viewpage.action?pageId=123` |
| REST | `rest/api/3` | **`rest/api/2`** |

`/display/SP/Title` 형태엔 **페이지 ID가 없다.** → `confluence_get_page(title=..., space_key=...)`

---

## 5. Data Center에서 아예 안 되는 툴

> 출처: mcp-atlassian `docs/compatibility.mdx` (2026-07-17)

```
jira_batch_get_changelogs              Cloud 전용 changelog API
jira_get_issue_proforma_forms          Cloud 전용 (cloud_id 필요)
confluence_get_page_views              Cloud 전용 분석 API
confluence_check_content_permissions   Cloud 전용
confluence_get_space_permissions       Cloud 전용
```

`confluence_search_user`는 DC에서 **group member API로 폴백**하므로 `group_name` 지정이 필요하다.

**포맷은 신경 쓸 필요 없다.** mcp-atlassian이 자동 변환한다 — Markdown으로 쓰면 DC엔 wiki markup으로 바뀐다.

⚠️ **커스텀 필드 ID는 Cloud와 다르다.** `customfield_XXXXX`가 하드코딩돼 있으면 **전부 틀린 값이고 조용히 실패한다.**
`jira_search_fields`로 사내 인스턴스의 실제 ID를 조회해 교체하라.

---

## 6. 검증 — 눈으로 대조하지 마라. 검사기가 있다

### 🔑 "폐쇄망이라 소스를 못 본다"는 틀린 전제다

이 문서의 초안이 그렇게 주장했고, 그건 **틀렸다.** 당신은 거의 다 검증할 수 있다:

| 소스 구하는 법 | 비고 |
|---|---|
| `pip show -f mcp-atlassian` | **설치했으면 소스가 이미 디스크에 있다.** 순수 파이썬 패키지다 |
| `git clone https://github.com/sooperset/mcp-atlassian` | GitHub이 뚫려 있으면 된다 |
| 사내 Artifactory 경유 설치본의 site-packages | 위와 같음 |

**소스가 있으면 4번 표를 믿을 필요가 없다. 대조하면 된다.**

### 검사기를 돌려라

```bash
python3 scripts/verify-dc-port.py <mcp-atlassian 소스 경로>
```

검사 항목: 이식 안 된 Cloud 툴 잔존 / 존재하지 않는 툴 / 없는 파라미터 / **타입 불일치** / DC에 없는 URL 형태.

> **왜 이게 있는가:** 이 이식의 1차 검증은 손으로 했고 **놓쳤다.**
> `jira_*` 패턴만 봐서 `updateConfluencePage`가 남은 걸 못 봤고,
> 파라미터 **이름**만 보고 **타입**을 안 봐서 `fields=[...]`(str이어야 함),
> `additional_fields={...}`(JSON str이어야 함)를 통과시켰다. 둘 다 런타임에만 깨진다.
> **눈으로 대조하면 놓친다. 실제로 놓쳤다.**

소스를 정말 못 구하면 `/mcp` 목록과 4번 표를 손으로 대조하는 수밖에 없다. **그건 최후 수단이다.**

### 실제 호출로 최종 확인

1. `/mcp` → 서버 connected + 툴 목록
2. 읽기 전용부터: "우리 문서에서 [아는 주제] 찾아줘"
   → `search-company-knowledge` 발동 + `jira_search`/`confluence_search` 호출되면 성공
3. 툴 이름 에러가 나면 → **에러 메시지에 찾던 이름이 그대로 찍힌다.** 그게 단서다.

**두 번 고쳐서 안 되면 멈춰라.** 추측으로 세 번째 수정을 하지 말고 에러 원문을 사람에게 보여줘라.

---

## 7. ⚠️ 사람에게 물어야 할 것 — 아무것도 건드리기 전에

**이 섹션을 건너뛰지 마라.** 이 레포엔 회사 정보가 **의도적으로 하나도 없다** (공개 포크다).
전부 물어서 채워라. 사용자는 프롬프트로 답할 수 있다.

### Q1. (필수) 실제 툴 목록 — 가장 중요

> "`/mcp` 쳐서 나오는 툴 목록 전체를 붙여넣어 주세요."

**4번 표는 2026-07-17 main 소스 기준이다.** 사내 설치본 버전이 다르면 이름이 다르다.
**받은 목록으로 4번 표를 검증한 뒤 작업하라.** 표를 그대로 믿지 마라.

### Q2. (필수) 툴 이름 prefix — 붙인 방식에 따라 다르다

> "MCP 서버를 `.mcp.json`에 직접 등록하셨나요, 플러그인으로 설치하셨나요? 서버/플러그인 이름이 뭔가요?"

**prefix가 두 가지다. 이걸 틀리면 아무것도 못 한다.**

| 붙인 방식 | 실제 호출명 |
|---|---|
| `.mcp.json` / `settings.json`에 직접 등록 | `mcp__<서버이름>__jira_search` |
| **플러그인으로 설치** | `mcp__plugin_<플러그인명>_<서버명>__jira_search` |

**Q1의 `/mcp` 출력에 실제 이름이 찍힌다. 거기서 확인하는 게 제일 확실하다.** 안 보이면 물어라.

### Q3. (필수) Confluence도 붙어 있는가?

> "Confluence도 연결돼 있나요, Jira만인가요?"

`CONFLUENCE_URL`/`CONFLUENCE_PERSONAL_TOKEN` 미설정이면 `confluence_*` 툴이 **아예 없다.**
→ `search-company-knowledge`, `generate-status-report`가 반쪽이 된다. **먼저 확인하고 범위를 조정하라.**

### Q4. (필수) `READ_ONLY_MODE`가 켜져 있는가?

켜져 있으면 쓰기 툴이 차단된다. 생성 계열 스킬은 테스트 불가 → **읽기 전용 스킬부터.**

### Q5. (필수) 어떤 스킬을 쓸 것인가?

```
search-company-knowledge          Confluence/Jira 검색·인용            읽기 전용 ← 여기부터
triage-issue                      버그 중복 확인 후 티켓 생성           읽기+생성
generate-status-report            Jira → 리포트 → Confluence 발행      읽기+생성
capture-tasks-from-meeting-notes  회의록 → 액션아이템 → 티켓            생성
spec-to-backlog                   스펙 → Epic/티켓 대량 생성           대량 생성 ⚠️ 마지막
jira-sprint-dashboard-canvas      스프린트 대시보드                    읽기 (이식 불필요)
```

**안 쓸 스킬은 건드리지 마라.** 순수 낭비다.

### Q6. (테스트용) 실존하는 프로젝트 키 / 검색어

> "테스트에 써도 되는 Jira 프로젝트 키 하나랑, 실제로 있는 걸 아시는 Confluence 검색어 하나만요."

**운영 프로젝트 말고 테스트 프로젝트를 요청하라.**

### Q7. (필요시) 커스텀 필드 ID

> "`jira_search_fields`로 필드 목록 한 번 뽑아주실 수 있나요?"

스킬에서 `customfield_`가 grep되면 **반드시 물어라.** Cloud와 번호가 다르고 조용히 실패한다 (5번).

### Q8. (필요시) Jira/Confluence DC 버전

Cloud 전용 툴 판별용 (5번). Jira **8.14 미만이면 PAT 기능 자체가 없다.**

---

## 8. 사내 스택 (확인됨)

```
코드        Bitbucket Data Center      ← 공식 마켓플레이스 256개 중 플러그인 0개
이슈        Jira Data Center
위키        Confluence Data Center
CI/CD       Jenkins (사내)             ← 플러그인 0개. Cloud/DC 구분 없는 오픈소스다
아티팩트     JFrog Artifactory (self-hosted)
            → PyPI/npm/Maven 리모트 프록시함 ✅ (설치가 한 줄로 끝남)
GitHub      Copilot용 지급 enterprise 계정. 코드 호스트 아님
```

**설치는 `company-claude-plugin/docs/INSTALL.md`에 있다.** Artifactory 경유가 주 경로다.

---

## 9. 🔒 절대 커밋하지 마라

이 레포는 **공개 포크**다 (`github.com/cruellaDev/atlassian-mcp-server`, PUBLIC).

```
PAT / 비밀번호 / 토큰 / Artifactory 토큰
사내 Jira/Confluence/Artifactory URL·도메인·IP
프로젝트 키 / 스페이스 키 / 사번 / 실명 / 이메일
커스텀 필드 ID / DC 버전
```

```bash
git diff --cached | grep -iE "PAT|token|password|jira\.|confluence\.|artifactory|customfield_"
```

**회사 정보가 하나도 없는 건 의도된 설계다.** 실제 값은 프롬프트로 주고받는다 (7번). 그 구조를 깨지 마라.

---

## 10. 이 세션에서 알아낸 것 중 문서화 안 된 나머지

- **issue #144** (Jira Assets/CMDB 추가 요청): 2026-04-18 등록, 3개월째 **공식 답변 0, 라벨조차 없음.**
  #16보다 방치 상태가 심하다. 이 레포 이슈는 로드맵 채널이 아니라 접수함이다.
- **`gh` CLI vs `github` 플러그인**: `github` 플러그인은 `api.githubcopilot.com`을 경유한다.
  `gh` CLI는 `GH_HOST`로 사내 호스트에 직접 붙는다. **후자가 짧고 결재도 필요 없다.**
- **`gitlab` 플러그인 함정**: `.mcp.json`에 `https://gitlab.com`이 **하드코딩**이라 사내 GitLab에 못 쓴다.
  반대로 `jfrog`는 `${JFROG_URL}/mcp`라 사내 가능. **`url`이 변수인지 도메인인지 1분이면 확인된다. 결재보다 이게 먼저다.**
- **관련 문서 위치**: `company-claude-plugin` 레포에
  `docs/INSTALL.md`(설치), `docs/PLUGIN-SURVEY.md`(256개 조사), `docs/CONTEXT7-SECURITY-REVIEW.md`(결재 자료),
  `plugins/onboarding/`(온보딩 스킬)이 있다.
