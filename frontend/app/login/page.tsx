"use client";

import { useState } from "react";

import { useAuth } from "../../hooks/useAuth";
import { API_BASE_URL } from "../../lib/api";

export default function LoginPage() {
  const { setToken } = useAuth();
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      body: new URLSearchParams({
        username: formData.get("email") as string,
        password: formData.get("password") as string
      })
    });
    if (!response.ok) {
      setError("Invalid credentials");
      return;
    }
    const data = await response.json();
    setToken(data.access_token);
  };

  return (
    <div className="mx-auto max-w-md rounded-lg bg-white p-6 shadow-sm">
      <h1 className="text-2xl font-semibold">Log in</h1>
      <form className="mt-4 space-y-4" onSubmit={handleSubmit}>
        <div>
          <label className="block text-sm font-medium text-slate-700" htmlFor="email">
            Email
          </label>
          <input name="email" id="email" type="email" className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2" />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700" htmlFor="password">
            Password
          </label>
          <input
            name="password"
            id="password"
            type="password"
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
          />
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button type="submit" className="w-full rounded-md bg-indigo-600 px-4 py-2 text-white">
          Sign in
        </button>
      </form>
    </div>
  );
}
