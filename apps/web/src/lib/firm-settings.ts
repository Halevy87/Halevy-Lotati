// Firm requester details used to speed up filling the Taboo (Land Registry) form.
// Stored locally on the lawyer's machine — NON-sensitive contact details only, never a card.

export interface FirmSettings {
  name: string;
  phone: string;
  email: string;
}

const KEY = "halevy.firmSettings";
const EMPTY: FirmSettings = { name: "", phone: "", email: "" };

export function getFirmSettings(): FirmSettings {
  if (typeof window === "undefined") return { ...EMPTY };
  try {
    return { ...EMPTY, ...(JSON.parse(localStorage.getItem(KEY) || "{}") as Partial<FirmSettings>) };
  } catch {
    return { ...EMPTY };
  }
}

export function saveFirmSettings(settings: FirmSettings): void {
  localStorage.setItem(KEY, JSON.stringify(settings));
}
