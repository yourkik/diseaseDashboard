import time
import unittest
import requests


class DiseaseDashboardQATest(unittest.TestCase):

    def setUp(self):
        """백엔드 서버 기본 주소 설정 (루프백 IP 사용)"""
        self.base_url = "http://127.0.0.1:8000"

    def test_disease_contents_integrity(self):
        """1. 질병 콘텐츠(뉴스) API의 응답 및 데이터 무결성 검증"""
        # Swagger 명세에 등록된 진짜 뉴스/콘텐츠 엔드포인트로 변경
        target_url = f"{self.base_url}/api/data/contents?disease=코로나"

        try:
            start_time = time.time()
            response = requests.get(target_url, timeout=15)
            end_time = time.time()
            latency = end_time - start_time

            # 404 에러가 나지 않고 정상 응답(200)을 받는지 검증
            self.assertEqual(
                response.status_code,
                200,
                f"🚨 API 경로 오류 또는 서버 에러 (HTTP 상태 코드: {response.status_code})",
            )

            # 응답 데이터가 정상적인 구조인지 체크
            contents_data = response.json()
            self.assertIsNotNone(
                contents_data, "🚨 콘텐츠 API 응답 데이터가 빈 값(None)입니다."
            )

            print(f"\n 콘텐츠(뉴스) API 검증 완료 (응답 속도: {latency:.2f}초)")

        except requests.exceptions.ConnectionError:
            self.fail("🚨 백엔드 서버가 꺼져 있습니다. uvicorn 상태를 확인하세요.")

    def test_map_disease_spread_integrity(self):
        """2. 질병 확산 지도 API의 연동 및 데이터 포맷 무결성 검증"""
        
        target_url = f"{self.base_url}/api/map/disease-spread?disease=코로나"

        try:
            response = requests.get(target_url, timeout=15)
            self.assertEqual(
                response.status_code,
                200,
                f"🚨 지도 API 경로 오류 (HTTP 상태 코드: {response.status_code})",
            )

            map_data = response.json()
            self.assertIsNotNone(map_data, "🚨 지도 통계 데이터셋이 비어 있습니다.")

            print("질병 확산 지도 API 검증 및 데이터 무결성 확인 완료")

        except requests.exceptions.ConnectionError:
            self.fail("🚨 백엔드 서버 연결 실패")


if __name__ == "__main__":
    unittest.main()