# 폐쇄망에서 mcp-atlassian 설치하기

> **대상:** 인터넷이 차단된 업무망 PC에서 Claude Code에 사내 Jira/Confluence를 붙이려는 사람.
> Claude를 처음 써도 따라올 수 있게 썼다.
>
> **이 문서를 읽는 Claude에게:** 사용자가 Claude 사용이 처음일 수 있다. 용어를 설명하고, 한 번에 한 단계씩 진행하라.
> 모르는 것은 추측하지 말고 물어라. 당신은 폐쇄망에서 검색으로 확인할 수 없다.
>
> 작성 2026-07-17. 아래 수치·명령은 작성 시점에 **실제로 실행해서 검증**한 값이다.

---

## 0. 뭘 하는 건가

Claude Code가 사내 Jira/Confluence를 읽고 쓰게 만든다. 그러려면 **중개 프로그램(MCP 서버)** 이 하나 필요하다.

```
Claude Code  ──stdio──▶  mcp-atlassian  ──사내 HTTPS──▶  Jira/Confluence DC
  (내 PC)                  (내 PC)                        (사내 서버)
```

- `mcp-atlassian`은 **내 PC에서 도는 로컬 프로그램**이다. 외부로 나가지 않는다.
- 통신 상대는 **사내 Jira/Confluence뿐**이다.
- 인증은 **개인 PAT**(Personal Access Token)로 한다. 내 권한 그대로 동작한다 — 내가 못 보는 건 Claude도 못 본다.

> **왜 공식 Atlassian 플러그인을 안 쓰나:** 공식은 Atlassian **Cloud 전용**이다. Data Center는 지원하지 않고, 계획도 없다. 자세한 근거는 `DC-PORTING.md` 섹션 5.

---

## 1. 준비물 확인

설치 시작 전에 이것부터 확인하라. **하나라도 안 맞으면 뒤에서 막힌다.**

| 항목 | 요구 | 확인 방법 |
|---|---|---|
| Python | **3.10 이상** | `python --version` (Windows) / `python3 --version` (mac·리눅스) |
| Jira DC | **8.14 이상** | Jira 우하단 또는 관리 → 시스템 정보 |
| Confluence DC | **6.0 이상** | 동일 |
| Claude Code | 설치돼 있을 것 | `claude --version` |
| 반입 매체 | 사내 정책에 맞는 것 | 보안팀 |

> **Jira가 8.14 미만이면 PAT 기능 자체가 없다.** 그 경우 섹션 7의 폴백을 봐라.

### 먼저 물어볼 것 — 사내에 뭐가 있나

**설치 방법이 여기서 완전히 갈린다.** 정보팀/인프라팀에 물어라:

| 사내 인프라 | 설치 난이도 | 방법 |
|---|---|---|
| **사내 PyPI 미러** (Nexus / Artifactory) | 쉬움 | 섹션 2-A |
| **사내 Docker 레지스트리** (Harbor 등) | 중간 | 섹션 2-B |
| **둘 다 없음** (완전 폐쇄) | 어려움 | 섹션 2-C ← 대부분 여기 |

---

## 2-A. 사내 PyPI 미러가 있는 경우 (가장 쉬움)

```bash
pipx install --index-url https://<사내미러>/simple mcp-atlassian
```

`pipx`가 없으면:
```bash
pip install --index-url https://<사내미러>/simple mcp-atlassian
```

→ 섹션 3으로.

---

## 2-B. 사내 Docker 레지스트리가 있는 경우

인터넷 되는 PC에서:
```bash
docker pull ghcr.io/sooperset/mcp-atlassian:latest
docker tag ghcr.io/sooperset/mcp-atlassian:latest <사내레지스트리>/mcp-atlassian:latest
docker push <사내레지스트리>/mcp-atlassian:latest
```

레지스트리도 인터넷이 안 되면 파일로:
```bash
docker save ghcr.io/sooperset/mcp-atlassian:latest -o mcp-atlassian.tar   # 인터넷 PC
# mcp-atlassian.tar 반입
docker load -i mcp-atlassian.tar                                          # 업무망 PC
```

→ 섹션 3으로 (설정에서 `command`가 `docker`가 된다).

