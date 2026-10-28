import Link from "next/link";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata = {
  title: "Undoom",
  description: "Replay a failed agent run and see whether the fix held.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="shell">
          <header className="top">
            <Link className="mark" href="/">
              UNDO<span>OM</span>
            </Link>
            <nav className="nav">
              <Link href="/">Runs</Link>
              <Link href="/suite">Suite</Link>
            </nav>
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}
