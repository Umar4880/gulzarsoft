export type ChatRequestPayload = {
  user_id: string;
  query: string;
  conversation_id?: string | null;
};

export type ChatResponsePayload = {
  conversation_id: string;
  answer: string;
  approved: boolean;
  route_reason: string;
  iteration_count: number;
  raw_state: Record<string, unknown>;
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function postChatMessage(
  payload: ChatRequestPayload,
): Promise<ChatResponsePayload> {
  const response = await fetch(`${API_BASE_URL}/api/v1/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
    cache: "no-store",
  });

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;

    try {
      const err = (await response.json()) as { detail?: string };
      if (err.detail) {
        detail = err.detail;
      }
    } catch {
      // Keep default detail when response body is not JSON.
    }

    throw new Error(detail);
  }

  return (await response.json()) as ChatResponsePayload;
}