---

## 2-C. 완전 폐쇄망 — 휠 반입 (대부분 이 경우)

`pipx install mcp-atlassian`은 PyPI를 때리므로 **방화벽에서 막힌다.** 미리 받아서 들고 들어가야 한다.

### ⚠️ 핵심 함정 — 플랫폼을 맞춰야 한다

mcp-atlassian은 **컴파일된 네이티브 의존성 8개**를 쓴다:

```
cryptography   pydantic-core   lxml    orjson
rpds-py        pyyaml          markupsafe   charset-normalizer
```

이것들은 **OS·CPU·Python 버전별로 파일이 다르다.** 그냥 `pip download` 하면 **받는 PC 기준**으로 받아지고, 업무망 PC가 다르면 설치가 실패한다.

> 검증된 실제 수치 (Windows x64 + Python 3.12 기준):
> **휠 113개, 26MB.** 이 중 101개는 어디서나 도는 순수 파이썬, **12개가 플랫폼 종속**이다. 그 12개가 문제의 전부다.

### Step 1. 업무망 PC 사양 확인

업무망 PC에서 먼저 확인하라. **이 값으로 뒤 명령이 결정된다.**

```
python --version          → 예: 3.12.x
python -c "import platform; print(platform.machine())"   → 예: AMD64
```

| 업무망 PC | `--platform` 값 |
|---|---|
| Windows 64bit (대부분) | `win_amd64` |
| macOS Apple Silicon | `macosx_11_0_arm64` |
| macOS Intel | `macosx_10_9_x86_64` |
| Linux 64bit | `manylinux2014_x86_64` |

### Step 2. 인터넷 되는 PC에서 받기

**받는 PC의 OS는 상관없다.** `--platform`으로 지정하면 macOS에서 Windows용 휠을 받을 수 있다 (검증함).

```bash
pip download mcp-atlassian \
  -d wheels \
  --only-binary=:all: \
  --platform win_amd64 \
  --python-version 3.12
```

- `--platform`과 `--python-version`을 **업무망 PC 기준으로** 바꿔라.
- `--only-binary=:all:`는 **필수다.** 빼면 `--platform`이 동작하지 않는다.
- 결과: `wheels/` 폴더에 113개 안팎, 26MB 안팎.

**받은 게 맞는지 확인** — 네이티브 휠에 플랫폼 이름이 박혀 있어야 한다:
```bash
ls wheels | grep -E "cryptography|pydantic_core|lxml"
```
```
cryptography-49.0.0-cp311-abi3-win_amd64.whl        ← win_amd64 확인
lxml-6.1.1-cp312-cp312-win_amd64.whl                ← cp312 = Python 3.12 확인
pydantic_core-2.46.4-cp312-cp312-win_amd64.whl
```
여기에 `macosx`나 `linux`가 보이면 **잘못 받은 것이다.** 다시 받아라.

### Step 3. 반입

`wheels/` 폴더 전체를 사내 절차대로 반입한다. (섹션 8에 보안팀 설명용 정리)

### Step 4. 업무망 PC에서 설치

**pipx 권장** — venv를 격리해주고 실행파일을 PATH에 올려준다:
```bash
pipx install --pip-args="--no-index --find-links=C:\경로\wheels" mcp-atlassian
```

pipx가 없으면 venv + pip:
```bash
python -m venv C:\mcp-atlassian-env
C:\mcp-atlassian-env\Scripts\pip install --no-index --find-links=C:\경로\wheels mcp-atlassian
```

- `--no-index` = **PyPI를 아예 보지 마라.** 이게 있어야 폐쇄망에서 돈다.
- `--find-links` = 반입한 휠 폴더 경로.

> **검증됨:** 네트워크를 완전히 끊은 상태(`--no-index`)에서 113개 휠만으로 설치가 완주되고 실행까지 확인했다. 빠진 의존성은 없다.

### Step 5. 설치 확인

```bash
mcp-atlassian --help
```
pipx가 아니면: `C:\mcp-atlassian-env\Scripts\mcp-atlassian --help`

