import { useEffect, useMemo, useRef, useState, type KeyboardEvent, type ReactNode } from "react";

type ChatMode = "general" | "code" | "debug" | "review";
type ThemeName = "normal" | "black" | "white";
type MessageStatus = "pending" | "streaming" | "completed" | "failed" | "stopped";
type SelectorMode = "auto" | "manual";
type WebMode = "off" | "on";
type ModelName = "gpt-4o-mini" | "gpt-4o" | "gpt-5" | "gpt-5.4-mini";
type PromptName = "general" | "code" | "debug" | "review" | "web_research";
type ModelSelection = "auto" | ModelName;
type PromptSelection = "auto" | PromptName;

type ChoiceConfig = {
  mode: "manual";
  model_mode: SelectorMode;
  model_name: ModelName | null;
  prompt_mode: SelectorMode;
  prompt_name: PromptName | null;
  web_mode: WebMode;
};

type SourceSummary = {
  title: string;
  url: string;
  domain: string;
  snippet: string;
  summary: string;
  content_preview?: string;
  rank: number;
};

type MessageMetadata = {
  process?: {
    execution_mode?: string | null;
    model_name?: string | null;
    prompt_name?: string | null;
    web_search_used?: boolean;
    tools_used?: string[];
  } | null;
  sources?: SourceSummary[];
  citations?: Array<{ title?: string; url?: string; rank?: number }>;
  web_search_run_id?: string | null;
};

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt: string;
  status: MessageStatus;
  metadata: MessageMetadata | null;
};

type Thread = {
  id: string;
  title: string;
  updatedAt: string;
  mode: ChatMode;
  preview: string;
  messageCount: number;
  messagesLoaded: boolean;
  messages: Message[];
};

type SessionUser = {
  id: number;
  publicId: string;
  sessionLabel: string;
  email: string | null;
  displayName: string | null;
  userType: "guest" | "registered";
  authProvider: string;
  emailVerified: boolean;
  sessionId: string;
  sessionExpiresAt: string;
  guestMessageLimit: number | null;
  guestMessagesUsed: number;
  remainingGuestMessages: number | null;
};

type AuthSessionResponse = {
  access_token: string;
  token: string;
  user_id: number;
  session_label: string;
  session_id: string;
  expires_at: number;
  refresh_expires_at: number;
  user: {
    id: number;
    public_id: string;
    session_label: string;
    email: string | null;
    display_name: string | null;
    user_type: "guest" | "registered";
    auth_provider: string;
    email_verified: boolean;
    session_id: string;
    session_expires_at: string;
    guest_message_limit: number | null;
    guest_messages_used: number;
    remaining_guest_messages: number | null;
  };
};

type GoogleLoginUrlResponse = {
  enabled: boolean;
  login_url: string | null;
  detail: string | null;
};

type ThreadSummaryResponse = {
  id: string;
  title: string;
  mode: ChatMode;
  updated_at: string;
  last_message_at: string | null;
  preview: string;
  message_count: number;
};

type MessageResponse = {
  id: string;
  role: "user" | "assistant";
  content: string;
  status: MessageStatus;
  created_at: string;
  completed_at: string | null;
  metadata_json: MessageMetadata | null;
};

type ParsedStreamEvent = {
  event: string;
  data: Record<string, unknown>;
};

type ContentBlock =
  | {
      type: "heading";
      level: 1 | 2 | 3 | 4;
      content: string;
    }
  | {
      type: "paragraph";
      content: string;
    }
  | {
      type: "list";
      ordered: boolean;
      items: string[];
    }
  | {
      type: "blockquote";
      lines: string[];
    }
  | {
      type: "code";
      language: string;
      content: string;
    }
  | {
      type: "table";
      headers: string[];
      rows: string[][];
    };

type ExampleSection = {
  title: string;
  code: string;
};

type StructuredCodeExample = {
  label: string;
  code: string;
  language: string;
};

type StructuredAnswer = {
  title: string;
  subtitle: string;
  steps: string[];
  notes: string[];
  examples: StructuredCodeExample[];
};

const ACTIVE_THREAD_STORAGE_KEY = "codebot_active_thread";
const CLIENT_SESSION_STORAGE_KEY = "codebot_client_session_id";
const THEME_STORAGE_KEY = "codebot_theme";
const ACCESS_TOKEN_STORAGE_KEY = "codebot_access_token";

const themeOptions: Array<{
  value: ThemeName;
  label: string;
  description: string;
}> = [
  {
    value: "normal",
    label: "Normal",
    description: "Soft charcoal workspace",
  },
  {
    value: "black",
    label: "Black",
    description: "Pure black high contrast",
  },
  {
    value: "white",
    label: "White",
    description: "Bright light canvas",
  },
];

const starterPrompts = [
  "Review this function and suggest optimizations",
  "Debug why my API request is failing",
  "Generate a clean React component for a dashboard card",
  "Explain this Python stack trace in simple steps",
];

const manualModelOptions: Array<{ value: ModelSelection; label: string }> = [
  { value: "auto", label: "Model: Auto" },
  { value: "gpt-4o-mini", label: "gpt-4o-mini" },
  { value: "gpt-4o", label: "gpt-4o" },
  { value: "gpt-5", label: "gpt-5" },
  { value: "gpt-5.4-mini", label: "gpt-5.4-mini" },
];

const manualPromptOptions: Array<{ value: PromptSelection; label: string }> = [
  { value: "auto", label: "Prompt: Auto" },
  { value: "general", label: "General" },
  { value: "code", label: "Code" },
  { value: "debug", label: "Debug" },
  { value: "review", label: "Review" },
];

const manualWebOptions: Array<{ value: WebMode; label: string }> = [
  { value: "on", label: "Web On" },
  { value: "off", label: "Web Off" },
];

function buildChoiceConfig(
  modelSelection: ModelSelection,
  promptSelection: PromptSelection,
  webMode: WebMode,
): ChoiceConfig {
  return {
    mode: "manual",
    model_mode: modelSelection === "auto" ? "auto" : "manual",
    model_name: modelSelection === "auto" ? null : modelSelection,
    prompt_mode: promptSelection === "auto" ? "auto" : "manual",
    prompt_name: promptSelection === "auto" ? null : promptSelection,
    web_mode: webMode,
  };
}

function uid() {
  return Math.random().toString(36).slice(2, 10);
}

function safeUUID() {
  const cryptoApi = typeof globalThis !== "undefined" ? globalThis.crypto : undefined;
  const randomUUID = cryptoApi && typeof cryptoApi.randomUUID === "function" ? cryptoApi.randomUUID.bind(cryptoApi) : null;
  const getRandomValues =
    cryptoApi && typeof cryptoApi.getRandomValues === "function" ? cryptoApi.getRandomValues.bind(cryptoApi) : null;

  if (randomUUID) {
    return randomUUID();
  }

  if (getRandomValues) {
    const bytes = new Uint8Array(16);
    getRandomValues(bytes);
    bytes[6] = (bytes[6] & 0x0f) | 0x40;
    bytes[8] = (bytes[8] & 0x3f) | 0x80;

    const hex = Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0"));
    return [
      hex.slice(0, 4).join(""),
      hex.slice(4, 6).join(""),
      hex.slice(6, 8).join(""),
      hex.slice(8, 10).join(""),
      hex.slice(10, 16).join(""),
    ].join("-");
  }

  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (char) => {
    const random = Math.floor(Math.random() * 16);
    const value = char === "x" ? random : (random & 0x3) | 0x8;
    return value.toString(16);
  });
}

function getClientSessionId() {
  const saved = window.localStorage.getItem(CLIENT_SESSION_STORAGE_KEY);

  if (saved) {
    return saved;
  }

  const generated = `session-${safeUUID()}`;
  window.localStorage.setItem(CLIENT_SESSION_STORAGE_KEY, generated);
  return generated;
}

function getInitialTheme(): ThemeName {
  if (typeof window === "undefined") {
    return "normal";
  }

  const saved = window.localStorage.getItem(THEME_STORAGE_KEY);
  if (saved === "normal" || saved === "black" || saved === "white") {
    return saved;
  }

  return "normal";
}

function getStoredAccessToken() {
  if (typeof window === "undefined") {
    return "";
  }

  return window.localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY) || "";
}

function storeAccessToken(token: string | null) {
  if (typeof window === "undefined") {
    return;
  }

  if (!token) {
    window.localStorage.removeItem(ACCESS_TOKEN_STORAGE_KEY);
    return;
  }

  window.localStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, token);
}

