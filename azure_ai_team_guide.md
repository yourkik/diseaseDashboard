# 🚀 Azure AI Foundry (v2) 연동 팀 공유 가이드

본 문서는 우리 팀(`3dt-final-team5`)이 질병 대시보드 프로젝트에서 **Azure AI Foundry (Bing Search Grounding)**를 활용하기 위해 겪은 시행착오와 가장 빠르고 확실한 세팅 방법을 정리한 가이드입니다.

---

## ⚠️ 1. 가장 흔하게 겪는 3대 주의사항 (필독)

> [!WARNING]
> **1. 구버전 SDK 절대 사용 금지**
> 인터넷에 있는 과거 Azure AI 관련 예제 코드는 대부분 작동하지 않습니다. 우리는 반드시 최신 릴리스인 `azure-ai-projects==2.1.0`을 사용해야 합니다.

> [!CAUTION]
> **2. 권한(RBAC) 부여 필수**
> Azure 포털에서 내가 리소스를 만들었다고 해도 코드로 접근하려면 별도의 권한이 필요합니다. Azure AI Foundry 화면에서 본인 계정에 반드시 **`Azure AI 프로젝트 관리자`** 또는 **`Azure AI 개발자`** 역할을 할당해야 합니다. (일반 `Azure AI 사용자`는 읽기 권한이 없어 에러가 발생합니다.)

> [!IMPORTANT]
> **3. Connection String 폐기**
> 더 이상 복잡한 Connection String을 사용하지 않습니다. 최신 SDK는 직관적인 `PROJECT_ENDPOINT` URL만을 사용합니다.

---

## 🛠 2. 로컬 개발 환경 세팅 방법

### Step 1. Azure CLI 설치 및 로그인
로컬에서 보안 토큰을 발급받기 위해 Azure CLI가 필수입니다.
1. [Azure CLI 다운로드 및 설치](https://learn.microsoft.com/ko-kr/cli/azure/install-azure-cli)
2. 터미널(명령 프롬프트/PowerShell)을 열고 아래 명령어 실행:
   ```bash
   az login
   ```
3. 웹 브라우저가 열리면 Azure 계정으로 로그인합니다.

### Step 2. 라이브러리 설치
백엔드 폴더(`backend`)로 이동하여 최신 SDK가 명시된 `requirements.txt`를 설치합니다.
```bash
pip install -r requirements.txt
# azure-ai-projects==2.1.0 과 azure-identity 가 설치됩니다.
```

---

## 🔐 3. `.env` 파일 설정 가이드

백엔드 폴더 최상단에 `.env` 파일을 만들고 아래 3가지 값을 채워 넣습니다.

```env
# 1. 프로젝트 엔드포인트
# Azure AI Foundry -> 개요 탭 -> 프로젝트 세부 정보 -> 'AI Foundry API' URL (https://...services.ai.azure.com/api/projects/...)
PROJECT_ENDPOINT=https://diseasedashopenai.services.ai.azure.com/api/projects/DiseaseDashboard-Project

# 2. Azure OpenAI 모델 배포 이름 (보통 gpt-4o)
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o

# 3. Bing Search Grounding 연결 이름
# 관리 센터 -> 연결된 리소스(Connected resources)에 등록된 빙 검색 이름
BING_CONNECTION_NAME=GroundingBingSearch

# 4. 질병관리청 API KEY(KDCA_TOKEN)
# KDCA의 경우 기본 url + 개인 token + 질병 ID의 형태로 데이터 접근 방식 사용
이를 위해 URL을 만드는 기능은 ingestion에 포함되어 있음 -> API 추가 or 삭제 시 ID 부분 수정 필요
```

---

## 💻 4. Python 연동 핵심 코드 구조

최신 v2.1.0 SDK를 활용하면 API Key 노출 없이 `DefaultAzureCredential`을 통해 안전하게 통신할 수 있습니다.

```python
import os
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import BingGroundingTool

# 1. 클라이언트 초기화 (엔드포인트 방식)
project_client = AIProjectClient(
    endpoint=os.getenv("PROJECT_ENDPOINT"),
    credential=DefaultAzureCredential()
)

# 2. 빙 검색 도구 연결
bing_connection = project_client.connections.get(os.getenv("BING_CONNECTION_NAME"))
bing_tool = BingGroundingTool(connection_id=bing_connection.id)

# 3. 에이전트(Agent) 생성
agent = project_client.agents.create_agent(
    model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    name="disease-analyzer",
    instructions="당신은 감염병 분석 AI입니다. 최신 뉴스를 검색하고 요약하세요.",
    tools=[bing_tool]
)
```

## 🎉 5. 세팅 후 테스트 방법

위 모든 과정을 마친 후, 백엔드 폴더에서 다음 명령어를 실행하여 200 OK 응답과 함께 AI 요약 리포트가 터미널에 뜨면 성공입니다!

```powershell
$env:PYTHONIOENCODING="utf-8"; python test_apis.py
```