이렇게 나오면 성공:
```
Usage: mcp-atlassian [OPTIONS]
  MCP Atlassian Server - Jira and Confluence functionality for MCP
  Supports both Atlassian Cloud and Jira Server/Data Center deployments.
  Authentication methods supported: ... Personal Access Token (Server/Data Center) ...
```

> `AuthlibDeprecationWarning`이 뜰 수 있다. **정상이다. 무시하라.**

---

## 3. PAT 발급

**Jira와 Confluence가 별도 서버면 각각 발급해야 한다.**

1. Jira 웹 접속 → 우측 상단 **프로필 아이콘** 클릭
2. **Personal Access Tokens** 메뉴
3. **Create token** → 이름 입력 (예: `claude-code`) → 만료일 설정
4. **생성된 토큰을 복사한다. 이 화면을 벗어나면 다시 볼 수 없다.**
5. Confluence에서 같은 과정 반복

> 메뉴가 안 보이면 관리자가 PAT를 막아둔 것이다. 정보팀에 문의하라.
> **토큰은 비밀번호와 같다.** 채팅·이메일·Git에 올리지 마라.

---

## 4. Claude Code 설정

설정 파일 위치:

| OS | 경로 |
|---|---|
| Windows | `%USERPROFILE%\.claude\settings.json` |
| macOS / Linux | `~/.claude/settings.json` |

프로젝트 단위로 하려면 프로젝트 폴더의 `.mcp.json`.

```json
{
  "mcpServers": {
    "mcp-atlassian": {
      "command": "mcp-atlassian",
      "env": {
        "JIRA_URL": "https://jira.사내도메인.com",
        "JIRA_PERSONAL_TOKEN": "<Jira PAT>",
        "CONFLUENCE_URL": "https://confluence.사내도메인.com",
        "CONFLUENCE_PERSONAL_TOKEN": "<Confluence PAT>",
        "READ_ONLY_MODE": "true"
      }
    }
  }
}
```

### 처음엔 반드시 `READ_ONLY_MODE: true`

읽기만 되고 티켓 생성·수정이 차단된다. **익숙해진 뒤 지워라.** 처음부터 쓰기를 열면 운영 프로젝트에 사고가 난다.

### `command` 값 정하기

| 설치 방식 | `command` / `args` |
|---|---|
| pipx | `"command": "mcp-atlassian"` |
| venv | `"command": "C:\\mcp-atlassian-env\\Scripts\\mcp-atlassian.exe"` |
| Docker | `"command": "docker"`, `"args": ["run","--rm","-i", ...]` |

> Windows 경로는 JSON에서 **역슬래시를 두 번** 써야 한다: `C:\\경로\\파일`.

### 유용한 옵션 (실제 `--help`로 확인함)

| env var | 용도 |
|---|---|
| `READ_ONLY_MODE` | 쓰기 전면 차단. **처음엔 `true`** |
| `JIRA_PROJECTS_FILTER` | 검색을 특정 프로젝트로 제한 (콤마 구분) |
| `CONFLUENCE_SPACES_FILTER` | 검색을 특정 스페이스로 제한 |
| `ENABLED_TOOLS` | 쓸 툴만 화이트리스트 (콤마 구분) |
| `JIRA_SSL_VERIFY` / `CONFLUENCE_SSL_VERIFY` | 아래 참고 |

### 사내 자체 서명 인증서

**먼저 아무것도 하지 마라.** 사내 CA가 OS 신뢰 저장소(Windows 인증서 저장소 / macOS 키체인 / Linux system CA)에 등록돼 있으면 **자동으로 신뢰된다.**

SSL 오류가 **실제로 났을 때만** 추가하라:
```json
"JIRA_SSL_VERIFY": "false",
"CONFLUENCE_SSL_VERIFY": "false"
```
> 이건 검증을 끄는 것이므로 최후 수단이다. 가능하면 사내 CA를 OS에 등록하는 게 옳다.

---

## 4-B. 팀에 배포한다면 — 사내 플러그인으로 묶기

> 섹션 4는 **한 사람이 직접 설정**하는 방법이다. 팀원 여러 명에게 배포할 거면 이쪽이 낫다.
> 팀원이 JSON을 손댈 필요가 없어진다.

