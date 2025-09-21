"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent } from "react";

import { useAuth } from "../../../hooks/useAuth";
import { apiFetch } from "../../../lib/api";

interface Job {
  id: number;
  title: string;
  description: string;
  location: string;
  modality: string;
  skills: string[];
}

interface JobResponse {
  total: number;
  items: Job[];
}

export default function EmployerJobsPage() {
  const { token } = useAuth();
  const queryClient = useQueryClient();
  const jobsQuery = useQuery<JobResponse>(
    ["employer-jobs"],
    () =>
      apiFetch<JobResponse>(`/jobs?limit=50`, {
        headers: {
          Authorization: token ? `Bearer ${token}` : ""
        }
      }),
    { enabled: Boolean(token) }
  );

  const createMutation = useMutation(
    (values: Record<string, any>) =>
      apiFetch(`/jobs/employer/jobs`, {
        method: "POST",
        headers: {
          Authorization: token ? `Bearer ${token}` : ""
        },
        body: JSON.stringify(values)
      }),
    {
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ["employer-jobs"] });
      }
    }
  );

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    createMutation.mutate({
      title: formData.get("title"),
      description: formData.get("description"),
      location: formData.get("location"),
      modality: formData.get("modality"),
      skills: (formData.get("skills") as string).split(",").map((skill) => skill.trim()),
      responsibilities: ["Deliver value"],
      requirements: ["Great communication"],
      culture_signals: ["Inclusive"],
      growth_signals: ["Scaling"],
    });
  };

  if (!token) {
    return <p className="text-slate-600">Employer login required to manage jobs.</p>;
  }

  return (
    <div className="space-y-6">
      <section className="rounded-lg bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold">Create job posting</h2>
        <form className="mt-4 grid gap-4 md:grid-cols-2" onSubmit={handleSubmit}>
          <input name="title" placeholder="Role title" className="rounded-md border border-slate-300 px-3 py-2" />
          <input name="location" placeholder="Location" className="rounded-md border border-slate-300 px-3 py-2" />
          <input name="modality" placeholder="Modality" className="rounded-md border border-slate-300 px-3 py-2" />
          <textarea
            name="description"
            placeholder="Describe the opportunity"
            className="col-span-2 rounded-md border border-slate-300 px-3 py-2"
          />
          <input
            name="skills"
            placeholder="Key skills"
            className="col-span-2 rounded-md border border-slate-300 px-3 py-2"
          />
          <button type="submit" className="col-span-2 rounded-md bg-indigo-600 px-4 py-2 text-white">
            Publish
          </button>
        </form>
      </section>
      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Recent postings</h2>
        {jobsQuery.data?.items.map((job) => (
          <article key={job.id} className="rounded-lg border border-slate-200 bg-white p-4">
            <h3 className="text-lg font-semibold">{job.title}</h3>
            <p className="text-sm text-slate-600">{job.location} · {job.modality}</p>
          </article>
        ))}
      </section>
    </div>
  );
}
