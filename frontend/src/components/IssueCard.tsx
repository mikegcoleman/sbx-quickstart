"use client";

import { useState } from "react";
import clsx from "clsx";

interface Issue {
  id: number;
  title: string;
  description: string | null;
  status: string;
  priority: string;
  created_at: string;
}

interface Props {
  issue: Issue;
  onStatusChange: (id: number, status: string) => void;
  onDelete: (id: number) => void;
}

const PRIORITY_COLORS: Record<string, string> = {
  low: "bg-gray-100 text-gray-600",
  medium: "bg-blue-100 text-blue-700",
  high: "bg-orange-100 text-orange-700",
  critical: "bg-red-100 text-red-700",
};

const STATUS_COLORS: Record<string, string> = {
  open: "bg-green-100 text-green-700",
  in_progress: "bg-yellow-100 text-yellow-700",
  review: "bg-purple-100 text-purple-700",
  closed: "bg-gray-100 text-gray-500",
};

const NEXT_STATUS: Record<string, string> = {
  open: "in_progress",
  in_progress: "review",
  review: "closed",
  closed: "open",
};

export default function IssueCard({ issue, onStatusChange, onDelete }: Props) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm hover:border-gray-300 transition-colors">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-left w-full"
          >
            <p className="font-medium text-gray-900 truncate">{issue.title}</p>
          </button>
          {expanded && issue.description && (
            <p className="text-sm text-gray-500 mt-2 whitespace-pre-wrap">{issue.description}</p>
          )}
          <p className="text-xs text-gray-400 mt-1">
            #{issue.id} · {new Date(issue.created_at).toLocaleDateString()}
          </p>
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          <span
            className={clsx(
              "text-xs font-medium px-2 py-0.5 rounded-full",
              PRIORITY_COLORS[issue.priority] ?? "bg-gray-100 text-gray-600"
            )}
          >
            {issue.priority}
          </span>

          <button
            onClick={() => onStatusChange(issue.id, NEXT_STATUS[issue.status] ?? "open")}
            className={clsx(
              "text-xs font-medium px-2 py-0.5 rounded-full cursor-pointer hover:opacity-80 transition-opacity",
              STATUS_COLORS[issue.status] ?? "bg-gray-100 text-gray-500"
            )}
            title="Click to advance status"
          >
            {issue.status.replace("_", " ")}
          </button>

          <button
            onClick={() => onDelete(issue.id)}
            className="text-gray-300 hover:text-red-500 text-xs transition-colors"
          >
            ✕
          </button>
        </div>
      </div>
    </div>
  );
}
