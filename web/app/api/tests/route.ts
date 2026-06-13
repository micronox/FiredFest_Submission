import { NextResponse } from "next/server";
import { createGeneratedTest, listTests } from "@/lib/queries";

export async function GET() {
  const tests = await listTests();
  return NextResponse.json(tests);
}

export async function POST() {
  try {
    return NextResponse.json(await createGeneratedTest(), { status: 201 });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Generation failed." },
      { status: 500 }
    );
  }
}
