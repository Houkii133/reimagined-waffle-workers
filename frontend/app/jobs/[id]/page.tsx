"use client";

import { useQuery, useMutation } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { useState } from "react";

import { useAuth } from "../../../hooks/useAuth";
import { apiFetch } from "../../../lib/api";

interface JobDetail {
  id: number;
  title: string;
  description: string;
  responsibilities: string[];
  requirements: string[];
  culture_signals: string[];
  growth_signals: string[];
  skills: string[];
  location: string;
  modality: string;
}

interface WhyNotResponse {
  job_id: number;
  missing_skills: string[];
  message: string;
}

export default function JobDetailPage() {
  const params = useParams();
  const id = params?.id as string;
  const { token } = useAuth();
  const [whyNot, setWhyNot] = useState<WhyNotResponse | null>(null);

  const jobQuery = useQuery<JobDetail>(["job", id], () => apiFetch<JobDetail>(`/jobs/${id}`));
  const whyNotMutation = useMutation(() =>
    apiFetch<WhyNotResponse>(`/recommendations/why_not/${id}`, {
      headers: {
        Authorization: token ? `Bearer ${token}` : ""
      }
    })
  );

  const handleWhyNot = async () => {
    if (!token) return;
    const data = await whyNotMutation.mutateAsync();
    setWhyNot(data);
  };

  if (jobQuery.isLoading) {
    return <p>Loading job…</p>;
  }

  const job = jobQuery.data;
  if (!job) {
    return <p>Job not found.</p>;
  }

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold">{job.title}</h1>
          <p className="text-slate-500">{job.location} · {job.modality}</p>
        </div>
        {token && (
          <button
            onClick={handleWhyNot}
            className="rounded-md border border-indigo-200 px-4 py-2 text-sm text-indigo-700"
          >
            Why not me?
          </button>
        )}
      </header>
      <section className="rounded-lg bg-white p-6 shadow-sm">
        <h2 className="text-xl font-semibold">About the role</h2>
        <p className="mt-3 whitespace-pre-wrap text-sm text-slate-700">{job.description}</p>
      </section>
      <section className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg bg-white p-5 shadow-sm">
          <h3 className="text-lg font-semibold">Responsibilities</h3>
          <ul className="mt-2 space-y-2 text-sm text-slate-600">
            {job.responsibilities.map((item) => (
              <li key={item}>• {item}</li>
            ))}
          </ul>
        </div>
        <div className="rounded-lg bg-white p-5 shadow-sm">
          <h3 className="text-lg font-semibold">Requirements</h3>
          <ul className="mt-2 space-y-2 text-sm text-slate-600">
            {job.requirements.map((item) => (
              <li key={item}>• {item}</li>
            ))}
          </ul>
        </div>
      </section>
      {whyNot && (
        <section className="rounded-lg border border-amber-200 bg-amber-50 p-5">
          <h3 className="text-lg font-semibold text-amber-900">Gaps identified</h3>
          <p className="text-sm text-amber-900">{whyNot.message}</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {whyNot.missing_skills.map((skill) => (
              <span key={skill} className="rounded-full bg-amber-200 px-3 py-1 text-xs text-amber-900">
                {skill}
              </span>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
