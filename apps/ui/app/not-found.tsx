import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Page not found · Undoom",
  description: "That page is not in this library.",
};

export default function NotFound() {
  return (
    <main>
      <h1>Page not found</h1>
      <p className="lede">That page is not in this library.</p>
      <p>
        <Link href="/">Back to runs</Link>
      </p>
    </main>
  );
}