**문제:** 팀원마다 PAT가 다르다. 그렇다고 PAT를 레포에 커밋할 수는 없다.

**해결:** 플러그인 매니페스트의 `userConfig` + `"sensitive": true`.

`.claude-plugin/plugin.json`:
```json
{
  "name": "사내플러그인이름",
  "description": "사내 Jira/Confluence 연동 + 온보딩",
  "userConfig": {
    "jira_url": {
      "type": "string",
      "title": "사내 Jira 주소",
      "description": "예: https://jira.사내도메인.com",
      "required": true
    },
    "jira_pat": {
      "type": "string",
      "title": "Jira Personal Access Token",
      "description": "Jira 프로필 → Personal Access Tokens 에서 발급",
      "sensitive": true
    }
  },
  "mcpServers": {
    "atlassian": {
      "command": "mcp-atlassian",
      "env": {
        "JIRA_URL": "${user_config.jira_url}",
        "JIRA_PERSONAL_TOKEN": "${user_config.jira_pat}",
        "READ_ONLY_MODE": "true"
      }
    }
  },
  "skills": "./skills/"
}
```

**동작:** 팀원이 플러그인을 켜면 **Claude가 PAT를 한 번 물어본다.** 입력값은 macOS 키체인 또는 `~/.claude/.credentials.json`에 저장되고 **레포엔 안 들어간다.**

| | |
|---|---|
| `"sensitive": true` | 키체인 / `.credentials.json`에 저장. 버전관리 안 됨 |
| 일반 값 | `~/.claude/settings.json`의 `pluginConfigs[플러그인id].options` |
| 참조 문법 | `${user_config.키이름}` — `command`·`args`·`env`·`url`·`headers`에서 사용 가능 |

> 변수 확장 문법은 `${VAR}` / `${VAR:-기본값}` 두 가지뿐이다. bash식 `${VAR#패턴}` 같은 건 안 된다.
> 변수가 안 설정돼 있고 기본값도 없으면 **경고만 뜨고 문자열이 그대로 들어간다.** 조용히 깨지므로 `required: true`를 쓰거나 기본값을 줘라.

**플러그인 구조** — 이 레포와 같다. 그대로 템플릿으로 써라:
```
사내플러그인/
├── .claude-plugin/
│   └── plugin.json      ← 위 내용 (userConfig + mcpServers + skills)
├── skills/
│   ├── (DC-PORTING.md 따라 이식한 공식 스킬들)
│   └── onboarding/
│       └── SKILL.md     ← 팀 온보딩용 자체 스킬
```

> ⚠️ **플러그인은 mcp-atlassian이 이미 설치돼 있어야 동작한다.** 플러그인이 설치까지 해주지는 않는다. 팀원은 섹션 2를 먼저 거쳐야 하고, 플러그인은 그 다음 단계(설정 + 스킬)를 자동화하는 것이다.
> 팀 배포 시엔 반입한 `wheels/` 폴더를 사내 공유 스토리지에 두고 설치 절차를 온보딩 스킬에 적어두는 게 현실적이다.

> ⚠️ 위 `userConfig` 문법은 공식 문서 기준이다. **사내 Claude Code 버전에서 실제로 되는지 먼저 테스트하라.** 안 되면 섹션 4의 수동 설정으로 폴백하면 된다.

---

## 5. 검증

Claude Code를 **완전히 껐다가 다시 켜라.** 설정은 시작할 때만 읽는다.

### Step 1. 연결 확인
```
/mcp
```
`mcp-atlassian`이 **connected**로 뜨고 툴 목록이 보이면 성공.

### Step 2. 실제 호출
Claude에게:
> "JIRA-123 이슈 내용 알려줘"   ← 실제 존재하는 티켓 키로

또는:
> "우리 Confluence에서 [아는 주제] 검색해줘"

### 안 되면 → 섹션 6

---

## 6. 트러블슈팅

