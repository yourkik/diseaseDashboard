import { Inter, Outfit } from "next/font/google";
import "./globals.css";
import Link from 'next/link';
// import Script from 'next/script';

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const outfit = Outfit({
  variable: "--font-outfit",
  subsets: ["latin"],
});

export const metadata = {
  title: "질병 대시보드 - Sentinel",
  description: "실시간 질병 확산 및 위험도 모니터링 시스템",
};

export default function RootLayout({ children }) {
  return (
    <html lang="ko" className={`${inter.variable} ${outfit.variable}`}>
      <head>
         
      </head>
      <body>
        <nav className="navbar">
          <div>
            <Link href="/" style={{textDecoration: 'none'}}>
              <h2 className="title-gradient" style={{ margin: 0 }}>Sentinel Dashboard</h2>
            </Link>
          </div>
          <div className="nav-links">
            <Link href="/">대시보드</Link>
            <Link href="/analytics">심층 통계(Test)</Link>
            <Link href="/admin">관리자 설정</Link>
          </div>
        </nav>
        {children}
      </body>
    </html>
  );
}