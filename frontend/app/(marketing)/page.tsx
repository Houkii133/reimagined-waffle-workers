import Link from "next/link";

const heroFeatures = [
  "AI-personalized recommendations",
  "Structured employer job management",
  "Explainable matches and gap analysis",
  "Admin telemetry insights"
];

export default function HomePage() {
  return (
    <div className="space-y-10">
      <section className="rounded-xl bg-white p-10 shadow-sm">
        <h1 className="text-4xl font-bold">Find a role where you&apos;ll thrive.</h1>
        <p className="mt-4 text-lg text-slate-600">
          Reimagined Jobs pairs a rich job marketplace with an explainable AI matching engine. Build your profile, explore transparent recommendations, and close gaps faster.
        </p>
        <div className="mt-6 flex gap-4">
          <Link href="/register" className="rounded-md bg-indigo-600 px-5 py-2 text-white">
            Get started
          </Link>
          <Link href="/jobs" className="rounded-md border border-indigo-200 px-5 py-2 text-indigo-700">
            Browse jobs
          </Link>
        </div>
      </section>
      <section className="grid gap-6 md:grid-cols-2">
        {heroFeatures.map((feature) => (
          <div key={feature} className="rounded-lg border border-slate-200 bg-white p-6">
            <h3 className="text-lg font-semibold">{feature}</h3>
            <p className="mt-2 text-sm text-slate-600">
              Our AI engine continuously learns from feedback and employer updates to surface the best matches.
            </p>
          </div>
        ))}
      </section>
    </div>
  );
}
