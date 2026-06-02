import type { CaseDetail, CaseList, CreateCaseInput } from "./types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "content-type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    throw new Error(`API ${res.status}: ${await res.text()}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  listCases: () => request<CaseList>("/api/cases?page=1&page_size=100"),
  getCase: (id: string) => request<CaseDetail>(`/api/cases/${id}`),
  createCase: (input: CreateCaseInput) =>
    request<CaseDetail>("/api/cases", {
      method: "POST",
      body: JSON.stringify(input),
    }),
};