function formatRelativeTime(value: string) {
  const date = new Date(value);
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

function mapSessionUser(user: AuthSessionResponse["user"]): SessionUser {
  return {
    id: user.id,
    publicId: user.public_id,
    sessionLabel: user.session_label,
    email: user.email,
    displayName: user.display_name,
    userType: user.user_type,
    authProvider: user.auth_provider,
    emailVerified: user.email_verified,
    sessionId: user.session_id,
    sessionExpiresAt: user.session_expires_at,
    guestMessageLimit: user.guest_message_limit,
    guestMessagesUsed: user.guest_messages_used,
    remainingGuestMessages: user.remaining_guest_messages,
  };
}

function normalizeMessageMetadata(value: unknown): MessageMetadata | null {
  if (!value || typeof value !== "object") {
    return null;
  }

  const candidate = value as MessageMetadata;
  return {
    process: candidate.process ?? null,
    sources: Array.isArray(candidate.sources) ? candidate.sources : [],
    citations: Array.isArray(candidate.citations) ? candidate.citations : [],
    web_search_run_id: candidate.web_search_run_id ?? null,
  };
}

function createMessage(
  role: Message["role"],
  content: string,
  options?: Partial<Pick<Message, "id" | "createdAt" | "status" | "metadata">>,
): Message {
  return {
    id: options?.id ?? uid(),
    role,
    content,
    createdAt: options?.createdAt ?? new Date().toISOString(),
    status: options?.status ?? "completed",
    metadata: options?.metadata ?? null,
  };
}

function mapThreadSummary(thread: ThreadSummaryResponse, current?: Thread): Thread {
  return {
    id: thread.id,
    title: thread.title,
    updatedAt: thread.updated_at,
    mode: thread.mode,
    preview: thread.preview,
    messageCount: thread.message_count,
    messagesLoaded: current?.messagesLoaded ?? false,
    messages: current?.messages ?? [],
  };
}

function mapMessageResponse(message: MessageResponse): Message {
  return {
    id: message.id,
    role: message.role,
    content: message.content,
    createdAt: message.created_at,
    status: message.status,
    metadata: normalizeMessageMetadata(message.metadata_json),
  };
}

function mergeThreads(current: Thread[], incoming: ThreadSummaryResponse[]) {
  const currentById = new Map(current.map((thread) => [thread.id, thread]));
  return incoming
    .map((thread) => mapThreadSummary(thread, currentById.get(thread.id)))
    .sort((a, b) => +new Date(b.updatedAt) - +new Date(a.updatedAt));
}

async function readErrorMessage(response: Response) {
  try {
    const payload = (await response.json()) as { detail?: string };
    return payload.detail || `Request failed with status ${response.status}`;
  } catch {
    return `Request failed with status ${response.status}`;
  }
}

function parseSseBuffer(buffer: string) {
  const rawEvents = buffer.split("\n\n");
  const remainder = rawEvents.pop() ?? "";
  const events: ParsedStreamEvent[] = [];

  for (const rawEvent of rawEvents) {
    const lines = rawEvent.split("\n");
    let event = "message";
    const dataLines: string[] = [];

    for (const line of lines) {
      if (line.startsWith("event:")) {
        event = line.slice("event:".length).trim();
      }

      if (line.startsWith("data:")) {
        dataLines.push(line.slice("data:".length).trim());
      }
    }

    if (!dataLines.length) {
      continue;
    }

    try {
      events.push({
        event,
        data: JSON.parse(dataLines.join("\n")) as Record<string, unknown>,
      });
    } catch {
      continue;
    }
  }

  return { events, remainder };
}

function isSpecialBlockStart(line: string) {
  const trimmed = line.trim();

  return (
    trimmed.startsWith("```") ||
    /^#{1,4}\s+/.test(trimmed) ||
    /^>\s?/.test(trimmed) ||
    /^[-*]\s+/.test(trimmed) ||
    /^\d+\.\s+/.test(trimmed) ||
    /^\|.*\|$/.test(trimmed)
  );
}

function isPotentialTableRow(line: string) {
  return /^\|.*\|$/.test(line.trim());
}

function isTableSeparatorRow(line: string) {
  return /^\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?$/.test(line.trim());
}

function parseTableRow(line: string) {
  const normalized = line.trim().replace(/^\|/, "").replace(/\|$/, "");
  return normalized.split("|").map((cell) => cell.trim());
}

function parseContentBlocks(content: string): ContentBlock[] {
  const lines = content.replace(/\r\n/g, "\n").split("\n");
  const blocks: ContentBlock[] = [];
  let index = 0;

  while (index < lines.length) {
    const line = lines[index];
    const trimmed = line.trim();

    if (!trimmed) {
      index += 1;
      continue;
    }

    const codeMatch = trimmed.match(/^```([\w+-]*)\s*$/);

    if (codeMatch) {
      const codeLines: string[] = [];
      index += 1;

      while (index < lines.length && !lines[index].trim().startsWith("```")) {
        codeLines.push(lines[index]);
        index += 1;
      }

      if (index < lines.length) {
        index += 1;
      }

      blocks.push({
        type: "code",
        language: codeMatch[1] || "text",
        content: codeLines.join("\n").trimEnd(),
      });
      continue;
    }

    const headingMatch = trimmed.match(/^(#{1,4})\s+(.+)$/);

    if (headingMatch) {
      blocks.push({
        type: "heading",
        level: headingMatch[1].length as 1 | 2 | 3 | 4,
        content: headingMatch[2].trim(),
      });
      index += 1;
      continue;
    }

    if (/^>\s?/.test(trimmed)) {
      const quoteLines: string[] = [];

      while (index < lines.length && /^>\s?/.test(lines[index].trim())) {
        quoteLines.push(lines[index].trim().replace(/^>\s?/, ""));
        index += 1;
      }

      blocks.push({ type: "blockquote", lines: quoteLines });
      continue;
    }

    if (/^[-*]\s+/.test(trimmed) || /^\d+\.\s+/.test(trimmed)) {
      const ordered = /^\d+\.\s+/.test(trimmed);
      const items: string[] = [];

      while (index < lines.length) {
        const current = lines[index].trim();

        if (!current) {
          break;
        }

        const matcher = ordered ? /^\d+\.\s+(.+)$/ : /^[-*]\s+(.+)$/;
        const match = current.match(matcher);

        if (!match) {
          break;
        }

        items.push(match[1].trim());
        index += 1;
      }

      blocks.push({ type: "list", ordered, items });
      continue;
    }

    if (isPotentialTableRow(trimmed)) {
      const tableLines: string[] = [];

      while (index < lines.length && isPotentialTableRow(lines[index])) {
        tableLines.push(lines[index].trim());
        index += 1;
      }

      if (tableLines.length >= 2) {
        const rawRows = tableLines
          .filter((tableLine) => !isTableSeparatorRow(tableLine))
          .map(parseTableRow)
          .filter((row) => row.some((cell) => cell));

        if (rawRows.length >= 2) {
          const columnCount = Math.max(...rawRows.map((row) => row.length));
          const normalizedRows = rawRows.map((row) =>
            Array.from({ length: columnCount }, (_, cellIndex) => row[cellIndex] ?? ""),
          );

          blocks.push({
            type: "table",
            headers: normalizedRows[0],
            rows: normalizedRows.slice(1),
          });
          continue;
        }
      }

      blocks.push({
        type: "paragraph",
        content: tableLines.join(" "),
      });
      continue;
    }

    const paragraphLines: string[] = [];

    while (index < lines.length) {
      const current = lines[index];
      const currentTrimmed = current.trim();

      if (!currentTrimmed || isSpecialBlockStart(current)) {
        break;
      }

      paragraphLines.push(currentTrimmed);
      index += 1;
    }

    if (paragraphLines.length) {
      blocks.push({
        type: "paragraph",
        content: paragraphLines.join(" "),
      });
      continue;
    }

    index += 1;
  }

  return blocks;
}

function renderInlineContent(content: string) {
  const nodes: ReactNode[] = [];
  const pattern = /(`[^`]+`|\*\*[^*]+\*\*|\[[^\]]+\]\([^)]+\))/g;
  let lastIndex = 0;
  let tokenIndex = 0;

  for (const match of content.matchAll(pattern)) {
    const [token] = match;
    const start = match.index ?? 0;

    if (start > lastIndex) {
      nodes.push(content.slice(lastIndex, start));
    }

    if (token.startsWith("`")) {
      nodes.push(
        <code className="assistant-inline-code" key={`inline-code-${tokenIndex}`}>
          {token.slice(1, -1)}
        </code>,
      );
    } else if (token.startsWith("**")) {
      nodes.push(
        <strong key={`strong-${tokenIndex}`} className="font-semibold text-[var(--text-primary)]">
          {token.slice(2, -2)}
        </strong>,
      );
    } else {
      const linkMatch = token.match(/^\[([^\]]+)\]\(([^)]+)\)$/);

      if (linkMatch) {
        nodes.push(
          <a
            className="text-[var(--accent-link)] underline decoration-[color:var(--accent-link-decoration)] underline-offset-4 transition hover:opacity-80"
            href={linkMatch[2]}
            key={`link-${tokenIndex}`}
            rel="noreferrer"
            target="_blank"
          >
            {linkMatch[1]}
          </a>,
        );
      }
    }

    lastIndex = start + token.length;
    tokenIndex += 1;
  }

  if (lastIndex < content.length) {
    nodes.push(content.slice(lastIndex));
  }

  return nodes;
}

