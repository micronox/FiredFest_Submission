"use client";

import { useState } from "react";
import Link from "next/link";
import type { TestSummary } from "@/lib/types";
import BrandLogo from "@/components/BrandLogo";

export default function Dashboard({ tests }: { tests: TestSummary[] }) {
  const [availableTests, setAvailableTests] = useState(tests);
  const [selectedId, setSelectedId] = useState<number | null>(tests[0]?.id ?? null);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");

  async function generateTest() {
    setGenerating(true);
    setError("");
    try {
      const response = await fetch("/api/tests", { method: "POST" });
      const body = await response.json();
      if (!response.ok) throw new Error(body.error ?? "Could not generate test.");
      const generated = body as TestSummary;
      setAvailableTests((current) => [...current, generated]);
      setSelectedId(generated.id);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not generate test.");
    } finally {
      setGenerating(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col gap-6 px-6 py-12">
      <header>
        <BrandLogo priority />
        <h1 className="mt-5 text-3xl font-bold tracking-tight">QuizCat</h1>
        <p className="mt-1 text-sm text-zinc-500">
          Timed, CCAT-style multiple-choice practice tests.
        </p>
      </header>

      <section className="rounded-lg border border-zinc-200 dark:border-zinc-800">
        <h2 className="border-b border-zinc-200 px-4 py-2 text-sm font-semibold uppercase tracking-wide text-zinc-500 dark:border-zinc-800">
          Available Exams
        </h2>
        {availableTests.length === 0 ? (
          <p className="px-4 py-6 text-sm text-zinc-500">
            No exams found. Run the seed script to load the question bank.
          </p>
        ) : (
          <ul className="divide-y divide-zinc-200 dark:divide-zinc-800">
            {availableTests.map((test) => {
              const minutes = Math.floor(test.timeLimitSeconds / 60);
              const isSelected = test.id === selectedId;
              return (
                <li key={test.id}>
                  <button
                    type="button"
                    onClick={() => setSelectedId(test.id)}
                    className={`flex w-full items-center justify-between px-4 py-3 text-left transition-colors ${
                      isSelected
                        ? "bg-emerald-50 dark:bg-emerald-950/40"
                        : "hover:bg-zinc-50 dark:hover:bg-zinc-900"
                    }`}
                  >
                    <span className="font-medium">{test.title}</span>
                    <span className="text-sm text-zinc-500">
                      {test.questionCount} questions / {minutes} min
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </section>

      {error && (
        <p className="rounded-md bg-red-50 p-3 text-sm text-red-800 dark:bg-red-950/40 dark:text-red-200">
          {error}
        </p>
      )}

      <div className="flex gap-3">
        <Link
          href="/question-lab"
          className="rounded-md border border-zinc-300 px-4 py-2 text-sm font-medium hover:bg-zinc-50 dark:border-zinc-700 dark:hover:bg-zinc-900"
        >
          Question Lab
        </Link>
        <Link
          href="/stats"
          className="rounded-md border border-zinc-300 px-4 py-2 text-sm font-medium hover:bg-zinc-50 dark:border-zinc-700 dark:hover:bg-zinc-900"
        >
          View Stats
        </Link>
        <button
          type="button"
          disabled={generating}
          onClick={generateTest}
          className="rounded-md bg-amber-500 px-4 py-2 text-sm font-medium text-zinc-950 hover:bg-amber-400 disabled:cursor-wait disabled:bg-zinc-300 disabled:text-zinc-500"
        >
          {generating ? "Generating..." : "Generate Test"}
        </button>
        {selectedId !== null ? (
          <Link
            href={`/quiz/${selectedId}`}
            className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500"
          >
            Start Quiz
          </Link>
        ) : (
          <span className="rounded-md bg-zinc-300 px-4 py-2 text-sm font-medium text-zinc-500">
            Start Quiz
          </span>
        )}
      </div>
    </main>
  );
}
