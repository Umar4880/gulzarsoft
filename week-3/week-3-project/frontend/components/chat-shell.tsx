"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

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
};

const INITIAL_MESSAGE: UiMessage = {
  id: "welcome",
  role: "assistant",
  content:
    "Welcome to GulzarSoft Research Console. Ask a question and I will route it through your multi-agent pipeline.",
  timestamp: currentTime(),
};

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

export function ChatShell() {
  const [userId, setUserId] = useState<string>("");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<UiMessage[]>([INITIAL_MESSAGE]);
  const [draft, setDraft] = useState<string>("");
  const [isSending, setIsSending] = useState<boolean>(false);
  const [error, setError] = useState<string>("");
  const [meta, setMeta] = useState<ChatMeta>({
    approved: false,
    routeReason: "No route decision yet.",
    iterationCount: 0,
  });

  const scrollAnchorRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    setUserId(makeBrowserUserId());
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

    try {
      const response = await postChatMessage({
        user_id: userId,
        query,
        conversation_id: conversationId,
      });

      setConversationId(response.conversation_id);
      setMeta({
        approved: response.approved,
        routeReason: response.route_reason || "Route reason was not provided.",
        iterationCount: response.iteration_count,
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
    } finally {
      setIsSending(false);
    }
  }

  function resetConversation() {
    setConversationId(null);
    setMessages([INITIAL_MESSAGE]);
    setMeta({
      approved: false,
      routeReason: "No route decision yet.",
      iterationCount: 0,
    });
    setError("");
  }

  return (
    <main className="console-root">
      <div className="bg-orb orb-a" aria-hidden="true" />
      <div className="bg-orb orb-b" aria-hidden="true" />

      <div className="console-shell">
        <aside className="info-panel">
          <p className="eyebrow">GulzarSoft</p>
          <h1>Research Console</h1>
          <p className="intro-copy">
            A focused interface for your multi-agent pipeline with clean thread context and decision traces.
          </p>

          <div className="metric-stack">
            <article className="metric-card rise">
              <p className="metric-label">Thread</p>
              <p className="metric-value mono">
                {conversationId ? conversationId.slice(0, 8) : "new"}
              </p>
            </article>

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

          <button className="ghost-button rise delay-4" type="button" onClick={resetConversation}>
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
                  <p className="message-text">{message.content}</p>
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
