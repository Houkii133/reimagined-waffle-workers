"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "../../hooks/useAuth";
import { apiFetch } from "../../lib/api";
import { useMemo, useState } from "react";

interface Recommendation {
  job_id: number;
  score: number;
  rationale: string[];
  qualification_gaps: string[];
  fit_dimensions: Record<string, number>;
}

interface RecommendationResponse {
  items: Recommendation[];
}

export default function RecommendedPage() {
  const { token } = useAuth();
  const [sortKey, setSortKey] = useState<"score" | "job_id">("score");
  const queryClient = useQueryClient();
  const query = useQuery<RecommendationResponse>(
    ["recommendations", sortKey],
    () =>
      apiFetch<RecommendationResponse>(`/recommendations`, {
        headers: {
          Authorization: token ? `Bearer ${token}` : ""
        }
      }),
    { enabled: Boolean(token) }
  );

  const feedbackMutation = useMutation(
    (payload: { job_id: number; event_type: string }) =>
      apiFetch(`/recommendations/feedback`, {
        method: "POST",
        headers: {
          Authorization: token ? `Bearer ${token}` : ""
        },
        body: JSON.stringify(payload)
      }),
    {
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ["recommendations"] });
      }
    }
  );

  const sortedItems = useMemo(() => {
    const items = query.data?.items ?? [];
    if (sortKey === "score") {
      return [...items].sort((a, b) => b.score - a.score);
    }
    return items;
  }, [query.data, sortKey]);

  if (!token) {
    return <p className="text-slate-600">Login to view your personalized recommendations.</p>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold">Recommended for you</h1>
          <p className="text-slate-600">Ranked by skill fit and feedback from your interactions.</p>
        </div>
        <select
          className="rounded-md border border-slate-300 px-3 py-2"
          value={sortKey}
          onChange={(event) => setSortKey(event.target.value as any)}
        >
          <option value="score">Sort by score</option>
          <option value="job_id">Sort by recency</option>
        </select>
      </div>
      <div className="space-y-4">
        {sortedItems.map((rec) => (
          <article key={rec.job_id} className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
            <header className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Match score</p>
                <p className="text-2xl font-semibold">{Math.round(rec.score * 100)}%</p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => feedbackMutation.mutate({ job_id: rec.job_id, event_type: "save" })}
                  className="rounded-md bg-indigo-600 px-4 py-2 text-sm text-white"
                >
                  Save
                </button>
                <button
                  onClick={() => feedbackMutation.mutate({ job_id: rec.job_id, event_type: "dismiss" })}
                  className="rounded-md border border-slate-200 px-4 py-2 text-sm"
                >
                  Dismiss
                </button>
              </div>
            </header>
            <section className="mt-4 grid gap-4 md:grid-cols-2">
              <div>
                <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Rationale</h3>
                <ul className="mt-2 space-y-1 text-sm text-slate-600">
                  {rec.rationale.map((item) => (
                    <li key={item}>• {item}</li>
                  ))}
                </ul>
              </div>
              <div>
                <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Qualification gaps</h3>
                <ul className="mt-2 space-y-1 text-sm text-slate-600">
                  {rec.qualification_gaps.map((item) => (
                    <li key={item}>• {item}</li>
                  ))}
                </ul>
              </div>
            </section>
          </article>
        ))}
        {query.isLoading && <p>Loading recommendations…</p>}
      </div>
    </div>
  );
}
