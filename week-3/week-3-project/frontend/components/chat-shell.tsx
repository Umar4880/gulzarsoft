"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { postChatMessage } from "../lib/api";

type Role = "user" | "assistant";

type UiMessage = {
  id: string;
  role: Role;
  content: string;
  timestamp: string;
};

type ChatMeta = {
  approved: boolean;
  routeReason: string;
  iterationCount: number;
  lastAgent: string;
  nextAgent: string;
  backendStage: string;
};

const WELCOME_MESSAGE =
  "Welcome to GulzarSoft Research Console. Ask a question and I will route it through your multi-agent pipeline.";

function makeWelcomeMessage(timestamp = ""): UiMessage {
  return {
    id: "welcome",
    role: "assistant",
    content: WELCOME_MESSAGE,
    timestamp,
  };
}

function currentTime(): string {
  return new Date().toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function makeBrowserUserId(): string {
  const storageKey = "gulzarsoft_user_id";
  const existing = window.localStorage.getItem(storageKey);

  if (existing) {
    return existing;
  }

  const id = window.crypto.randomUUID();
  window.localStorage.setItem(storageKey, id);
  return id;
}

function readString(record: Record<string, unknown>, key: string): string {
  const value = record[key];
  return typeof value === "string" ? value : "";
}

function readBoolean(record: Record<string, unknown>, key: string): boolean | null {
  const value = record[key];
  return typeof value === "boolean" ? value : null;
}

function cleanRouteReason(rawReason: string): string {
  const withoutPrefix = rawReason
    .replace(/^Supervisor routed to\s+__?\w+__?\s*:?\s*/i, "")
    .replace(/^Supervisor routed to\s+\w+\s*:?\s*/i, "")
    .replace(/\*\*/g, "")
    .replace(/\s+/g, " ")
    .trim();

  if (!withoutPrefix) {
    return "Route reason was not provided.";
  }

  const firstSentence = withoutPrefix.split(/(?<=[.!?])\s+/)[0]?.trim() ?? withoutPrefix;
  return firstSentence.slice(0, 220);
}

export function ChatShell() {
  const [userId, setUserId] = useState<string>("");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<UiMessage[]>([makeWelcomeMessage()]);
  const [draft, setDraft] = useState<string>("");
  const [isSending, setIsSending] = useState<boolean>(false);
  const [error, setError] = useState<string>("");
  const [meta, setMeta] = useState<ChatMeta>({
    approved: false,
    routeReason: "No route decision yet.",
    iterationCount: 0,
    lastAgent: "idle",
    nextAgent: "supervisor",
    backendStage: "waiting for input",
  });

  const scrollAnchorRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    setUserId(makeBrowserUserId());
  }, []);

  useEffect(() => {
    // Keep server and client HTML identical at first paint, then fill timestamp on mount.
    setMessages((prev) => {
      if (prev.length !== 1 || prev[0].id !== "welcome" || prev[0].timestamp) {
        return prev;
      }

      return [makeWelcomeMessage(currentTime())];
    });
  }, []);

  useEffect(() => {
    scrollAnchorRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isSending]);

  const canSend = useMemo(() => {
    return Boolean(userId && draft.trim() && !isSending);
  }, [draft, isSending, userId]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const query = draft.trim();
    if (!query || isSending || !userId) {
      return;
    }

    const userMessage: UiMessage = {
      id: `${Date.now()}-user`,
      role: "user",
      content: query,
      timestamp: currentTime(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setDraft("");
    setError("");
    setIsSending(true);
    setMeta((prev) => ({
      ...prev,
      backendStage: "supervisor deciding route",
      nextAgent: "supervisor",
    }));

    try {
      const response = await postChatMessage({
        user_id: userId,
        query,
        conversation_id: conversationId,
      });

      const rawState = response.raw_state ?? {};
      const routeReason = cleanRouteReason(
        readString(rawState, "route_reason") || response.route_reason || "",
      );
      const approved = readBoolean(rawState, "is_approved") ?? response.approved;
      const lastAgent = readString(rawState, "last_agent") || "unknown";
      const nextAgent = readString(rawState, "next_agent") || "end";

      setConversationId(response.conversation_id);
      setMeta({
        approved,
        routeReason,
        iterationCount: response.iteration_count,
        lastAgent,
        nextAgent,
        backendStage: approved ? "workflow approved" : "workflow completed",
      });

      const assistantMessage: UiMessage = {
        id: `${Date.now()}-assistant`,
        role: "assistant",
        content: response.answer,
        timestamp: currentTime(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (submissionError) {
      const message =
        submissionError instanceof Error
          ? submissionError.message
          : "Failed to reach the API. Check if backend is running.";

      setError(message);
      setMeta((prev) => ({
        ...prev,
        backendStage: "request failed",
      }));
    } finally {
      setIsSending(false);
    }
  }

  function resetConversation() {
    setConversationId(null);
    setMessages([makeWelcomeMessage(currentTime())]);
    setMeta({
      approved: false,
      routeReason: "No route decision yet.",
      iterationCount: 0,
      lastAgent: "idle",
      nextAgent: "supervisor",
      backendStage: "waiting for input",
    });
    setError("");
  }

  return (
    <main className="console-root">

      <div className="console-shell">
        <aside className="info-panel">
          <p className="eyebrow">GulzarSoft</p>
          <h1>Research Console</h1>
          <p className="intro-copy">
            A focused interface for your multi-agent pipeline with clean thread context and decision traces.
          </p>

          <div className="metric-stack">
            <article className="metric-card rise delay-1">
              <p className="metric-label">Iterations</p>
              <p className="metric-value">{meta.iterationCount}</p>
            </article>

            <article className="metric-card rise delay-2">
              <p className="metric-label">Approval</p>
              <p className={`metric-value ${meta.approved ? "good" : "warn"}`}>
                {meta.approved ? "approved" : "in review"}
              </p>
            </article>
          </div>

          <article className="route-note rise delay-3">
            <p className="metric-label">Last route reason</p>
            <p>{meta.routeReason}</p>
          </article>

          <article className="route-note rise delay-4">
            <p className="metric-label">Backend stage</p>
            <p className="status-inline">
              <strong>{isSending ? "processing" : meta.backendStage}</strong>
            </p>
            <p className="status-inline">last: {meta.lastAgent}</p>
            <p className="status-inline">next: {meta.nextAgent}</p>
          </article>

          <button className="ghost-button rise delay-5" type="button" onClick={resetConversation}>
            Start New Thread
          </button>
        </aside>

        <section className="chat-panel">
          <header className="chat-header">
            <div>
              <p className="chat-title">Agent Conversation</p>
              <p className="chat-subtitle">Connected to /api/v1/chat</p>
            </div>
            <span className="status-chip">{isSending ? "processing" : "ready"}</span>
          </header>

          <div className="chat-log" role="log" aria-live="polite">
            {messages.map((message, index) => (
              <article
                key={message.id}
                className={`message-row ${message.role}`}
                style={{ animationDelay: `${index * 55}ms` }}
              >
                <div className="message-bubble">
                  <div className="message-text markdown-body">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
                  </div>
                  <span className="message-time">{message.timestamp}</span>
                </div>
              </article>
            ))}

            {isSending && (
              <article className="message-row assistant">
                <div className="message-bubble typing">
                  <span className="dot" />
                  <span className="dot" />
                  <span className="dot" />
                </div>
              </article>
            )}

            {error && <p className="error-banner">{error}</p>}
            <div ref={scrollAnchorRef} />
          </div>

          <form className="composer" onSubmit={onSubmit}>
            <textarea
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder="Ask your research question..."
              className="composer-input"
              rows={3}
              disabled={isSending}
            />
            <button className="send-button" type="submit" disabled={!canSend}>
              {isSending ? "Sending..." : "Send"}
            </button>
          </form>
        </section>
      </div>
    </main>
  );
}
