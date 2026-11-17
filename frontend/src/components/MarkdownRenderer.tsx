"use client";

import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface MarkdownRendererProps {
  content: string;
  isUser?: boolean;
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content, isUser }) => {
  if (isUser) {
    return <div className="whitespace-pre-wrap">{content}</div>;
  }

  return (
    <div className="markdown-content space-y-2 text-xs sm:text-sm leading-relaxed text-slate-100">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
          strong: ({ children }) => (
            <strong className="font-semibold text-amber-200 tracking-wide">{children}</strong>
          ),
          em: ({ children }) => <em className="italic text-slate-300">{children}</em>,
          ul: ({ children }) => (
            <ul className="list-disc list-outside pl-5 my-2 space-y-1.5 text-slate-200 marker:text-amber-400">
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className="list-decimal list-outside pl-5 my-2 space-y-1.5 text-slate-200 marker:text-amber-400">
              {children}
            </ol>
          ),
          li: ({ children }) => <li className="leading-relaxed pl-0.5">{children}</li>,
          h1: ({ children }) => (
            <h1 className="text-base sm:text-lg font-serif font-bold text-amber-100 mt-3 mb-1.5 pb-1 border-b border-white/[0.08]">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-sm sm:text-base font-serif font-bold text-amber-100 mt-2.5 mb-1">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-xs sm:text-sm font-semibold text-amber-200 mt-2 mb-1">
              {children}
            </h3>
          ),
          code: ({ className, children, ...props }) => {
            const isInline = !className;
            if (isInline) {
              return (
                <code
                  className="px-1.5 py-0.5 rounded-md bg-white/[0.08] font-mono text-[11px] text-amber-300 border border-white/[0.06]"
                  {...props}
                >
                  {children}
                </code>
              );
            }
            return (
              <code className="font-mono text-xs text-slate-200 block overflow-x-auto" {...props}>
                {children}
              </code>
            );
          },
          pre: ({ children }) => (
            <pre className="p-3 my-2.5 rounded-xl bg-[#090c12] border border-white/[0.08] font-mono text-xs overflow-x-auto text-slate-200">
              {children}
            </pre>
          ),
          blockquote: ({ children }) => (
            <blockquote className="border-l-2 border-amber-500/60 pl-3 my-2 italic text-slate-400 bg-white/[0.02] py-1 rounded-r-lg">
              {children}
            </blockquote>
          ),
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-amber-400 hover:text-amber-300 underline underline-offset-2 transition-colors font-medium inline-flex items-center gap-0.5"
            >
              <span>{children}</span>
            </a>
          ),
          table: ({ children }) => (
            <div className="overflow-x-auto my-3 rounded-xl border border-white/[0.08]">
              <table className="w-full text-left text-xs border-collapse">{children}</table>
            </div>
          ),
          thead: ({ children }) => <thead className="bg-white/[0.06] text-amber-300">{children}</thead>,
          tbody: ({ children }) => <tbody className="divide-y divide-white/[0.06]">{children}</tbody>,
          tr: ({ children }) => <tr className="hover:bg-white/[0.02] transition-colors">{children}</tr>,
          th: ({ children }) => <th className="p-2.5 font-semibold font-mono text-[11px]">{children}</th>,
          td: ({ children }) => <td className="p-2.5 text-slate-300">{children}</td>,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};
