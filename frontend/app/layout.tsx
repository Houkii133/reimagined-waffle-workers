"use client";

import "./globals.css";
import { ReactNode, useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { AuthProvider } from "../hooks/useAuth";

export default function RootLayout({ children }: { children: ReactNode }) {
  const [client] = useState(() => new QueryClient());
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50">
        <AuthProvider>
          <QueryClientProvider client={client}>
            <div className="mx-auto max-w-6xl px-6 py-8">
              <header className="mb-8 flex items-center justify-between">
                <a className="text-2xl font-semibold" href="/">
                  Reimagined Jobs
                </a>
                <nav className="space-x-4 text-sm font-medium">
                  <a href="/jobs">Jobs</a>
                  <a href="/recommended">Recommended</a>
                  <a href="/profile">Profile</a>
                  <a href="/employer/jobs">Employer</a>
                  <a href="/admin">Admin</a>
                </nav>
              </header>
              <main>{children}</main>
            </div>
            <ReactQueryDevtools initialIsOpen={false} />
          </QueryClientProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
