"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";

import { apiFetch } from "../../lib/api";

interface Job {
  id: number;
  title: string;
  description: string;
  location: string;
  modality: string;
  industry?: string;
  salary_min?: number;
  salary_max?: number;
  skills: string[];
}

interface JobResponse {
  total: number;
  items: Job[];
}

export default function JobIndexPage() {
  const [skill, setSkill] = useState("");
  const query = useQuery<JobResponse>(["jobs", skill], () => apiFetch<JobResponse>(`/jobs?skill=${skill}`));

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-semibold">Discover roles</h1>
          <p className="text-slate-600">Search and filter across open opportunities.</p>
        </div>
        <input
          value={skill}
          onChange={(event) => setSkill(event.target.value)}
          placeholder="Filter by skill"
          className="rounded-md border border-slate-300 px-3 py-2"
        />
      </div>
      <div className="grid gap-4">
        {query.data?.items.map((job) => (
          <article key={job.id} className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold">
                  <Link href={`/jobs/${job.id}`}>{job.title}</Link>
                </h2>
                <p className="text-sm text-slate-500">{job.location} · {job.modality}</p>
              </div>
              <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-700">
                {job.industry ?? "General"}
              </span>
            </div>
            <p className="mt-4 text-sm text-slate-600 line-clamp-3">{job.description}</p>
            <div className="mt-4 flex flex-wrap gap-2">
              {job.skills.slice(0, 6).map((skill) => (
                <span key={skill} className="rounded-full bg-slate-100 px-2 py-1 text-xs text-slate-700">
                  {skill}
                </span>
              ))}
            </div>
          </article>
        ))}
        {query.isLoading && <p>Loading jobs…</p>}
      </div>
    </div>
  );
}
