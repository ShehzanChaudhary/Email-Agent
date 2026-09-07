import { EmailRecord } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function fetchEmails(): Promise<EmailRecord[]> {
  const res = await fetch(`${API_BASE_URL}/api/emails`);
  if (!res.ok) {
    throw new Error(`Failed to load emails (${res.status} ${res.statusText})`);
  }
  return res.json();
}