| 증상 | 원인 / 조치 |
|---|---|
| `/mcp`에 안 나옴 | Claude Code 재시작했나? 설정 파일 JSON 문법 오류 확인 (콤마·따옴표) |
| `command not found` | `command` 경로가 틀림. `mcp-atlassian --help`가 되는 경로를 절대경로로 |
| `is not a supported wheel on this platform` | **휠 플랫폼 불일치.** 섹션 2-C Step 1로 돌아가 `--platform`/`--python-version` 다시 확인 |
| `No matching distribution found` | 휠이 빠졌다. `--only-binary=:all:` 빼먹었는지 확인 |
| `SSL: CERTIFICATE_VERIFY_FAILED` | 사내 CA 미등록. 섹션 4의 SSL 항목 |
| `401 Unauthorized` | PAT가 틀렸거나 만료. 재발급 |
| `403 Forbidden` | PAT는 맞는데 권한 없음. 내 계정이 그 프로젝트를 볼 수 있는지 웹에서 확인 |
| 연결은 되는데 검색 결과 0 | `JIRA_PROJECTS_FILTER` / `CONFLUENCE_SPACES_FILTER`가 걸려 있나 확인 |
| 쓰기가 안 됨 | `READ_ONLY_MODE`가 `true`. 의도된 동작 |
| `AuthlibDeprecationWarning` | 정상. 무시 |

**두 번 고쳐서 안 되면 멈춰라.** 추측으로 세 번째 수정을 하지 말고, 에러 원문을 그대로 들고 물어라. 폐쇄망에선 검색으로 확인할 수 없다.

---

## 7. PAT를 못 쓰는 경우 (Jira 8.14 미만)

username + 비밀번호로 폴백한다:
```json
"JIRA_USERNAME": "<사번/ID>",
"JIRA_API_TOKEN": "<비밀번호>"
```
> DC에선 `JIRA_API_TOKEN` 자리에 **실제 비밀번호**가 들어간다 (Cloud와 이름만 같고 내용이 다르다).
> 보안상 PAT가 낫다. 가능하면 Jira 업그레이드를 요청하라.

---

## 8. 보안팀 반입 심사 설명용

| 항목 | 내용 |
|---|---|
| 소프트웨어 | `mcp-atlassian` (오픈소스) |
| 라이선스 | **MIT** |
| 소스 | `github.com/sooperset/mcp-atlassian` — 전체 공개 |
| 동작 방식 | 사용자 PC의 **로컬 프로세스** (stdio) |
| 외부 통신 | **없음.** 통신 상대는 사내 Jira/Confluence뿐 |
| 인증 | 사용자 **개인 PAT**. 사용자 권한을 그대로 상속 — 권한 상승 없음 |
| 데이터 반출 | 없음. 조회 결과는 로컬 Claude Code로만 전달 |
| 반입물 | Python 휠 113개 (약 26MB), 전부 PyPI 공개 패키지 |
| 권한 통제 | `READ_ONLY_MODE`로 쓰기 전면 차단 가능. `JIRA_PROJECTS_FILTER`로 접근 프로젝트 제한 가능 |

> **주의:** Claude Code 자체가 조회 결과를 Anthropic API로 보낸다(모델 추론). 이건 mcp-atlassian이 아니라 Claude Code의 동작이며, **사내에서 Claude 사용이 이미 승인됐다는 전제**다. 승인 범위에 Jira/Confluence 내용이 포함되는지는 별도로 확인하라.

---

## 9. 🔒 커밋 금지

이 레포는 **공개 포크**다 (`github.com/cruellaDev/atlassian-mcp-server`, PUBLIC).

```
절대 커밋 금지:
  PAT / 비밀번호 / 토큰          ← 유출 시 즉시 폐기·재발급
  사내 Jira/Confluence URL·도메인·IP
  프로젝트 키 / 스페이스 키 / 사번 / 실명 / 이메일
  커스텀 필드 ID
  DC 버전
```

커밋 전 확인:
```bash
git diff --cached | grep -iE "PAT|token|password|jira\.|confluence\.|customfield_"
```
걸리는 게 있으면 커밋하지 말고 물어라.

**이 문서에 회사 정보가 하나도 없는 건 의도된 설계다.** 실제 값은 업무망에서 프롬프트로 주고받는다.

---

## 다음 단계

설치가 끝났으면 **`DC-PORTING.md`** 로 가라. 공식 Atlassian 스킬 6개를 이 서버에 맞게 이식하는 방법이 있다.
