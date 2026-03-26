import { useEffect, useMemo, useRef, useState, type KeyboardEvent, type ReactNode } from "react";

type ChatMode = "chat" | "code" | "debug" | "review";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt: string;
};

type Thread = {
  id: string;
  title: string;
  updatedAt: string;
  messages: Message[];
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

const THREADS_STORAGE_KEY = "codebot_threads";
const ACTIVE_THREAD_STORAGE_KEY = "codebot_active_thread";
const USER_ID_STORAGE_KEY = "codebot_user_id";

const starterPrompts = [
  "Review this function and suggest optimizations",
  "Debug why my API request is failing",
  "Generate a clean React component for a dashboard card",
  "Explain this Python stack trace in simple steps",
];

function uid() {
  return Math.random().toString(36).slice(2, 10);
}

function getStoredUserId() {
  const saved = window.localStorage.getItem(USER_ID_STORAGE_KEY);

  if (saved) {
    const parsed = Number(saved);

    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }

  const generated = Math.floor(100000 + Math.random() * 900000);
  window.localStorage.setItem(USER_ID_STORAGE_KEY, String(generated));
  return generated;
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

function createMessage(role: Message["role"], content: string): Message {
  return {
    id: uid(),
    role,
    content,
    createdAt: new Date().toISOString(),
  };
}

function loadThreads() {
  const saved = window.localStorage.getItem(THREADS_STORAGE_KEY);

  if (!saved) {
    return [];
  }

  try {
    return JSON.parse(saved) as Thread[];
  } catch {
    return [];
  }
}

function isSpecialBlockStart(line: string) {
  const trimmed = line.trim();

  return (
    trimmed.startsWith("```") ||
    /^#{1,4}\s+/.test(trimmed) ||
    /^>\s?/.test(trimmed) ||
    /^[-*]\s+/.test(trimmed) ||
    /^\d+\.\s+/.test(trimmed)
  );
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
        <strong key={`strong-${tokenIndex}`} className="font-semibold text-zinc-50">
          {token.slice(2, -2)}
        </strong>,
      );
    } else {
      const linkMatch = token.match(/^\[([^\]]+)\]\(([^)]+)\)$/);

      if (linkMatch) {
        nodes.push(
          <a
            className="text-amber-200 underline decoration-amber-200/50 underline-offset-4 transition hover:text-amber-100"
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

        return (
          <CodeBlockContent content={block.content} key={`code-${index}`} language={block.language} />
        );
      })}
    </div>
  );
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