function stripCommentPrefix(line: string) {
  return line
    .trim()
    .replace(/^--\s?/, "")
    .replace(/^\/\/\s?/, "")
    .replace(/^#\s?/, "")
    .replace(/^\/\*\s?/, "")
    .replace(/\s?\*\/$/, "")
    .trim();
}

function isCommentHeading(line: string) {
  const trimmed = line.trim();
  return /^--\s+/.test(trimmed) || /^\/\/\s+/.test(trimmed) || /^#\s+/.test(trimmed) || /^\/\*\s?.+\*\/$/.test(trimmed);
}

function parseExampleSections(language: string, content: string): ExampleSection[] | null {
  if (!content.trim()) {
    return null;
  }

  const normalizedLanguage = language.toLowerCase();

  if (!["sql", "javascript", "typescript", "python", "bash", "text"].includes(normalizedLanguage)) {
    return null;
  }

  const chunks = content
    .split(/\n\s*\n/g)
    .map((chunk) => chunk.trim())
    .filter(Boolean);

  if (chunks.length < 2) {
    return null;
  }

  const sections = chunks
    .map((chunk) => {
      const lines = chunk.split("\n").filter((line) => line.trim());
      const [firstLine, ...restLines] = lines;

      if (!firstLine || !isCommentHeading(firstLine) || restLines.length === 0) {
        return null;
      }

      return {
        title: stripCommentPrefix(firstLine),
        code: restLines.join("\n").trim(),
      };
    })
    .filter((section): section is ExampleSection => Boolean(section && section.title && section.code));

  return sections.length === chunks.length ? sections : null;
}

function normalizeWhitespace(value: string) {
  return value.replace(/\s+/g, " ").trim();
}

function looksLikeCode(value: string) {
  const trimmed = value.trim();

  return (
    /\b(select|insert|update|delete|create|alter|drop|from|where)\b/i.test(trimmed) ||
    /[(){}[\];]/.test(trimmed) ||
    /\b\w+\.\w+\(/.test(trimmed) ||
    /\b\w+__\w+\b/.test(trimmed) ||
    trimmed.includes("=>") ||
    trimmed.includes("::") ||
    trimmed.includes("localhost") ||
    trimmed.includes("127.0.0.1")
  );
}

function inferExampleLanguage(label: string, code: string) {
  const sample = `${label} ${code}`.toLowerCase();

  if (sample.includes("sql")) {
    return "sql";
  }

  if (
    sample.includes("django") ||
    sample.includes("orm") ||
    sample.includes("sqlalchemy") ||
    /\bdef\s+\w+/.test(code) ||
    /\bsession\.query\b/.test(code) ||
    /\bobjects\./.test(code)
  ) {
    return "python";
  }

  if (sample.includes("bash") || sample.includes("shell") || sample.includes("curl ")) {
    return "bash";
  }

  if (sample.includes("typescript") || sample.includes("javascript") || sample.includes("react")) {
    return "typescript";
  }

  return "text";
}

function parseInlineExamples(text: string): StructuredCodeExample[] {
  const normalizedText = normalizeWhitespace(text);

  if (!normalizedText.includes(":")) {
    return [];
  }

  const pattern = /(?:^|\s)([A-Za-z][A-Za-z0-9+#./ -]{0,30}):\s*([^:]+?)(?=(?:\s+[A-Za-z][A-Za-z0-9+#./ -]{0,30}:\s)|$)/g;
  const matches = [...normalizedText.matchAll(pattern)];

  if (!matches.length) {
    return [];
  }

  const reconstructed = matches
    .map((match) => `${match[1].trim()}: ${match[2].trim()}`)
    .join(" ")
    .trim();

  if (normalizeWhitespace(reconstructed) !== normalizedText) {
    return [];
  }

  const examples = matches
    .map((match) => {
      const label = match[1].trim();
      const code = match[2].trim();

      if (!looksLikeCode(code)) {
        return null;
      }

      return {
        label,
        code,
        language: inferExampleLanguage(label, code),
      };
    })
    .filter((example): example is StructuredCodeExample => Boolean(example));

  return examples.length === matches.length ? examples : [];
}

function collectSectionLines(lines: string[], startIndex: number, endIndex: number, marker: string) {
  if (startIndex < 0) {
    return [];
  }

  const sectionLines: string[] = [];
  const inlineContent = lines[startIndex].trim().slice(marker.length).trim();

  if (inlineContent) {
    sectionLines.push(inlineContent);
  }

  for (let index = startIndex + 1; index < endIndex; index += 1) {
    const trimmed = lines[index].trim();

    if (trimmed) {
      sectionLines.push(trimmed);
    }
  }

  return sectionLines;
}

function findSectionIndex(lines: string[], marker: string, startIndex = 0) {
  return lines.findIndex((line, index) => index >= startIndex && line.trim().startsWith(marker));
}

function nextSectionIndex(lines: string[], startIndex: number, markers: string[]) {
  const indexes = markers
    .map((marker) => findSectionIndex(lines, marker, startIndex))
    .filter((index) => index !== -1);

  return indexes.length ? Math.min(...indexes) : lines.length;
}

function collectSectionText(lines: string[], startIndex: number, endIndex: number, marker: string) {
  if (startIndex < 0) {
    return "";
  }

  const inlineContent = lines[startIndex].trim().slice(marker.length).trim();
  const contentLines = inlineContent ? [inlineContent] : [];

  for (let index = startIndex + 1; index < endIndex; index += 1) {
    contentLines.push(lines[index]);
  }

  return contentLines.join("\n").trim();
}

function parseExamplesSection(text: string): StructuredCodeExample[] {
  const lines = text.replace(/\r\n/g, "\n").split("\n");
  const examples: StructuredCodeExample[] = [];
  let index = 0;

  while (index < lines.length) {
    const current = lines[index].trim();

    if (!current) {
      index += 1;
      continue;
    }

    const inlineSplit = current.split(/:\s+/, 2);
    if (inlineSplit.length === 2 && looksLikeCode(inlineSplit[1])) {
      examples.push({
        label: inlineSplit[0].trim(),
        code: inlineSplit[1].trim(),
        language: inferExampleLanguage(inlineSplit[0], inlineSplit[1]),
      });
      index += 1;
      continue;
    }

    const label = current;
    let language = "text";
    let code = "";
    const nextLine = lines[index + 1]?.trim() ?? "";
    const fenceMatch = nextLine.match(/^```([\w+-]*)\s*$/);

    if (fenceMatch) {
      language = fenceMatch[1] || inferExampleLanguage(label, label);
      const codeLines: string[] = [];
      index += 2;

      while (index < lines.length && !lines[index].trim().startsWith("```")) {
        codeLines.push(lines[index]);
        index += 1;
      }

      if (index < lines.length && lines[index].trim().startsWith("```")) {
        index += 1;
      }

      code = codeLines.join("\n").trim();
    } else if (nextLine && looksLikeCode(nextLine)) {
      code = nextLine;
      language = inferExampleLanguage(label, nextLine);
      index += 2;
    } else {
      index += 1;
      continue;
    }

    if (code) {
      examples.push({
        label,
        code,
        language,
      });
    }
  }

  return examples;
}

function parseStructuredAnswer(content: string): StructuredAnswer | null {
  const lines = content.replace(/\r\n/g, "\n").split("\n");
  const titleIndex = findSectionIndex(lines, "TITLE:");
  const subtitleIndex = findSectionIndex(lines, "SUBTITLE:", titleIndex + 1);
  const stepsIndex = findSectionIndex(lines, "STEPS:", titleIndex + 1);

  if (titleIndex === -1 || stepsIndex === -1) {
    return null;
  }

  const notesIndex = findSectionIndex(lines, "NOTES:", stepsIndex + 1);
  const examplesIndex = findSectionIndex(lines, "EXAMPLES:", stepsIndex + 1);
  const title = lines[titleIndex].trim().slice("TITLE:".length).trim();
  const subtitle = subtitleIndex === -1 ? "" : lines[subtitleIndex].trim().slice("SUBTITLE:".length).trim();
  const stepsEnd = nextSectionIndex(lines, stepsIndex + 1, ["NOTES:", "EXAMPLES:"]);
  const notesEnd = nextSectionIndex(lines, notesIndex + 1, ["EXAMPLES:"]);
  const examplesEnd = nextSectionIndex(lines, examplesIndex + 1, ["NOTES:"]);
  const steps = collectSectionLines(lines, stepsIndex, stepsEnd, "STEPS:");
  const rawNotes = notesIndex === -1 ? [] : collectSectionLines(lines, notesIndex, notesEnd, "NOTES:");
  const notes: string[] = [];
  const examples: StructuredCodeExample[] = examplesIndex === -1
    ? []
    : parseExamplesSection(collectSectionText(lines, examplesIndex, examplesEnd, "EXAMPLES:"));

  for (const note of rawNotes) {
    if (!note || note.toLowerCase() === "none") {
      continue;
    }

    const inlineExamples = parseInlineExamples(note);

    if (inlineExamples.length) {
      examples.push(...inlineExamples);
      continue;
    }

    notes.push(note);
  }

  if (!title || (!subtitle && !steps.length && !notes.length && !examples.length)) {
    return null;
  }

  return {
    title,
    subtitle,
    steps,
    notes,
    examples,
  };
}

async function copyText(value: string) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(value);
    return;
  }

  const textarea = document.createElement("textarea");
  textarea.value = value;
  textarea.setAttribute("readonly", "true");
  textarea.style.position = "absolute";
  textarea.style.left = "-9999px";
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand("copy");
  document.body.removeChild(textarea);
}

function MarkdownBlocksContent({ blocks }: { blocks: ContentBlock[] }) {
  return (
    <div className="assistant-markdown">
      {blocks.map((block, index) => {
        if (block.type === "heading") {
          const headingClassName =
            block.level === 1
              ? "assistant-heading assistant-heading-1"
              : block.level === 2
                ? "assistant-heading assistant-heading-2"
                : block.level === 3
                  ? "assistant-heading assistant-heading-3"
                  : "assistant-heading assistant-heading-4";

          return (
            <div className={headingClassName} key={`heading-${index}`}>
              {renderInlineContent(block.content)}
            </div>
          );
        }

        if (block.type === "paragraph") {
          return (
            <p className="assistant-paragraph" key={`paragraph-${index}`}>
              {renderInlineContent(block.content)}
            </p>
          );
        }

        if (block.type === "blockquote") {
          return (
            <blockquote className="assistant-quote" key={`quote-${index}`}>
              {block.lines.map((line, lineIndex) => (
                <p className="assistant-quote-line" key={`quote-line-${lineIndex}`}>
                  {renderInlineContent(line)}
                </p>
              ))}
            </blockquote>
          );
        }

        if (block.type === "list") {
          const ListTag = block.ordered ? "ol" : "ul";

          return (
            <ListTag className="assistant-list" key={`list-${index}`}>
              {block.items.map((item, itemIndex) => (
                <li className="assistant-list-item" key={`list-item-${itemIndex}`}>
                  {renderInlineContent(item)}
                </li>
              ))}
            </ListTag>
          );
        }

        if (block.type === "table") {
          return <TableBlockContent headers={block.headers} key={`table-${index}`} rows={block.rows} />;
        }

        return (
          <CodeBlockContent content={block.content} key={`code-${index}`} language={block.language} />
        );
      })}
    </div>
  );
}

function AssistantMessageContent({ content, isStreaming }: { content: string; isStreaming: boolean }) {
  const structuredAnswer = useMemo(() => parseStructuredAnswer(content), [content]);
  const blocks = useMemo(() => parseContentBlocks(content), [content]);

  if (!content) {
    return <p className="assistant-thinking">{isStreaming ? "Thinking..." : ""}</p>;
  }

  if (structuredAnswer) {
    return <StructuredAnswerContent answer={structuredAnswer} />;
  }

  if (!blocks.length) {
    return <p className="assistant-paragraph">{content}</p>;
  }

  return <MarkdownBlocksContent blocks={blocks} />;
}

function CopyButton({ value }: { value: string }) {
  const [copied, setCopied] = useState(false);
  const timeoutRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        window.clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const handleCopy = async () => {
    try {
      await copyText(value);
      setCopied(true);

      if (timeoutRef.current) {
        window.clearTimeout(timeoutRef.current);
      }

      timeoutRef.current = window.setTimeout(() => {
        setCopied(false);
      }, 1600);
    } catch {
      setCopied(false);
    }
  };

  return (
    <button className="assistant-copy-button" onClick={() => void handleCopy()} type="button">
      <CopyIcon />
      <span>{copied ? "Copied" : "Copy"}</span>
    </button>
  );
}

function CodeSurface({
  content,
  language,
  label,
}: {
  content: string;
  language: string;
  label: string;
}) {
  return (
    <div className="assistant-codeblock">
      <div className="assistant-codeblock-header">
        <div className="assistant-codeblock-meta">
          <span>{language}</span>
          <span>{label}</span>
        </div>
        <CopyButton value={content} />
      </div>
      <pre className="assistant-codeblock-pre">
        <code>{content}</code>
      </pre>
    </div>
  );
}

function StructuredAnswerContent({ answer }: { answer: StructuredAnswer }) {
  return (
    <article className="assistant-structured">
      <header className="assistant-structured-hero">
        <span className="assistant-structured-tag">Title</span>
        <h2 className="assistant-structured-title">{answer.title}</h2>
        {answer.subtitle ? <p className="assistant-structured-subtitle">{answer.subtitle}</p> : null}
      </header>

      {answer.steps.length ? (
        <section className="assistant-structured-section">
          <div className="assistant-structured-section-header">
            <span className="assistant-structured-tag">Steps</span>
          </div>
          <div className="assistant-step-list">
            {answer.steps.map((step, index) => (
              <article className="assistant-step-card" key={`step-${index}`}>
                <span className="assistant-step-index">{String(index + 1).padStart(2, "0")}</span>
                <p className="assistant-step-text">{renderInlineContent(step)}</p>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      {answer.notes.length ? (
        <section className="assistant-structured-section">
          <div className="assistant-structured-section-header">
            <span className="assistant-structured-tag">Notes</span>
          </div>
          <div className="assistant-note-list">
            {answer.notes.map((note, index) => (
              <article className="assistant-note-card" key={`note-${index}`}>
                <p className="assistant-note-text">{renderInlineContent(note)}</p>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      {answer.examples.length ? (
        <section className="assistant-structured-section">
          <div className="assistant-structured-section-header">
            <span className="assistant-structured-tag">Examples</span>
          </div>
          <div className="assistant-example-stack">
            {answer.examples.map((example, index) => (
              <section className="assistant-example-card" key={`structured-example-${index}`}>
                <p className="assistant-example-title">{example.label}</p>
                <CodeSurface content={example.code} label="Snippet" language={example.language} />
              </section>
            ))}
          </div>
        </section>
      ) : null}
    </article>
  );
}

function CodeBlockContent({ content, language }: { content: string; language: string }) {
  const examples = parseExampleSections(language, content);

  if (examples?.length) {
    return (
      <div className="assistant-example-stack">
        {examples.map((example, index) => (
          <section className="assistant-example-card" key={`example-${index}`}>
            <p className="assistant-example-title">{example.title}</p>
            <CodeSurface content={example.code} label="Example" language={language} />
          </section>
        ))}
      </div>
    );
  }

  return <CodeSurface content={content} label="Code" language={language} />;
}

function TableBlockContent({ headers, rows }: { headers: string[]; rows: string[][] }) {
  return (
    <div className="assistant-table-wrap">
      <table className="assistant-table">
        <thead>
          <tr>
            {headers.map((header, index) => (
              <th key={`header-${index}`} scope="col">
                {renderInlineContent(header)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={`row-${rowIndex}`}>
              {row.map((cell, cellIndex) => (
                <td key={`cell-${rowIndex}-${cellIndex}`}>{renderInlineContent(cell)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}


function SourceCards({ sources }: { sources: SourceSummary[] }) {
  if (!sources.length) {
    return null;
  }

  return (
    <div className="source-chips">
      {sources.map((source) => (
        <a
          className="source-chip"
          href={source.url}
          key={`${source.rank}-${source.url}`}
          rel="noreferrer"
          target="_blank"
          title={source.title}
        >
          <img
            alt=""
            className="source-chip-favicon"
            onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
            src={`https://www.google.com/s2/favicons?domain=${source.domain}&sz=32`}
          />
          <span className="source-chip-domain">{source.domain}</span>
        </a>
      ))}
    </div>
  );
}

function AssistantProgress({ label }: { label: string | null }) {
  if (!label) {
    return null;
  }

  return (
    <div className="assistant-progress">
      <span className="assistant-progress-dot" />
      <span>{label}</span>
    </div>
  );
}

function App() {
  const [threads, setThreads] = useState<Thread[]>([]);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [mode, setMode] = useState<ChatMode>("general");
  const [manualModelSelection, setManualModelSelection] = useState<ModelSelection>("auto");
  const [manualPromptSelection, setManualPromptSelection] = useState<PromptSelection>("auto");
  const [manualWebMode, setManualWebMode] = useState<WebMode>("on");
  const [codeContext, setCodeContext] = useState("");
  const [showCodeContext, setShowCodeContext] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamProgress, setStreamProgress] = useState<{
    assistantMessageId: string;
    stage: string;
    label: string;
  } | null>(null);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [sessionUser, setSessionUser] = useState<SessionUser | null>(null);
  const [isBootstrapping, setIsBootstrapping] = useState(true);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [isAuthDialogOpen, setIsAuthDialogOpen] = useState(false);
  const [authView, setAuthView] = useState<"login" | "signup">("signup");
  const [authName, setAuthName] = useState("");
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [isAuthSubmitting, setIsAuthSubmitting] = useState(false);
  const [theme, setTheme] = useState<ThemeName>(getInitialTheme);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(() => {
    if (typeof window === "undefined") {
      return true;
    }

    return window.innerWidth >= 1024;
  });

  const abortRef = useRef<AbortController | null>(null);
  const bootstrapStartedRef = useRef(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const textAreaRef = useRef<HTMLTextAreaElement | null>(null);

  const activeThread = useMemo(() => {
    return threads.find((thread) => thread.id === activeThreadId) ?? null;
  }, [threads, activeThreadId]);

  const isGuestSession = !sessionUser || sessionUser.userType === "guest";

  const openAuthDialog = (view: "login" | "signup") => {
    setError("");
    setAuthView(view);
    setIsAuthDialogOpen(true);
  };

  const authFetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    const headers = new Headers(init?.headers);
    const accessToken = getStoredAccessToken();
    if (accessToken && !headers.has("Authorization")) {
      headers.set("Authorization", `Bearer ${accessToken}`);
    }

    const response = await fetch(input, {
      ...init,
      headers,
      credentials: "include",
    });

    if (response.status === 401 && !String(input).includes("/api/auth/")) {
      try {
        const refreshResponse = await fetch("/api/auth/refresh", {
          method: "POST",
          credentials: "include",
        });

        if (refreshResponse.ok) {
          const session = (await refreshResponse.json()) as AuthSessionResponse;
          storeAccessToken(session.access_token);

          const retryHeaders = new Headers(init?.headers);
          retryHeaders.set("Authorization", `Bearer ${session.access_token}`);

          return fetch(input, {
            ...init,
            headers: retryHeaders,
            credentials: "include",
          });
        }
      } catch {
        // refresh failed, return original 401 response
      }
    }

    return response;
  };

  const loadThreadsFromApi = async (preferredThreadId?: string | null) => {
    const response = await authFetch("/api/threads");

    if (!response.ok) {
      throw new Error(await readErrorMessage(response));
    }

    const data = (await response.json()) as ThreadSummaryResponse[];
    setThreads((current) => mergeThreads(current, data));
    setActiveThreadId((current) => {
      const nextId = preferredThreadId ?? current;

      if (nextId && data.some((thread) => thread.id === nextId)) {
        return nextId;
      }

      return data[0]?.id ?? null;
    });
  };

  const loadMessagesForThread = async (threadId: string) => {
    if (!sessionUser) {
      return;
    }

    setIsLoadingMessages(true);

    try {
      const response = await authFetch(`/api/threads/${threadId}/messages`);

      if (!response.ok) {
        throw new Error(await readErrorMessage(response));
      }

      const data = (await response.json()) as MessageResponse[];
      const nextMessages = data.map(mapMessageResponse);

      setThreads((current) =>
        current
          .map((thread) => {
            if (thread.id !== threadId) {
              return thread;
            }

            return {
              ...thread,
              messages: nextMessages,
              messagesLoaded: true,
              preview: nextMessages[nextMessages.length - 1]?.content ?? thread.preview,
              messageCount: nextMessages.length,
              updatedAt: nextMessages[nextMessages.length - 1]?.createdAt ?? thread.updatedAt,
            };
          })
          .sort((a, b) => +new Date(b.updatedAt) - +new Date(a.updatedAt)),
      );
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Failed to load chat messages.");
    } finally {
      setIsLoadingMessages(false);
    }
  };

  const applyAuthenticatedSession = async (
    session: AuthSessionResponse,
    options?: {
      preserveThreads?: boolean;
      closeDialog?: boolean;
    },
  ) => {
    storeAccessToken(session.access_token);
    setSessionUser(mapSessionUser(session.user));

    if (options?.closeDialog) {
      setIsAuthDialogOpen(false);
      setAuthPassword("");
    }

    if (!options?.preserveThreads) {
      setThreads([]);
      setActiveThreadId(null);
      const preferredThreadId = window.localStorage.getItem(ACTIVE_THREAD_STORAGE_KEY);
      await loadThreadsFromApi(preferredThreadId);
      return;
    }

    const preferredThreadId = window.localStorage.getItem(ACTIVE_THREAD_STORAGE_KEY);
    await loadThreadsFromApi(preferredThreadId);
  };

  const syncCurrentUser = async () => {
    const response = await authFetch("/api/auth/me");

    if (!response.ok) {
      throw new Error(await readErrorMessage(response));
    }

    const user = (await response.json()) as AuthSessionResponse["user"];
    setSessionUser(mapSessionUser(user));
  };

  const bootstrapSession = async () => {
    let meResponse = await authFetch("/api/auth/me");

    if (meResponse.status === 401) {
      const refreshResponse = await authFetch("/api/auth/refresh", {
        method: "POST",
      });

      if (refreshResponse.ok) {
        const refreshedSession = (await refreshResponse.json()) as AuthSessionResponse;
        storeAccessToken(refreshedSession.access_token);
        setSessionUser(mapSessionUser(refreshedSession.user));
        return;
      }

      storeAccessToken(null);
      meResponse = await fetch("/api/auth/me", {
        credentials: "include",
      });
    }

    if (meResponse.ok) {
      const user = (await meResponse.json()) as AuthSessionResponse["user"];
      setSessionUser(mapSessionUser(user));
      return;
    }

    const guestResponse = await authFetch("/api/auth/guest", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        client_session_id: getClientSessionId(),
      }),
    });

    if (!guestResponse.ok) {
      throw new Error(await readErrorMessage(guestResponse));
    }

    const session = (await guestResponse.json()) as AuthSessionResponse;
    storeAccessToken(session.access_token);
    setSessionUser(mapSessionUser(session.user));
  };

  useEffect(() => {
    if (bootstrapStartedRef.current) {
      return;
    }

    bootstrapStartedRef.current = true;
    let cancelled = false;

    const bootstrap = async () => {
      try {
        await bootstrapSession();
      } catch (bootstrapError) {
        if (!cancelled) {
          setError(bootstrapError instanceof Error ? bootstrapError.message : "Failed to create session.");
        }
      } finally {
        if (!cancelled) {
          setIsBootstrapping(false);
        }
      }
    };

    void bootstrap();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!sessionUser) {
      return;
    }

    const REFRESH_INTERVAL = 4 * 60 * 1000; // 4 minutes

    const refreshToken = async () => {
      try {
        const response = await authFetch("/api/auth/refresh", {
          method: "POST",
        });

        if (response.ok) {
          const session = (await response.json()) as AuthSessionResponse;
          storeAccessToken(session.access_token);
        }
      } catch {
        // silent fail - will retry next interval
      }
    };

    const intervalId = window.setInterval(() => void refreshToken(), REFRESH_INTERVAL);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [sessionUser]);

  useEffect(() => {
    window.localStorage.setItem(THEME_STORAGE_KEY, theme);
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const authError = params.get("auth_error");
    if (!authError) {
      return;
    }

    setError(decodeURIComponent(authError));
    params.delete("auth_error");
    const nextQuery = params.toString();
    const nextUrl = `${window.location.pathname}${nextQuery ? `?${nextQuery}` : ""}${window.location.hash}`;
    window.history.replaceState({}, "", nextUrl);
  }, []);

  useEffect(() => {
    if (!sessionUser) {
      return;
    }

    const preferredThreadId = window.localStorage.getItem(ACTIVE_THREAD_STORAGE_KEY);

    void loadThreadsFromApi(preferredThreadId).catch((loadError) => {
      setError(loadError instanceof Error ? loadError.message : "Failed to load chats.");
    });
  }, [sessionUser]);

  useEffect(() => {
    if (!activeThreadId) {
      window.localStorage.removeItem(ACTIVE_THREAD_STORAGE_KEY);
      return;
    }

    window.localStorage.setItem(ACTIVE_THREAD_STORAGE_KEY, activeThreadId);
  }, [activeThreadId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [threads, activeThreadId, isStreaming]);

  useEffect(() => {
    const element = textAreaRef.current;
    if (!element) {
      return;
    }

    element.style.height = "0px";
    element.style.height = `${Math.min(element.scrollHeight, 240)}px`;
  }, [input]);

  useEffect(() => {
    if (!sessionUser || !activeThreadId) {
      return;
    }

    const thread = threads.find((entry) => entry.id === activeThreadId);

    if (!thread || thread.messagesLoaded) {
      return;
    }

    void loadMessagesForThread(activeThreadId);
  }, [sessionUser, activeThreadId, threads]);

  const filteredThreads = useMemo(() => {
    const query = search.trim().toLowerCase();

    if (!query) {
      return threads;
    }

    return threads.filter((thread) => {
      return (
        thread.title.toLowerCase().includes(query) ||
        thread.preview.toLowerCase().includes(query) ||
        thread.messages.some((message) => message.content.toLowerCase().includes(query))
      );
    });
  }, [threads, search]);

  const createThread = async (firstPrompt?: string) => {
    if (!sessionUser) {
      throw new Error("Session not ready.");
    }

    const response = await authFetch("/api/threads", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        title: firstPrompt?.slice(0, 48) || "New conversation",
        mode,
        client_session_id: getClientSessionId(),
      }),
    });

    if (!response.ok) {
      throw new Error(await readErrorMessage(response));
    }

    const thread = (await response.json()) as ThreadSummaryResponse;
    const newThread = mapThreadSummary(thread);
    setThreads((current) => [newThread, ...current]);
    setActiveThreadId(thread.id);
    return thread.id;
  };

  const startFreshChat = () => {
    if (isStreaming) {
      return;
    }

    setInput("");
    setError("");
    setCodeContext("");
    setShowCodeContext(false);
    setActiveThreadId(null);
  };

  const handleThreadSelect = (threadId: string) => {
    setActiveThreadId(threadId);

    if (typeof window !== "undefined" && window.innerWidth < 1024) {
      setIsSidebarOpen(false);
    }
  };

  const updateThreadMessages = (
    threadId: string,
    updater: (messages: Message[]) => Message[],
    nextTitle?: string,
  ) => {
    setThreads((current) =>
      current
        .map((thread) => {
          if (thread.id !== threadId) {
            return thread;
          }

          const nextMessages = updater(thread.messages);
          const lastMessage = nextMessages[nextMessages.length - 1];

          return {
            ...thread,
            title: nextTitle ?? thread.title,
            updatedAt: new Date().toISOString(),
            preview: lastMessage?.content ?? thread.preview,
            messageCount: nextMessages.length,
            messagesLoaded: true,
            messages: nextMessages,
          };
        })
        .sort((a, b) => +new Date(b.updatedAt) - +new Date(a.updatedAt)),
    );
  };

  const stopStreaming = () => {
    abortRef.current?.abort();
    abortRef.current = null;
    setIsStreaming(false);
  };

  const sendMessage = async (presetPrompt?: string) => {
    const prompt = (presetPrompt ?? input).trim();

    if (!prompt || isStreaming || !sessionUser) {
      return;
    }

    setError("");
    setInput("");
    setStreamProgress(null);

    let threadId = activeThread?.id;
    const choiceConfig = buildChoiceConfig(manualModelSelection, manualPromptSelection, manualWebMode);

    if (!threadId) {
      try {
        threadId = await createThread(prompt);
      } catch (threadError) {
        setError(threadError instanceof Error ? threadError.message : "Failed to create chat.");
        return;
      }
    }

    const title = prompt.slice(0, 48);
    const tempUserMessageId = `temp-user-${uid()}`;
    const tempAssistantMessageId = `temp-assistant-${uid()}`;
    const optimisticUserMessage = createMessage("user", prompt, {
      id: tempUserMessageId,
      status: "completed",
    });
    const optimisticAssistantMessage = createMessage("assistant", "", {
      id: tempAssistantMessageId,
      status: "streaming",
      metadata: null,
    });

    updateThreadMessages(
      threadId,
      (messages) => [...messages, optimisticUserMessage, optimisticAssistantMessage],
      title,
    );
    setActiveThreadId(threadId);
    setIsStreaming(true);

    const controller = new AbortController();
    abortRef.current = controller;

    let currentUserMessageId = tempUserMessageId;
    let currentAssistantMessageId = tempAssistantMessageId;
    let sseBuffer = "";

    try {
      const response = await authFetch("/api/chat/stream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          thread_id: threadId,
          query: prompt,
          code: codeContext || null,
          mode,
          choice_config: choiceConfig,
        }),
        signal: controller.signal,
      });

      if (!response.ok || !response.body) {
        throw new Error(await readErrorMessage(response));
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { value, done } = await reader.read();

        if (done) {
          break;
        }

        sseBuffer += decoder.decode(value, { stream: true });
        const parsed = parseSseBuffer(sseBuffer);
        sseBuffer = parsed.remainder;

        for (const event of parsed.events) {
          if (event.event === "message.created") {
            const payload = event.data as {
              user_message: {
                id: string;
                created_at: string;
                status: MessageStatus;
              };
              assistant_message: {
                id: string;
                created_at: string;
                status: MessageStatus;
                metadata_json?: MessageMetadata | null;
              };
            };

            currentUserMessageId = payload.user_message.id;
            currentAssistantMessageId = payload.assistant_message.id;

            updateThreadMessages(threadId, (messages) =>
              messages.map((message) => {
                if (message.id === tempUserMessageId) {
                  return {
                    ...message,
                    id: payload.user_message.id,
                    createdAt: payload.user_message.created_at,
                    status: payload.user_message.status,
                  };
                }

                if (message.id === tempAssistantMessageId) {
                  return {
                    ...message,
                    id: payload.assistant_message.id,
                    createdAt: payload.assistant_message.created_at,
                    status: payload.assistant_message.status,
                    metadata: normalizeMessageMetadata(payload.assistant_message.metadata_json),
                  };
                }

                return message;
              }),
            );
          }

          if (event.event === "message.delta") {
            const payload = event.data as {
              assistant_message_id: string;
              delta: string;
            };

            currentAssistantMessageId = payload.assistant_message_id;

            updateThreadMessages(threadId, (messages) =>
              messages.map((message) =>
                message.id === currentAssistantMessageId || message.id === tempAssistantMessageId
                  ? {
                      ...message,
                      id: currentAssistantMessageId,
                      content: `${message.content}${payload.delta}`,
                      status: "streaming",
                    }
                  : message,
              ),
            );
          }

          if (event.event === "message.progress") {
            const payload = event.data as {
              assistant_message_id: string;
              stage: string;
              label: string;
            };

            setStreamProgress({
              assistantMessageId: payload.assistant_message_id,
              stage: payload.stage,
              label: payload.label,
            });
          }

          if (event.event === "message.sources") {
            const payload = event.data as {
              assistant_message_id: string;
              metadata_json: MessageMetadata | null;
            };

            updateThreadMessages(threadId, (messages) =>
              messages.map((message) =>
                message.id === payload.assistant_message_id || message.id === tempAssistantMessageId
                  ? {
                      ...message,
                      id: payload.assistant_message_id,
                      metadata: normalizeMessageMetadata(payload.metadata_json),
                    }
                  : message,
              ),
            );
          }

          if (event.event === "message.completed") {
            const payload = event.data as {
              assistant_message_id: string;
              content: string;
              metadata_json?: MessageMetadata | null;
            };

            currentAssistantMessageId = payload.assistant_message_id;
            setStreamProgress((current) =>
              current?.assistantMessageId === payload.assistant_message_id ? null : current,
            );

            updateThreadMessages(threadId, (messages) =>
              messages.map((message) =>
                message.id === currentAssistantMessageId || message.id === tempAssistantMessageId
                  ? {
                      ...message,
                      id: currentAssistantMessageId,
                      content: payload.content ?? message.content,
                      status: "completed",
                      metadata: normalizeMessageMetadata(payload.metadata_json),
                    }
                  : message,
              ),
            );
          }

          if (event.event === "message.failed") {
            const payload = event.data as {
              assistant_message_id: string;
              content?: string;
              error?: string;
              metadata_json?: MessageMetadata | null;
            };

            currentAssistantMessageId = payload.assistant_message_id;
            setError(payload.error || "Streaming failed.");
            setStreamProgress((current) =>
              current?.assistantMessageId === payload.assistant_message_id ? null : current,
            );

            updateThreadMessages(threadId, (messages) =>
              messages.map((message) =>
                message.id === currentAssistantMessageId || message.id === tempAssistantMessageId
                  ? {
                      ...message,
                      id: currentAssistantMessageId,
                      content: payload.content || message.content || payload.error || "Streaming failed.",
                      status: "failed",
                      metadata: normalizeMessageMetadata(payload.metadata_json),
                    }
                  : message,
              ),
            );
          }
        }
      }
    } catch (streamError) {
      const message =
        streamError instanceof Error
          ? streamError.name === "AbortError"
            ? "Generation stopped."
            : streamError.message
          : "Unknown streaming error";

      setError(message);
      setStreamProgress((current) =>
        current?.assistantMessageId === currentAssistantMessageId ? null : current,
      );

      updateThreadMessages(threadId, (messages) =>
        messages.map((entry) => {
          if (entry.id !== currentAssistantMessageId && entry.id !== tempAssistantMessageId) {
            return entry;
          }

          return {
            ...entry,
            id: currentAssistantMessageId,
            content: entry.content || message,
            status: streamError instanceof Error && streamError.name === "AbortError" ? "stopped" : "failed",
          };
        }),
      );
    } finally {
      abortRef.current = null;
      setIsStreaming(false);
      setStreamProgress(null);

      try {
        await loadThreadsFromApi(threadId);
        await loadMessagesForThread(threadId);
        await syncCurrentUser();
      } catch (syncError) {
        setError(syncError instanceof Error ? syncError.message : "Failed to refresh chat history.");
      }
    }
  };

  const submitAuthForm = async () => {
    const normalizedEmail = authEmail.trim();

    if (!normalizedEmail || !authPassword.trim()) {
      setError("Email and password are required.");
      return;
    }

    setIsAuthSubmitting(true);
    setError("");

    try {
      const response = await authFetch(authView === "signup" ? "/api/auth/signup" : "/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: normalizedEmail,
          password: authPassword,
          display_name: authView === "signup" ? authName.trim() || null : null,
          client_session_id: getClientSessionId(),
        }),
      });

      if (!response.ok) {
        throw new Error(await readErrorMessage(response));
      }

      const session = (await response.json()) as AuthSessionResponse;
      await applyAuthenticatedSession(session, {
        preserveThreads: authView === "signup" && sessionUser?.userType === "guest",
        closeDialog: true,
      });
    } catch (authError) {
      setError(authError instanceof Error ? authError.message : "Authentication failed.");
    } finally {
      setIsAuthSubmitting(false);
    }
  };

  const handleLogout = async () => {
    setError("");

    try {
      await authFetch("/api/auth/logout", {
        method: "POST",
      });
      storeAccessToken(null);
      setSessionUser(null);
      setThreads([]);
      setActiveThreadId(null);
      setIsSettingsOpen(false);
      await bootstrapSession();
    } catch (logoutError) {
      setError(logoutError instanceof Error ? logoutError.message : "Logout failed.");
    }
  };

  const handleGoogleLogin = async () => {
    setError("");

    try {
      const response = await authFetch("/api/auth/google/url");

      if (!response.ok) {
        throw new Error(await readErrorMessage(response));
      }

      const payload = (await response.json()) as GoogleLoginUrlResponse;
      if (!payload.enabled || !payload.login_url) {
        throw new Error(payload.detail || "Google login is not configured.");
      }

      window.location.assign(payload.login_url);
    } catch (googleError) {
      setError(googleError instanceof Error ? googleError.message : "Google login failed.");
    }
  };

  const handleComposerKeyDown = async (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      await sendMessage();
    }
  };

  return (
    <div
      className="app-shell flex h-screen overflow-hidden"
      data-theme={theme}
      style={{ colorScheme: theme === "white" ? "light" : "dark" }}
    >
      {isSidebarOpen ? (
        <button
          aria-label="Close sidebar backdrop"
          className="fixed inset-0 z-20 bg-[color:var(--overlay)] lg:hidden"
          onClick={() => setIsSidebarOpen(false)}
          type="button"
        />
      ) : null}

      {isAuthDialogOpen ? (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-[color:var(--overlay-strong)] px-4">
          <div className="w-full max-w-md rounded-[28px] border border-[color:var(--border-subtle)] bg-[var(--surface-1)] p-6 text-[var(--text-primary)] shadow-glow">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs uppercase tracking-[0.24em] text-[var(--text-faint)]">Authentication</p>
                <h2 className="mt-2 text-2xl font-semibold text-[var(--text-primary)]">
                  {authView === "signup" ? "Create your account" : "Login to your account"}
                </h2>
                <p className="mt-2 text-sm text-[var(--text-secondary)]">
                  {authView === "signup"
                    ? "Guest chats stay on this account when you upgrade."
                    : "Switch from guest mode to your saved account."}
                </p>
              </div>

              <button
                className="rounded-xl border border-[color:var(--border-subtle)] bg-[var(--surface-0)] px-3 py-2 text-sm text-[var(--text-secondary)] transition hover:bg-[var(--surface-2)]"
                onClick={() => {
                  setError("");
                  setIsAuthDialogOpen(false);
                }}
                type="button"
              >
                Close
              </button>
            </div>

            {error ? (
              <div className="mt-4 rounded-2xl border border-[color:var(--danger-border)] bg-[var(--danger-bg)] px-4 py-3 text-sm text-[var(--danger-text)]">
                {error}
              </div>
            ) : null}

            <div className="mt-5 grid gap-3">
              {authView === "signup" ? (
                <input
                  className="rounded-2xl border border-[color:var(--border-subtle)] bg-[var(--surface-0)] px-4 py-3 text-sm text-[var(--text-primary)] outline-none placeholder:text-[var(--text-faint)]"
                  onChange={(event) => setAuthName(event.target.value)}
                  placeholder="Display name"
                  value={authName}
                />
              ) : null}
              <input
                className="rounded-2xl border border-[color:var(--border-subtle)] bg-[var(--surface-0)] px-4 py-3 text-sm text-[var(--text-primary)] outline-none placeholder:text-[var(--text-faint)]"
                onChange={(event) => setAuthEmail(event.target.value)}
                placeholder="Email address"
                type="email"
                value={authEmail}
              />
              <input
                className="rounded-2xl border border-[color:var(--border-subtle)] bg-[var(--surface-0)] px-4 py-3 text-sm text-[var(--text-primary)] outline-none placeholder:text-[var(--text-faint)]"
                onChange={(event) => setAuthPassword(event.target.value)}
                placeholder="Password"
                type="password"
                value={authPassword}
              />
            </div>

            <div className="mt-5 flex flex-wrap gap-3">
              <button
                className="rounded-2xl bg-[var(--button-primary-bg)] px-4 py-3 text-sm font-semibold text-[var(--button-primary-text)] transition hover:opacity-90 disabled:cursor-not-allowed disabled:bg-[var(--surface-3)] disabled:text-[var(--text-faint)]"
                disabled={isAuthSubmitting}
                onClick={() => void submitAuthForm()}
                type="button"
              >
                {isAuthSubmitting ? "Submitting..." : authView === "signup" ? "Sign up" : "Login"}
              </button>
              <button
                className="rounded-2xl border border-[color:var(--border-subtle)] bg-[var(--surface-2)] px-4 py-3 text-sm font-semibold text-[var(--text-primary)] transition hover:bg-[var(--surface-3)]"
                disabled={isAuthSubmitting}
                onClick={() => void handleGoogleLogin()}
                type="button"
              >
                Continue with Google
              </button>
            </div>

            <div className="mt-4 text-sm text-[var(--text-secondary)]">
              {authView === "signup" ? "Already have an account?" : "Need a new account?"}{" "}
              <button
                className="text-[var(--text-primary)] underline underline-offset-4"
                onClick={() => setAuthView((current) => (current === "signup" ? "login" : "signup"))}
                type="button"
              >
                {authView === "signup" ? "Login" : "Create account"}
              </button>
            </div>
          </div>
        </div>
      ) : null}

      <aside
        className={`${
          isSidebarOpen ? "flex" : "hidden"
        } fixed inset-y-0 left-0 z-30 h-full w-[290px] shrink-0 border-r border-[color:var(--border-subtle)] bg-[var(--sidebar-bg)] lg:static lg:z-auto`}
      >
        <div className="flex h-full min-h-0 w-full flex-col px-4 py-5">
          <div className="mb-4 flex items-center gap-3">
            <div className="flex min-w-0 flex-1 items-center gap-3 rounded-2xl border border-[color:var(--border-subtle)] bg-[var(--surface-2)] px-4 py-3 shadow-glow">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--surface-3)] text-[var(--text-primary)]">
                <SparkIcon />
              </div>
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold tracking-wide text-[var(--text-primary)]">Codebot</p>
                <p className="truncate text-xs text-[var(--text-secondary)]">Streaming AI assistant</p>
              </div>
            </div>

            <button
              aria-label="Close sidebar"
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-[color:var(--border-subtle)] bg-[var(--surface-2)] text-[var(--text-secondary)] transition hover:bg-[var(--surface-3)]"
              onClick={() => setIsSidebarOpen(false)}
              type="button"
            >
              <SidebarToggleIcon />
            </button>
          </div>

          <button
            className="mb-4 flex items-center justify-center gap-2 rounded-2xl bg-[var(--button-primary-bg)] px-4 py-3 text-sm font-semibold text-[var(--button-primary-text)] transition hover:opacity-90"
            onClick={startFreshChat}
            type="button"
          >
            <EditIcon />
            New chat
          </button>

          <div className="mb-4 rounded-2xl border border-[color:var(--border-subtle)] bg-[var(--surface-2)] px-3 py-2">
            <div className="flex items-center gap-2 text-[var(--text-faint)]">
              <SearchIcon />
              <input
                className="w-full border-none bg-transparent text-sm text-[var(--text-primary)] outline-none placeholder:text-[var(--text-faint)]"
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search chats"
                value={search}
              />
            </div>
          </div>

          <div className="mb-3 flex items-center justify-between px-1 text-xs uppercase tracking-[0.2em] text-[var(--text-faint)]">
            <span>Recent</span>
            <span>{threads.length}</span>
          </div>

          <div className="min-h-0 flex-1 space-y-2 overflow-y-auto pr-1">
            {filteredThreads.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-[color:var(--border-subtle)] bg-[var(--surface-1)] p-4 text-sm text-[var(--text-secondary)]">
                {isBootstrapping ? "Preparing secure chat session..." : "No chats yet. Start a conversation to populate the sidebar."}
              </div>
            ) : (
              filteredThreads.map((thread) => {
                return (
                  <button
                    className={`group w-full rounded-2xl border px-3 py-3 text-left transition ${
                      thread.id === activeThreadId
                        ? "border-[color:var(--border-strong)] bg-[var(--surface-2)]"
                        : "border-[color:var(--border-soft)] bg-[var(--surface-1)] hover:border-[color:var(--border-subtle)] hover:bg-[var(--surface-2)]"
                    }`}
                    key={thread.id}
                    onClick={() => handleThreadSelect(thread.id)}
                    type="button"
                  >
                    <p className="truncate text-sm font-medium text-[var(--text-primary)]">{thread.title}</p>
                  </button>
                );
              })
            )}
          </div>

          <div className="mt-4 space-y-2">
            <div className="relative">
              <button
                className="flex w-full items-center gap-3 rounded-2xl border border-[color:var(--border-subtle)] bg-[var(--surface-2)] px-4 py-3 text-left transition hover:bg-[var(--surface-3)]"
                onClick={() => setIsSettingsOpen((current) => !current)}
                type="button"
              >
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[var(--surface-3)] text-sm font-semibold text-[var(--text-primary)]">
                  {sessionUser
                    ? (sessionUser.displayName || sessionUser.email || "U").charAt(0).toUpperCase()
                    : "?"}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-[var(--text-primary)]">
                    {sessionUser
                      ? sessionUser.displayName || sessionUser.email || "Guest"
                      : isBootstrapping
                        ? "Connecting..."
                        : "Unavailable"}
                  </p>
                  {sessionUser?.userType === "guest" && sessionUser.remainingGuestMessages !== null ? (
                    <p className="text-xs text-[var(--accent-text)]">
                      {sessionUser.remainingGuestMessages} messages left
                    </p>
                  ) : null}
                </div>
                <span className={`text-[var(--text-faint)] transition ${isSettingsOpen ? "rotate-180" : ""}`}>
                  <ChevronIcon />
                </span>
              </button>

              {isSettingsOpen ? (
                <div className="mt-2 rounded-2xl border border-[color:var(--border-subtle)] bg-[var(--surface-1)] p-3">
                  <div className="space-y-1">
                    <button
                      className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm text-[var(--text-primary)] transition hover:bg-[var(--surface-2)]"
                      onClick={() => {/* personalization placeholder */}}
                      type="button"
                    >
                      <SettingsIcon />
                      <span>Personalization</span>
                    </button>

                    <div className="px-3 py-2">
                      <p className="mb-2 text-xs uppercase tracking-[0.15em] text-[var(--text-faint)]">Theme</p>
                      <div className="flex gap-2">
                        {themeOptions.map((option) => (
                          <button
                            className={`flex-1 rounded-xl border px-2 py-2 text-center text-xs font-medium transition ${
                              theme === option.value
                                ? "border-[color:var(--theme-ring)] bg-[var(--theme-active-bg)] text-[var(--text-primary)]"
                                : "border-[color:var(--border-subtle)] bg-[var(--surface-2)] text-[var(--text-secondary)] hover:bg-[var(--surface-3)]"
                            }`}
                            key={option.value}
                            onClick={() => setTheme(option.value)}
                            type="button"
                          >
                            {option.label}
                          </button>
                        ))}
                      </div>
                    </div>

                    <div className="my-1 border-t border-[color:var(--border-soft)]" />

                    {isGuestSession ? (
                      <>
                        <button
                          className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm text-[var(--text-primary)] transition hover:bg-[var(--surface-2)]"
                          onClick={() => openAuthDialog("signup")}
                          type="button"
                        >
                          Sign up
                        </button>
                        <button
                          className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm text-[var(--text-primary)] transition hover:bg-[var(--surface-2)]"
                          onClick={() => openAuthDialog("login")}
                          type="button"
                        >
                          Login
                        </button>
                      </>
                    ) : (
                      <button
                        className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm text-[var(--danger-text)] transition hover:bg-[var(--surface-2)]"
                        onClick={() => void handleLogout()}
                        type="button"
                      >
                        Logout
                      </button>
                    )}
                  </div>
                </div>
              ) : null}
            </div>
          </div>
        </div>
      </aside>

      {!isSidebarOpen ? (
        <aside className="hidden h-full w-[72px] shrink-0 border-r border-[color:var(--border-subtle)] bg-[var(--sidebar-bg)] lg:flex lg:flex-col lg:items-center lg:px-3 lg:py-5">
          <button
            aria-label="Open sidebar"
            className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl border border-[color:var(--border-subtle)] bg-[var(--surface-2)] text-[var(--text-secondary)] transition hover:bg-[var(--surface-3)]"
            onClick={() => setIsSidebarOpen(true)}
            title="Open sidebar"
            type="button"
          >
            <SidebarToggleIcon />
          </button>

          <button
            aria-label="New chat"
            className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl border border-[color:var(--border-subtle)] bg-[var(--surface-2)] text-[var(--text-secondary)] transition hover:bg-[var(--surface-3)]"
            onClick={startFreshChat}
            title="New chat"
            type="button"
          >
            <EditIcon />
          </button>

          <button
            aria-label="Open search"
            className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl border border-[color:var(--border-subtle)] bg-[var(--surface-2)] text-[var(--text-secondary)] transition hover:bg-[var(--surface-3)]"
            onClick={() => setIsSidebarOpen(true)}
            title="Open search"
            type="button"
          >
            <SearchIcon />
          </button>

          <button
            aria-label="Open settings"
            className="flex h-10 w-10 items-center justify-center rounded-xl border border-[color:var(--border-subtle)] bg-[var(--surface-2)] text-[var(--text-secondary)] transition hover:bg-[var(--surface-3)]"
            onClick={() => {
              setIsSidebarOpen(true);
              setIsSettingsOpen(true);
            }}
            title="Open settings"
            type="button"
          >
            <SettingsIcon />
          </button>
        </aside>
      ) : null}

      <main className="flex h-full min-h-0 flex-1 flex-col overflow-hidden">
        <header className="shrink-0 border-b border-[color:var(--border-subtle)] bg-[var(--header-bg)] backdrop-blur">
          <div className="mx-auto flex w-full max-w-5xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
            <div className="flex items-center gap-3">
              <button
                className="flex h-9 w-9 items-center justify-center rounded-xl border border-[color:var(--border-subtle)] bg-[var(--surface-2)] text-[var(--text-secondary)] transition hover:bg-[var(--surface-3)] lg:hidden"
                onClick={() => setIsSidebarOpen(true)}
                type="button"
              >
                <SidebarToggleIcon />
              </button>
              <h1 className="text-base font-semibold text-[var(--text-primary)]">Codebot</h1>
            </div>

            <div className="flex items-center gap-2">
              <select
                className="rounded-xl border border-[color:var(--border-subtle)] bg-[var(--surface-2)] px-3 py-2 text-sm text-[var(--text-primary)] outline-none transition hover:bg-[var(--surface-3)]"
                onChange={(event) => setMode(event.target.value as ChatMode)}
                value={mode}
              >
                <option value="general">General</option>
                <option value="code">Code</option>
                <option value="debug">Debug</option>
                <option value="review">Review</option>
              </select>

              <button
                className="rounded-xl border border-[color:var(--border-subtle)] bg-[var(--surface-2)] px-3 py-2 text-sm text-[var(--text-secondary)] transition hover:bg-[var(--surface-3)]"
                onClick={() => setShowCodeContext((current) => !current)}
                type="button"
              >
                {showCodeContext ? "Hide code" : "Add code"}
              </button>
            </div>
          </div>
        </header>

        <div className="relative min-h-0 flex-1">
          <div className="pointer-events-none absolute inset-0 bg-[var(--workspace-overlay)]" />

          <div className="relative flex h-full min-h-0 flex-col">
            <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain">
              <div className="relative mx-auto flex w-full max-w-5xl flex-col px-4 py-6 sm:px-6">
                {activeThread && !activeThread.messagesLoaded && isLoadingMessages ? (
                  <section className="mx-auto mt-8 w-full max-w-3xl rounded-[32px] border border-[color:var(--border-subtle)] bg-[var(--surface-1)] p-8 shadow-glow">
                    <p className="text-sm text-[var(--text-secondary)]">Loading chat history...</p>
                  </section>
                ) : activeThread?.messages.length ? (
                  <div className="space-y-8 pb-8">
                    {activeThread.messages.map((message) => (
                      <div
                        className={`flex animate-rise ${message.role === "user" ? "justify-end" : "justify-start"}`}
                        key={message.id}
                      >
                        {message.role === "user" ? (
                          <section className="max-w-[70%] rounded-[28px] bg-[var(--user-bubble-bg)] px-5 py-3 shadow-lg">
                            <div className="message-content text-sm leading-7 text-[var(--user-bubble-text)]">
                              {message.content}
                            </div>
                          </section>
                        ) : (
                          <section className="w-full max-w-3xl px-2 py-1">
                            <AssistantMessageContent
                              content={message.content}
                              isStreaming={isStreaming && message.id === activeThread.messages[activeThread.messages.length - 1]?.id}
                            />
                            <AssistantProgress
                              label={streamProgress?.assistantMessageId === message.id ? streamProgress.label : null}
                            />
                            <SourceCards sources={message.metadata?.sources ?? []} />
                          </section>
                        )}
                      </div>
                    ))}
                    <div ref={messagesEndRef} />
                  </div>
                ) : (
                  <section className="mx-auto mt-8 w-full max-w-3xl rounded-[32px] border border-[color:var(--border-subtle)] bg-[var(--surface-1)] p-8 shadow-glow">
                    <div className="mb-6 flex items-center gap-4">
                      <div className="flex h-14 w-14 items-center justify-center rounded-3xl bg-[var(--surface-2)] text-[var(--text-primary)]">
                        <SparkIcon />
                      </div>
                      <div>
                        <p className="text-xs uppercase tracking-[0.25em] text-[var(--text-faint)]">Frontend ready</p>
                        <h2 className="mt-2 text-3xl font-semibold text-[var(--text-primary)]">Ask Codebot anything</h2>
                      </div>
                    </div>

                    <p className="max-w-2xl text-sm leading-7 text-[var(--text-secondary)]">
                      This UI now uses database-backed sessions, guest upgrades, and account-linked chat history instead of
                      local-only sidebar state.
                    </p>

                    <div className="mt-8 grid gap-3 sm:grid-cols-2">
                      {starterPrompts.map((prompt) => (
                        <button
                          className="rounded-2xl border border-[color:var(--border-subtle)] bg-[var(--surface-2)] px-4 py-4 text-left text-sm text-[var(--text-secondary)] transition hover:bg-[var(--surface-3)]"
                          key={prompt}
                          onClick={() => void sendMessage(prompt)}
                          type="button"
                        >
                          {prompt}
                        </button>
                      ))}
                    </div>
                  </section>
                )}
              </div>
            </div>

            <div className="shrink-0 border-t border-[color:var(--border-subtle)] bg-[var(--header-bg)] px-4 py-4 backdrop-blur sm:px-6">
              <div className="mx-auto w-full max-w-5xl">
              {showCodeContext ? (
                <div className="mb-3 rounded-3xl border border-[color:var(--border-subtle)] bg-[var(--surface-1)] p-4">
                  <div className="mb-2 flex items-center justify-between">
                    <p className="text-sm font-medium text-[var(--text-primary)]">Code context</p>
                    <span className="text-xs text-[var(--text-faint)]">Sent as `code` in the API request</span>
                  </div>
                  <textarea
                    className="min-h-28 w-full resize-y rounded-2xl border border-[color:var(--border-subtle)] bg-[var(--surface-0)] px-4 py-3 text-sm text-[var(--text-primary)] outline-none placeholder:text-[var(--text-faint)]"
                    onChange={(event) => setCodeContext(event.target.value)}
                    placeholder="Paste code here if you want debug/review/code generation context."
                    value={codeContext}
                  />
                </div>
              ) : null}

              <div className="rounded-[28px] border border-[color:var(--border-subtle)] bg-[var(--surface-1)] p-3 shadow-glow">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3 border-b border-[color:var(--border-subtle)] px-2 pb-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <select
                      className="choice-select"
                      onChange={(event) => setManualModelSelection(event.target.value as ModelSelection)}
                      value={manualModelSelection}
                    >
                      {manualModelOptions.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                    <select
                      className="choice-select"
                      onChange={(event) => setManualPromptSelection(event.target.value as PromptSelection)}
                      value={manualPromptSelection}
                    >
                      {manualPromptOptions.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                    <select
                      className="choice-select"
                      onChange={(event) => setManualWebMode(event.target.value as WebMode)}
                      value={manualWebMode}
                    >
                      {manualWebOptions.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="text-xs text-[var(--text-secondary)]">
                    Web stays on by default. Turn it off only when you do not want live sources.
                  </div>
                </div>

                <div className="flex items-end gap-3">
                  <button
                    className="hidden h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-[color:var(--border-subtle)] bg-[var(--surface-2)] text-[var(--text-secondary)] transition hover:bg-[var(--surface-3)] sm:flex"
                    onClick={() => setShowCodeContext((current) => !current)}
                    type="button"
                  >
                    <CodeIcon />
                  </button>

                  <textarea
                    className="max-h-60 min-h-12 flex-1 resize-none border-none bg-transparent px-2 py-3 text-sm leading-6 text-[var(--text-primary)] outline-none placeholder:text-[var(--text-faint)]"
                    onChange={(event) => setInput(event.target.value)}
                    onKeyDown={handleComposerKeyDown}
                    placeholder="Message Codebot..."
                    ref={textAreaRef}
                    rows={1}
                    value={input}
                  />

                  {isStreaming ? (
                    <button
                      className="h-12 shrink-0 rounded-2xl border border-[color:var(--danger-border)] bg-[var(--danger-bg)] px-4 text-sm font-semibold text-[var(--danger-text)] transition hover:opacity-90"
                      onClick={stopStreaming}
                      type="button"
                    >
                      Stop
                    </button>
                  ) : (
                    <button
                      className="h-12 shrink-0 rounded-2xl bg-[var(--button-primary-bg)] px-5 text-sm font-semibold text-[var(--button-primary-text)] transition hover:opacity-90 disabled:cursor-not-allowed disabled:bg-[var(--surface-3)] disabled:text-[var(--text-faint)]"
                      disabled={!input.trim() || isBootstrapping || !sessionUser}
                      onClick={() => void sendMessage()}
                      type="button"
                    >
                      Send
                    </button>
                  )}
                </div>

                <div className="mt-2 px-2 text-right text-xs text-[var(--text-faint)]">
                  <span>Enter to send, Shift+Enter for newline</span>
                </div>
              </div>

                {error ? <p className="mt-3 text-sm text-[var(--danger-text)]">{error}</p> : null}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

function SparkIcon() {
  return (
    <svg aria-hidden="true" className="h-5 w-5" fill="none" viewBox="0 0 24 24">
      <path
        d="M12 3L13.95 8.05L19 10L13.95 11.95L12 17L10.05 11.95L5 10L10.05 8.05L12 3Z"
        fill="currentColor"
      />
    </svg>
  );
}

function EditIcon() {
  return (
    <svg aria-hidden="true" className="h-4 w-4" fill="none" viewBox="0 0 24 24">
      <path
        d="M4 20H8L18.5 9.5C19.3284 8.67157 19.3284 7.32843 18.5 6.5V6.5C17.6716 5.67157 16.3284 5.67157 15.5 6.5L5 17V20Z"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.8"
      />
    </svg>
  );
}

function SearchIcon() {
  return (
    <svg aria-hidden="true" className="h-4 w-4" fill="none" viewBox="0 0 24 24">
      <circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="1.8" />
      <path d="M20 20L16.65 16.65" stroke="currentColor" strokeLinecap="round" strokeWidth="1.8" />
    </svg>
  );
}

function CodeIcon() {
  return (
    <svg aria-hidden="true" className="h-5 w-5" fill="none" viewBox="0 0 24 24">
      <path
        d="M8 8L4 12L8 16M16 8L20 12L16 16M14 4L10 20"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.8"
      />
    </svg>
  );
}

function SettingsIcon() {
  return (
    <svg aria-hidden="true" className="h-5 w-5" fill="none" viewBox="0 0 24 24">
      <path
        d="M12 8.5A3.5 3.5 0 1 1 8.5 12A3.5 3.5 0 0 1 12 8.5Z"
        stroke="currentColor"
        strokeWidth="1.8"
      />
      <path
        d="M19.4 15A1 1 0 0 0 19.6 16.1L19.7 16.2A1.2 1.2 0 0 1 19.7 17.9L17.9 19.7A1.2 1.2 0 0 1 16.2 19.7L16.1 19.6A1 1 0 0 0 15 19.4A1 1 0 0 0 14.4 20.3V20.6A1.2 1.2 0 0 1 13.2 21.8H10.8A1.2 1.2 0 0 1 9.6 20.6V20.4A1 1 0 0 0 9 19.4A1 1 0 0 0 7.9 19.6L7.8 19.7A1.2 1.2 0 0 1 6.1 19.7L4.3 17.9A1.2 1.2 0 0 1 4.3 16.2L4.4 16.1A1 1 0 0 0 4.6 15A1 1 0 0 0 3.7 14.4H3.4A1.2 1.2 0 0 1 2.2 13.2V10.8A1.2 1.2 0 0 1 3.4 9.6H3.6A1 1 0 0 0 4.6 9A1 1 0 0 0 4.4 7.9L4.3 7.8A1.2 1.2 0 0 1 4.3 6.1L6.1 4.3A1.2 1.2 0 0 1 7.8 4.3L7.9 4.4A1 1 0 0 0 9 4.6A1 1 0 0 0 9.6 3.7V3.4A1.2 1.2 0 0 1 10.8 2.2H13.2A1.2 1.2 0 0 1 14.4 3.4V3.6A1 1 0 0 0 15 4.6A1 1 0 0 0 16.1 4.4L16.2 4.3A1.2 1.2 0 0 1 17.9 4.3L19.7 6.1A1.2 1.2 0 0 1 19.7 7.8L19.6 7.9A1 1 0 0 0 19.4 9A1 1 0 0 0 20.3 9.6H20.6A1.2 1.2 0 0 1 21.8 10.8V13.2A1.2 1.2 0 0 1 20.6 14.4H20.4A1 1 0 0 0 19.4 15Z"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.4"
      />
    </svg>
  );
}

function CopyIcon() {
  return (
    <svg aria-hidden="true" className="h-4 w-4" fill="none" viewBox="0 0 24 24">
      <rect height="11" rx="2" stroke="currentColor" strokeWidth="1.8" width="11" x="9" y="9" />
      <path
        d="M7 15H6C4.89543 15 4 14.1046 4 13V6C4 4.89543 4.89543 4 6 4H13C14.1046 4 15 4.89543 15 6V7"
        stroke="currentColor"
        strokeLinecap="round"
        strokeWidth="1.8"
      />
    </svg>
  );
}

function ChevronIcon() {
  return (
    <svg aria-hidden="true" className="h-4 w-4" fill="none" viewBox="0 0 24 24">
      <path d="M6 9L12 15L18 9" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
    </svg>
  );
}

function SidebarToggleIcon() {
  return (
    <svg aria-hidden="true" className="h-5 w-5" fill="none" viewBox="0 0 24 24">
      <rect height="14" rx="2.5" stroke="currentColor" strokeWidth="1.8" width="16" x="4" y="5" />
      <path d="M10 5V19" stroke="currentColor" strokeWidth="1.8" />
    </svg>
  );
}

export default App;
