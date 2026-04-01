"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  getProject,
  getIssues,
  createIssue,
  updateIssue,
  deleteIssue,
  searchIssues,
} from "@/lib/api";
import IssueCard from "@/components/IssueCard";

interface Issue {
  id: number;
  title: string;
  description: string | null;
  status: string;
  priority: string;
  reporter_id: number;
  assignee_id: number | null;
  created_at: string;
  updated_at: string;
}

interface Project {
  id: number;
  name: string;
  description: string | null;
}

const STATUSES = ["open", "in_progress", "review", "closed"];

export default function ProjectPage() {
  const { id } = useParams<{ id: string }>();
  const projectId = Number(id);

  const [project, setProject] = useState<Project | null>(null);
  const [issues, setIssues] = useState<Issue[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<Issue[] | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [newIssue, setNewIssue] = useState({ title: "", description: "", priority: "medium" });
  const PAGE_SIZE = 10;

  const loadIssues = async () => {
    const data = await getIssues(projectId, {
      page,
      page_size: PAGE_SIZE,
      status: statusFilter || undefined,
    });
    setIssues(data.items);
    setTotal(data.total);
  };

  useEffect(() => {
    getProject(projectId).then(setProject);
  }, [projectId]);

  useEffect(() => {
    loadIssues();
  }, [projectId, page, statusFilter]);

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults(null);
      return;
    }
    try {
      const results = await searchIssues(projectId, searchQuery);
      setSearchResults(results);
    } catch {
      alert("Search is not yet implemented — complete the TODO in issues.py!");
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    await createIssue(projectId, newIssue);
    setNewIssue({ title: "", description: "", priority: "medium" });
    setShowCreate(false);
    await loadIssues();
  };

  const handleStatusChange = async (issueId: number, status: string) => {
    await updateIssue(projectId, issueId, { status });
    setIssues((prev) =>
      prev.map((i) => (i.id === issueId ? { ...i, status } : i))
    );
  };

  const handleDelete = async (issueId: number) => {
    if (!confirm("Delete this issue?")) return;
    await deleteIssue(projectId, issueId);
    setIssues((prev) => prev.filter((i) => i.id !== issueId));
    setTotal((t) => t - 1);
  };

  const displayIssues = searchResults ?? issues;

  return (
    <div className="max-w-5xl mx-auto px-6 py-10">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <Link href="/projects" className="text-sm text-gray-400 hover:text-gray-600 mb-1 block">
            ← Projects
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">{project?.name ?? "Loading…"}</h1>
          {project?.description && (
            <p className="text-gray-500 mt-1 text-sm">{project.description}</p>
          )}
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="bg-brand-600 hover:bg-brand-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          + New Issue
        </button>
      </div>

      {/* Search + Filter bar */}
      <div className="flex gap-3 mb-6">
        <input
          value={searchQuery}
          onChange={(e) => {
            setSearchQuery(e.target.value);
            if (!e.target.value) setSearchResults(null);
          }}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          placeholder="Search issues… (press Enter)"
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
        />
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
        >
          <option value="">All statuses</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>{s.replace("_", " ")}</option>
          ))}
        </select>
      </div>

      {/* Create issue form */}
      {showCreate && (
        <form
          onSubmit={handleCreate}
          className="bg-white border border-gray-200 rounded-xl p-6 mb-6 shadow-sm"
        >
          <h2 className="font-semibold text-lg mb-4">New Issue</h2>
          <input
            required
            value={newIssue.title}
            onChange={(e) => setNewIssue({ ...newIssue, title: e.target.value })}
            placeholder="Issue title"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
          <textarea
            value={newIssue.description}
            onChange={(e) => setNewIssue({ ...newIssue, description: e.target.value })}
            placeholder="Description (optional)"
            rows={3}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
          <select
            value={newIssue.priority}
            onChange={(e) => setNewIssue({ ...newIssue, priority: e.target.value })}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm mb-4 focus:outline-none focus:ring-2 focus:ring-brand-500"
          >
            {["low", "medium", "high", "critical"].map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
          <div className="flex gap-3">
            <button type="submit" className="bg-brand-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-brand-700">
              Create
            </button>
            <button type="button" onClick={() => setShowCreate(false)} className="text-gray-600 px-4 py-2 rounded-lg text-sm border border-gray-300 hover:bg-gray-50">
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Issue list */}
      {displayIssues.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p className="text-lg font-medium">No issues found</p>
        </div>
      ) : (
        <div className="space-y-3">
          {displayIssues.map((issue) => (
            <IssueCard
              key={issue.id}
              issue={issue}
              onStatusChange={handleStatusChange}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      {/* Pagination */}
      {!searchResults && total > PAGE_SIZE && (
        <div className="flex justify-between items-center mt-8">
          <button
            disabled={page === 1}
            onClick={() => setPage((p) => p - 1)}
            className="px-4 py-2 text-sm border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50"
          >
            Previous
          </button>
          <span className="text-sm text-gray-500">
            Page {page} — {total} total issues
          </span>
          <button
            disabled={page * PAGE_SIZE >= total}
            onClick={() => setPage((p) => p + 1)}
            className="px-4 py-2 text-sm border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
