export type Classification =
  | "Enquiry"
  | "Complaint"
  | "Order Update"
  | "Support Request"
  | "Promotional"
  | "Spam";

export type ProcessStatus = "processed" | "pending" | "failed";

export interface AgentThoughtStep {
  step: number;
  observation: string;
  thought: string;
  action: string;
}

export interface EmailRecord {
  id: string;
  sender: string;
  senderEmail: string;
  subject: string;
  snippet: string;
  body: string;
  receivedAt: string;
  classification: Classification | "";
  confidence: number;
  status: ProcessStatus;
  thoughtProcess: AgentThoughtStep[];
  suggestedReply: string;
  replySent: boolean;
}
