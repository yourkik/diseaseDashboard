# Azure Grounding with Bing Search 설정 가이드

본 가이드는 감염병 대시보드 백엔드에서 최신 방식의 실시간 뉴스 RAG 처리를 위해 필요한 Azure 리소스를 생성하고 연결하는 방법을 안내합니다.

## 1. 리소스 생성

1. **Azure Portal (portal.azure.com)** 에 로그인합니다.
2. 상단 검색창에 **"Grounding with Bing Search"** 를 검색하여 선택합니다.
3. **[만들기]** 버튼을 클릭하고 다음 정보를 입력합니다:
   - 구독 및 리소스 그룹 선택 (예: `disease-dashboard-rg`)
   - 인스턴스 이름: `disease-bing-grounding` (예시)
   - 가격 책정 계층: 기본값 적용 (약 1,000건당 $14)
4. 동일하게 **Azure OpenAI** 리소스도 하나 생성합니다. (이미 있다면 기존 것을 사용해도 됩니다.)
5. Azure OpenAI 리소스 내부에서 **GPT-4o** 또는 **GPT-4-turbo** 모델을 배포(Deploy)합니다. 이 때 설정한 '배포 이름(Deployment Name)'을 기억해 두세요.

## 2. 권한 연결 (매우 중요)

Azure OpenAI가 Grounding 리소스를 사용하여 스스로 웹 검색을 하려면 상호 권한 연결이 필요합니다.

1. 방금 만든 **Azure OpenAI** 리소스 페이지로 이동합니다.
2. 좌측 메뉴에서 **[ID] (Identity)** 를 클릭하고 시스템 할당(System assigned) 관리 ID를 **'켜기(On)'**로 설정 후 저장합니다.
3. 이제 **Grounding with Bing Search** 리소스 페이지로 이동합니다.
4. 좌측 메뉴에서 **[액세스 제어 (IAM)]** 를 클릭합니다.
5. **[추가] -> [역할 할당 추가]** 를 클릭합니다.
6. 역할 탭: **"Cognitive Services Bing Grounding Search User"** (또는 빙 검색 사용자 관련 권한) 선택
7. 멤버 탭: 액세스 할당 대상 ➔ **관리 ID (Managed Identity)** 선택
8. 멤버 선택 ➔ 아까 만든 Azure OpenAI 인스턴스를 찾아 선택 후 최종 저장합니다.

## 3. API Key 확보 및 .env 적용

1. Azure OpenAI 리소스의 **[키 및 엔드포인트]** 메뉴에서 `KEY 1`과 `엔드포인트` 값을 복사합니다.
2. 프로젝트의 `backend/.env` 파일을 열고 다음과 같이 값을 붙여넣어 줍니다.

```env
AZURE_OPENAI_KEY=복사한_키_값
AZURE_OPENAI_ENDPOINT=https://당신의리소스.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
BING_GROUNDING_RESOURCE_ID=/subscriptions/사용자아이디/resourceGroups/리소스그룹명/providers/Microsoft.Bing/groundingWithBingSearch/설정한이름
```
> [!NOTE]
> `BING_GROUNDING_RESOURCE_ID`는 Grounding 리소스의 **[개요] -> [JSON 뷰]** 또는 **[속성(Properties)]** 탭에서 찾을 수 있는 매우 긴 Resource ID 문자열입니다.

위 클라우드 세팅이 완료되면 터미널/로컬 환경에서 바로 실제 AI 연동 테스트가 가능합니다!