function App() {
  const [threads, setThreads] = useState<Thread[]>([]);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [mode, setMode] = useState<ChatMode>("chat");
  const [codeContext, setCodeContext] = useState("");
  const [showCodeContext, setShowCodeContext] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [userId, setUserId] = useState<number | null>(null);

  const abortRef = useRef<AbortController | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const textAreaRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    const initialThreads = loadThreads();
    const initialActiveThread = window.localStorage.getItem(ACTIVE_THREAD_STORAGE_KEY);

    setThreads(initialThreads);
    setActiveThreadId(initialActiveThread ?? initialThreads[0]?.id ?? null);
    setUserId(getStoredUserId());
  }, []);

  useEffect(() => {
    window.localStorage.setItem(THREADS_STORAGE_KEY, JSON.stringify(threads));
  }, [threads]);

  useEffect(() => {
    if (activeThreadId) {
      window.localStorage.setItem(ACTIVE_THREAD_STORAGE_KEY, activeThreadId);
      return;
    }

    window.localStorage.removeItem(ACTIVE_THREAD_STORAGE_KEY);
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

  const filteredThreads = useMemo(() => {
    const query = search.trim().toLowerCase();

    if (!query) {
      return threads;
    }

    return threads.filter((thread) => {
      return (
        thread.title.toLowerCase().includes(query) ||
        thread.messages.some((message) => message.content.toLowerCase().includes(query))
      );
    });
  }, [threads, search]);

  const activeThread = useMemo(() => {
    return threads.find((thread) => thread.id === activeThreadId) ?? null;
  }, [threads, activeThreadId]);

  const createThread = (firstPrompt?: string) => {
    const thread: Thread = {
      id: uid(),
      title: firstPrompt?.slice(0, 40) || "New conversation",
      updatedAt: new Date().toISOString(),
      messages: [],
    };

    setThreads((current) => [thread, ...current]);
    setActiveThreadId(thread.id);
    return thread.id;
  };

  const startFreshChat = () => {
    setInput("");
    setError("");
    setCodeContext("");
    setShowCodeContext(false);
    createThread();
  };

  const deleteThread = (threadId: string) => {
    setThreads((current) => {
      const nextThreads = current.filter((thread) => thread.id !== threadId);

      if (activeThreadId === threadId) {
        setActiveThreadId(nextThreads[0]?.id ?? null);
      }

      return nextThreads;
    });
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

          return {
            ...thread,
            title: nextTitle ?? thread.title,
            updatedAt: new Date().toISOString(),
            messages: updater(thread.messages),
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

    if (!prompt || isStreaming || !userId) {
      return;
    }

    setError("");
    setInput("");

    const threadId = activeThread?.id ?? createThread(prompt);
    const userMessage = createMessage("user", prompt);
    const assistantMessage = createMessage("assistant", "");
    const title = prompt.slice(0, 48);

    updateThreadMessages(threadId, (messages) => [...messages, userMessage, assistantMessage], title);
    setActiveThreadId(threadId);
    setIsStreaming(true);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: prompt,
          user_id: userId,
          code: codeContext || null,
          mode,
        }),
        signal: controller.signal,
      });

      if (!response.ok || !response.body) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { value, done } = await reader.read();

        if (done) {
          break;
        }

        const chunk = decoder.decode(value, { stream: true });

        updateThreadMessages(threadId, (messages) =>
          messages.map((message) =>
            message.id === assistantMessage.id
              ? { ...message, content: `${message.content}${chunk}` }
              : message,
          ),
        );
      }
    } catch (streamError) {
      const message =
        streamError instanceof Error
          ? streamError.name === "AbortError"
            ? "Generation stopped."
            : streamError.message
          : "Unknown streaming error";

      setError(message);

      updateThreadMessages(threadId, (messages) =>
        messages.map((entry) =>
          entry.id === assistantMessage.id && !entry.content
            ? { ...entry, content: message }
            : entry,
        ),
      );
    } finally {
      abortRef.current = null;
      setIsStreaming(false);
    }
  };

  const handleComposerKeyDown = async (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      await sendMessage();
    }
  };

  return (
    <div className="flex min-h-screen bg-black text-zinc-100">
      <aside className="hidden w-[290px] shrink-0 border-r border-white/10 bg-black/95 lg:flex">
        <div className="flex w-full flex-col px-4 py-5">
          <div className="mb-4 flex items-center gap-3 rounded-2xl border border-white/10 bg-zinc-900 px-4 py-3 shadow-glow">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-zinc-800 text-zinc-100">
              <SparkIcon />
            </div>
            <div>
              <p className="text-sm font-semibold tracking-wide text-zinc-100">Codebot</p>
              <p className="text-xs text-zinc-400">Streaming AI assistant</p>
            </div>
          </div>

          <button
            className="mb-4 flex items-center justify-center gap-2 rounded-2xl bg-white px-4 py-3 text-sm font-semibold text-black transition hover:bg-zinc-200"
            onClick={startFreshChat}
            type="button"
          >
            <EditIcon />
            New chat
          </button>

          <div className="mb-4 rounded-2xl border border-white/10 bg-zinc-900 px-3 py-2">
            <div className="flex items-center gap-2 text-zinc-500">
              <SearchIcon />
              <input
                className="w-full border-none bg-transparent text-sm text-zinc-100 outline-none placeholder:text-zinc-500"
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search chats"
                value={search}
              />
            </div>
          </div>

          <div className="mb-3 flex items-center justify-between px-1 text-xs uppercase tracking-[0.2em] text-zinc-500">
            <span>Recent</span>
            <span>{threads.length}</span>
          </div>

          <div className="flex-1 space-y-2 overflow-y-auto pr-1">
            {filteredThreads.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-white/10 bg-zinc-950 p-4 text-sm text-zinc-400">
                No chats yet. Start a conversation to populate the sidebar.
              </div>
            ) : (
              filteredThreads.map((thread) => {
                const lastMessage = thread.messages[thread.messages.length - 1]?.content || "No messages yet";

                return (
                  <button
                    className={`group w-full rounded-2xl border px-3 py-3 text-left transition ${
                      thread.id === activeThreadId
                        ? "border-white/20 bg-zinc-900"
                        : "border-white/5 bg-zinc-950 hover:border-white/10 hover:bg-zinc-900"
                    }`}
                    key={thread.id}
                    onClick={() => setActiveThreadId(thread.id)}
                    type="button"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium text-zinc-100">{thread.title}</p>
                        <p className="mt-1 line-clamp-2 text-xs text-zinc-400">{lastMessage}</p>
                      </div>
                      <span className="text-[11px] text-zinc-500">{formatRelativeTime(thread.updatedAt)}</span>
                    </div>
                    <div className="mt-3 flex items-center justify-between text-[11px] text-zinc-500">
                      <span>{thread.messages.length} messages</span>
                      <button
                        className="opacity-0 transition group-hover:opacity-100"
                        onClick={(event) => {
                          event.stopPropagation();
                          deleteThread(thread.id);
                        }}
                        type="button"
                      >
                        Delete
                      </button>
                    </div>
                  </button>
                );
              })
            )}
          </div>

          <div className="mt-4 rounded-2xl border border-white/10 bg-zinc-900 p-4">
            <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">Session</p>
            <p className="mt-2 text-sm font-medium text-zinc-100">User ID {userId ?? "..."}</p>
            <p className="mt-1 text-xs text-zinc-400">Stored locally and sent to the backend on each prompt.</p>
          </div>
        </div>
      </aside>

      <main className="flex min-h-screen flex-1 flex-col">
        <header className="sticky top-0 z-10 border-b border-white/10 bg-black/80 backdrop-blur">
          <div className="mx-auto flex w-full max-w-5xl items-center justify-between gap-4 px-4 py-4 sm:px-6">
            <div>
              <p className="text-xs uppercase tracking-[0.26em] text-zinc-500">Codebot workspace</p>
              <h1 className="mt-1 text-lg font-semibold text-zinc-50">Chat interface</h1>
            </div>

            <div className="flex items-center gap-3">
              <button
                className="rounded-xl border border-white/10 bg-zinc-900 px-3 py-2 text-sm text-zinc-200 transition hover:bg-zinc-800 lg:hidden"
                onClick={startFreshChat}
                type="button"
              >
                New chat
              </button>

              <select
                className="rounded-xl border border-white/10 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 outline-none transition hover:bg-zinc-800"
                onChange={(event) => setMode(event.target.value as ChatMode)}
                value={mode}
              >
                <option value="chat">Chat</option>
                <option value="code">Code</option>
                <option value="debug">Debug</option>
                <option value="review">Review</option>
              </select>

              <button
                className="rounded-xl border border-white/10 bg-zinc-900 px-3 py-2 text-sm text-zinc-200 transition hover:bg-zinc-800"
                onClick={() => setShowCodeContext((current) => !current)}
                type="button"
              >
                {showCodeContext ? "Hide code" : "Add code"}
              </button>
            </div>
          </div>
        </header>

        <div className="relative flex-1">
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.05),_transparent_22%),radial-gradient(circle_at_bottom_right,_rgba(255,255,255,0.04),_transparent_18%)]" />

          <div className="relative mx-auto flex w-full max-w-5xl flex-1 flex-col px-4 pb-40 pt-6 sm:px-6">
            {activeThread?.messages.length ? (
              <div className="space-y-8">
                {activeThread.messages.map((message) => (
                  <div
                    className={`flex animate-rise ${message.role === "user" ? "justify-end" : "justify-start"}`}
                    key={message.id}
                  >
                    {message.role === "user" ? (
                      <section className="max-w-[70%] rounded-[28px] bg-zinc-800 px-5 py-3 text-right shadow-lg">
                        <div className="message-content text-sm leading-7 text-zinc-100">
                          {message.content}
                        </div>
                      </section>
                    ) : (
                      <section className="w-full max-w-3xl px-2 py-1">
                        <AssistantMessageContent
                          content={message.content}
                          isStreaming={isStreaming && message.id === activeThread.messages[activeThread.messages.length - 1]?.id}
                        />
                      </section>
                    )}
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>
            ) : (
              <section className="mx-auto mt-8 w-full max-w-3xl rounded-[32px] border border-white/10 bg-zinc-950 p-8 shadow-glow">
                <div className="mb-6 flex items-center gap-4">
                  <div className="flex h-14 w-14 items-center justify-center rounded-3xl bg-zinc-900 text-zinc-100">
                    <SparkIcon />
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-[0.25em] text-zinc-500">Frontend ready</p>
                    <h2 className="mt-2 text-3xl font-semibold text-zinc-50">Ask Codebot anything</h2>
                  </div>
                </div>

                <p className="max-w-2xl text-sm leading-7 text-zinc-400">
                  This UI streams the assistant response directly from your FastAPI endpoint and keeps lightweight
                  local chat history in the sidebar, similar to ChatGPT.
                </p>

                <div className="mt-8 grid gap-3 sm:grid-cols-2">
                  {starterPrompts.map((prompt) => (
                    <button
                      className="rounded-2xl border border-white/10 bg-zinc-900 px-4 py-4 text-left text-sm text-zinc-200 transition hover:bg-zinc-800"
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

          <div className="fixed inset-x-0 bottom-0 z-20 border-t border-white/10 bg-black/90 px-4 py-4 backdrop-blur sm:px-6">
            <div className="mx-auto w-full max-w-5xl">
              {showCodeContext ? (
                <div className="mb-3 rounded-3xl border border-white/10 bg-zinc-950 p-4">
                  <div className="mb-2 flex items-center justify-between">
                    <p className="text-sm font-medium text-zinc-100">Code context</p>
                    <span className="text-xs text-zinc-500">Sent as `code` in the API request</span>
                  </div>
                  <textarea
                    className="min-h-28 w-full resize-y rounded-2xl border border-white/10 bg-black px-4 py-3 text-sm text-zinc-100 outline-none placeholder:text-zinc-500"
                    onChange={(event) => setCodeContext(event.target.value)}
                    placeholder="Paste code here if you want debug/review/code generation context."
                    value={codeContext}
                  />
                </div>
              ) : null}

              <div className="rounded-[28px] border border-white/10 bg-zinc-950 p-3 shadow-glow">
                <div className="flex items-end gap-3">
                  <button
                    className="hidden h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-white/10 bg-zinc-900 text-zinc-300 transition hover:bg-zinc-800 sm:flex"
                    onClick={() => setShowCodeContext((current) => !current)}
                    type="button"
                  >
                    <CodeIcon />
                  </button>

                  <textarea
                    className="max-h-60 min-h-12 flex-1 resize-none border-none bg-transparent px-2 py-3 text-sm leading-6 text-zinc-100 outline-none placeholder:text-zinc-500"
                    onChange={(event) => setInput(event.target.value)}
                    onKeyDown={handleComposerKeyDown}
                    placeholder="Message Codebot..."
                    ref={textAreaRef}
                    rows={1}
                    value={input}
                  />

                  {isStreaming ? (
                    <button
                      className="h-12 shrink-0 rounded-2xl border border-rose-400/20 bg-rose-950 px-4 text-sm font-semibold text-rose-100 transition hover:bg-rose-900"
                      onClick={stopStreaming}
                      type="button"
                    >
                      Stop
                    </button>
                  ) : (
                    <button
                      className="h-12 shrink-0 rounded-2xl bg-white px-5 text-sm font-semibold text-black transition hover:bg-zinc-200 disabled:cursor-not-allowed disabled:bg-zinc-800 disabled:text-zinc-500"
                      disabled={!input.trim()}
                      onClick={() => void sendMessage()}
                      type="button"
                    >
                      Send
                    </button>
                  )}
                </div>

                <div className="mt-3 flex flex-wrap items-center justify-between gap-3 border-t border-white/10 px-2 pt-3 text-xs text-zinc-500">
                  <div className="flex flex-wrap items-center gap-3">
                    <span>Mode: {mode}</span>
                    <span>Streaming: {isStreaming ? "live" : "idle"}</span>
                    <span>Endpoint: /api/chat</span>
                  </div>
                  <span>Enter to send, Shift+Enter for newline</span>
                </div>
              </div>

              {error ? <p className="mt-3 text-sm text-rose-300">{error}</p> : null}
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

export default App;
