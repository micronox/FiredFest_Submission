"use client";

import { useEffect, useState } from "react";
import type { HarnessResult } from "@/lib/types";

interface LabStatus {
  configured: boolean;
  enabled: boolean;
  accessProtected: boolean;
  model: string;
  questionTypes: string[];
}

export default function QuestionLab() {
  const [status, setStatus] = useState<LabStatus | null>(null);
  const [questionType, setQuestionType] = useState("");
  const [result, setResult] = useState<HarnessResult | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch("/api/question-lab")
      .then((response) => response.json())
      .then((data: LabStatus) => {
        setStatus(data);
        setQuestionType(data.questionTypes[0] ?? "");
      })
      .catch(() => setError("Could not load Question Lab configuration."));
  }, []);

  async function generate() {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const response = await fetch("/api/question-lab", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ questionType, exampleCount: 5 }),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.error ?? "Generation failed.");
      setResult(body as HarnessResult);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Generation failed.");
    } finally {
      setLoading(false);
    }
  }

  if (!status) {
    return <p className="text-sm text-zinc-500">Loading lab configuration...</p>;
  }

  return (
    <>
      <section className="rounded-lg border border-zinc-200 p-5 dark:border-zinc-800">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="font-semibold">Governed generation</p>
            <p className="text-sm text-zinc-500">Model: {status.model}</p>
          </div>
          <span
            className={`rounded-full px-3 py-1 text-xs font-semibold ${
              status.enabled
                ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300"
                : "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300"
            }`}
          >
            {status.enabled ? "Ready" : "Locked"}
          </span>
        </div>

        {!status.enabled && (
          <p className="mt-4 rounded-md bg-amber-50 p-3 text-sm text-amber-900 dark:bg-amber-950/40 dark:text-amber-200">
            Generation is locked. Configure <code>OPENAI_API_KEY</code> and set{" "}
            <code>QUESTION_LAB_ENABLED=true</code> on the server.
          </p>
        )}

        {status.enabled && status.accessProtected && (
          <p className="mt-4 text-sm text-zinc-500">
            Access is managed automatically by a secure server-issued session.
          </p>
        )}

        <label className="mt-5 block text-sm font-medium" htmlFor="question-type">
          Question type
        </label>
        <div className="mt-2 flex flex-col gap-3 sm:flex-row">
          <select
            id="question-type"
            value={questionType}
            onChange={(event) => setQuestionType(event.target.value)}
            className="min-w-0 flex-1 rounded-md border border-zinc-300 bg-transparent px-3 py-2 text-sm dark:border-zinc-700"
          >
            {status.questionTypes.map((type) => (
              <option key={type}>{type}</option>
            ))}
          </select>
          <button
            type="button"
            disabled={
              !status.enabled ||
              !questionType ||
              loading
            }
            onClick={generate}
            className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:cursor-not-allowed disabled:bg-zinc-300 disabled:text-zinc-500"
          >
            {loading ? "Generating and checking..." : "Generate candidate"}
          </button>
        </div>
      </section>

      {error && (
        <p className="rounded-md bg-red-50 p-3 text-sm text-red-800 dark:bg-red-950/40 dark:text-red-200">
          {error}
        </p>
      )}

      {result && (
        <section className="space-y-5 rounded-lg border border-zinc-200 p-5 dark:border-zinc-800">
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-xl font-bold">Review package</h2>
            <span className={result.accepted ? "text-emerald-600" : "text-red-600"}>
              {result.accepted ? "Accepted by harness" : "Rejected by harness"}
            </span>
          </div>
          <div>
            {result.candidate.stimulus && (
              <p className="mb-2 whitespace-pre-wrap text-sm text-zinc-600 dark:text-zinc-300">
                {result.candidate.stimulus}
              </p>
            )}
            <p className="font-semibold">{result.candidate.prompt}</p>
            <ol className="mt-3 space-y-1 text-sm">
              {result.candidate.choices.map((choice) => (
                <li key={choice.label}>
                  <span className="font-semibold">{choice.label}.</span> {choice.text}
                </li>
              ))}
            </ol>
            <p className="mt-4 text-sm">
              <span className="font-semibold">Answer:</span>{" "}
              {result.candidate.correctChoiceLabel}
            </p>
            <p className="mt-2 text-sm">
              <span className="font-semibold">Explanation:</span>{" "}
              {result.candidate.explanation}
            </p>
          </div>
          <div>
            <h3 className="font-semibold">Final checkpoints</h3>
            <ul className="mt-2 space-y-2">
              {result.checkpoints.map((checkpoint) => (
                <li
                  key={checkpoint.name}
                  className="rounded-md bg-zinc-50 px-3 py-2 text-sm dark:bg-zinc-900"
                >
                  <span
                    className={
                      checkpoint.passed ? "text-emerald-600" : "text-red-600"
                    }
                  >
                    {checkpoint.passed ? "PASS" : "FAIL"}
                  </span>{" "}
                  <span className="font-semibold">{checkpoint.name}</span>:{" "}
                  {checkpoint.detail}
                </li>
              ))}
            </ul>
            <p className="mt-3 text-xs text-zinc-500">
              {result.attempts.length} generation attempt(s). Candidates are review-only
              and are not written to the production question bank.
            </p>
          </div>
        </section>
      )}
    </>
  );
}
