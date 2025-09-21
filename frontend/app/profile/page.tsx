"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { FormEvent, useState } from "react";

import { useAuth } from "../../hooks/useAuth";
import { apiFetch } from "../../lib/api";

interface UserProfile {
  email: string;
  full_name?: string;
  profile?: {
    bio?: string;
    skills: string[];
    soft_skills: string[];
    years_experience?: number;
    desired_roles: string[];
    desired_industries: string[];
    salary_currency: string;
    salary_min?: number;
    salary_max?: number;
    location_preferences: string[];
    work_authorization?: string;
    career_goals?: string;
    resume_text?: string;
  };
}

export default function ProfilePage() {
  const { token } = useAuth();
  const query = useQuery<UserProfile>(
    ["me"],
    () =>
      apiFetch<UserProfile>(`/users/me`, {
        headers: {
          Authorization: token ? `Bearer ${token}` : ""
        }
      }),
    { enabled: Boolean(token) }
  );

  const mutation = useMutation((values: Partial<UserProfile>) =>
    apiFetch<UserProfile>(`/users/me`, {
      method: "PUT",
      headers: {
        Authorization: token ? `Bearer ${token}` : ""
      },
      body: JSON.stringify(values)
    })
  );

  const [resumeText, setResumeText] = useState("");

  if (!token) {
    return <p className="text-slate-600">Login to complete your profile.</p>;
  }

  const profile = query.data?.profile;

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const skills = (formData.get("skills") as string).split(",").map((skill) => skill.trim()).filter(Boolean);
    mutation.mutate({
      full_name: formData.get("full_name") as string,
      skills,
      resume_text: resumeText
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold">Your profile</h1>
        <p className="text-slate-600">Share your skills, preferences, and goals to personalize matching.</p>
      </div>
      <form className="space-y-4 rounded-lg bg-white p-6 shadow-sm" onSubmit={handleSubmit}>
        <div>
          <label className="block text-sm font-medium text-slate-700" htmlFor="full_name">
            Full name
          </label>
          <input
            name="full_name"
            id="full_name"
            defaultValue={query.data?.full_name ?? ""}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700" htmlFor="skills">
            Skills (comma separated)
          </label>
          <input
            name="skills"
            id="skills"
            defaultValue={profile?.skills?.join(", ") ?? ""}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700">Resume (mock parser)</label>
          <textarea
            value={resumeText}
            onChange={(event) => setResumeText(event.target.value)}
            placeholder="Paste your resume text here to auto-extract skills."
            className="mt-1 h-40 w-full rounded-md border border-slate-300 px-3 py-2"
          />
        </div>
        <button
          type="submit"
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white"
        >
          Save profile
        </button>
      </form>
    </div>
  );
}
