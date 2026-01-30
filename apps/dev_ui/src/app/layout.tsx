import "./globals.css";
import Link from "next/link";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body className="min-h-screen">
        <header className="border-b">
          <div className="mx-auto max-w-6xl px-4 py-4 flex items-center justify-between">
            <div className="font-black text-xl">bandabi dev_ui</div>
            <nav className="flex gap-4 text-sm">
              <Link href="/experiments" className="hover:underline">Experiments</Link>
              <Link href="/insights" className="hover:underline">Insights</Link>
            </nav>
          </div>
        </header>
        <main className="mx-auto max-w-6xl px-4 py-6">{children}</main>
      </body>
    </html>
  );
}
