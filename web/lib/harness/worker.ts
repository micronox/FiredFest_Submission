import OpenAI from "openai";
import { zodTextFormat } from "openai/helpers/zod";
import { z } from "zod";
import type {
  CandidateQuestion,
  HarnessAttempt,
  HarnessCheckpoint,
  HarnessResult,
  Question,
} from "@/lib/types";
import { runCheckpoints } from "./checkpoints";

const candidateSchema = z.object({
  category: z.string(),
  questionType: z.string(),
  prompt: z.string(),
  stimulus: z.string(),
  choices: z
    .array(z.object({ label: z.string(), text: z.string() }))
    .length(4),
  correctChoiceLabel: z.string(),
  explanation: z.string(),
  verificationExpression: z.string(),
});

export const DEFAULT_MODEL = "gpt-4o-mini";
const MAX_REVISIONS = 1;

export function questionLabStatus() {
  const hasKey = Boolean(process.env.OPENAI_API_KEY);
  const enabled = process.env.QUESTION_LAB_ENABLED === "true";
  return {
    configured: hasKey,
    enabled: hasKey && enabled,
    accessProtected: Boolean(process.env.QUESTION_LAB_ACCESS_TOKEN),
    model: process.env.OPENAI_MODEL ?? DEFAULT_MODEL,
  };
}

export async function generateGovernedQuestion(
  questionType: string,
  examples: Question[]
): Promise<HarnessResult> {
  const status = questionLabStatus();
  if (!status.configured) throw new Error("OPENAI_API_KEY is not configured.");
  if (!status.enabled) throw new Error("QUESTION_LAB_ENABLED is not true.");

  const client = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
    timeout: 20_000,
    maxRetries: 0,
  });
  const attempts: HarnessAttempt[] = [];
  let feedback: HarnessCheckpoint[] = [];
  let previous: CandidateQuestion | null = null;

  for (let revision = 0; revision <= MAX_REVISIONS; revision += 1) {
    const response = await client.responses.parse({
      model: status.model,
      max_output_tokens: 1_200,
      input: [
        {
          role: "system",
          content:
            "You create original CCAT-style multiple-choice practice questions. " +
            "Return exactly four choices with unique A-D labels and one correct answer. " +
            "The explanation must explicitly include the full text of the correct choice. " +
            "For arithmetic questions, verificationExpression must be a safe arithmetic expression " +
            "using only numbers, parentheses, +, -, *, /, and ^ that evaluates to the numeric correct choice. " +
            "For non-arithmetic questions, verificationExpression must be an empty string. " +
            "Never copy or closely paraphrase examples.",
        },
        {
          role: "user",
          content: buildRequest(questionType, examples, previous, feedback),
        },
      ],
      text: { format: zodTextFormat(candidateSchema, "candidate_question") },
    });

    const candidate = response.output_parsed as CandidateQuestion | null;
    if (!candidate) throw new Error("The model did not return a candidate question.");
    const checkpoints = runCheckpoints(candidate, questionType, examples);
    attempts.push({ revision, candidate, checkpoints });
    if (checkpoints.every((checkpoint) => checkpoint.passed)) {
      return {
        accepted: true,
        model: status.model,
        attempts,
        candidate,
        checkpoints,
      };
    }
    previous = candidate;
    feedback = checkpoints.filter((checkpoint) => !checkpoint.passed);
  }

  const last = attempts[attempts.length - 1];
  return {
    accepted: false,
    model: status.model,
    attempts,
    candidate: last.candidate,
    checkpoints: last.checkpoints,
  };
}

function buildRequest(
  questionType: string,
  examples: Question[],
  previous: CandidateQuestion | null,
  feedback: HarnessCheckpoint[]
): string {
  const exampleText = examples
    .map(
      (example, index) =>
        `Example ${index + 1}:\n${example.stimulus}\n${example.prompt}\n` +
        example.choices.map((choice) => `${choice.label}. ${choice.text}`).join("\n")
    )
    .join("\n\n");

  if (!previous) {
    return `Create one original question of exact type "${questionType}". Use these only as style references:\n\n${exampleText}`;
  }

  return (
    `Revise this candidate while keeping exact type "${questionType}".\n` +
    `Candidate:\n${JSON.stringify(previous)}\n\n` +
    `Failed checkpoints:\n${feedback
      .map((checkpoint) => `- ${checkpoint.name}: ${checkpoint.detail}`)
      .join("\n")}\n\nStyle references:\n${exampleText}`
  );
}
