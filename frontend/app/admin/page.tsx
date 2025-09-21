"use client";

import { useQuery } from "@tanstack/react-query";

import { useAuth } from "../../hooks/useAuth";
import { apiFetch } from "../../lib/api";

interface TelemetryResponse {
  jobs_indexed: number;
  feedback_events: number;
}

export default function AdminPage() {
  const { token } = useAuth();
  const query = useQuery<TelemetryResponse>(
    ["telemetry"],
    () =>
      apiFetch<TelemetryResponse>(`/admin/telemetry`, {
        headers: {
          Authorization: token ? `Bearer ${token}` : ""
        }
      }),
    { enabled: Boolean(token) }
  );

  if (!token) {
    return <p className="text-slate-600">Admin authentication required.</p>;
  }

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <div className="rounded-lg bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold">Jobs indexed</h2>
        <p className="mt-2 text-3xl font-semibold">{query.data?.jobs_indexed ?? 0}</p>
      </div>
      <div className="rounded-lg bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold">Feedback events</h2>
        <p className="mt-2 text-3xl font-semibold">{query.data?.feedback_events ?? 0}</p>
      </div>
    </div>
  );
}
