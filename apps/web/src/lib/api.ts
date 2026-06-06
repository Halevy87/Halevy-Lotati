import type {
  AddressResolution,
  CaseDetail,
  CaseList,
  CreateCaseInput,
  ManualResolutionInput,
} from "./types";

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
  resolveAddress: (id: string) =>
    request<AddressResolution>(`/api/cases/${id}/resolve-address`, {
      method: "POST",
      body: JSON.stringify({}),
    }),
  getAddressResolution: async (id: string): Promise<AddressResolution | null> => {
    const res = await fetch(`${BASE_URL}/api/cases/${id}/address-resolution`, {
      headers: { "content-type": "application/json" },
    });
    if (res.status === 404) return null;
    if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
    return (await res.json()) as AddressResolution;
  },
  manualResolution: (id: string, input: ManualResolutionInput) =>
    request<AddressResolution>(`/api/cases/${id}/address-resolution/manual`, {
      method: "PATCH",
      body: JSON.stringify(input),
    }),
};
