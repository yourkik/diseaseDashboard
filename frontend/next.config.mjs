/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",
  // Azure Static Web Apps에서는 이미지를 위한 서버 최적화가 지원되지 않으므로 unoptimized 옵션 활성화
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
