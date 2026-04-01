"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getProjects, createProject, deleteProject } from "@/lib/api";

interface Project {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
}

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      const data = await getProjects();
      setProjects(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    await createProject(newName, newDesc || undefined);
    setNewName("");
    setNewDesc("");
    setShowCreate(false);
    await load();
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this project and all its issues?")) return;
    await deleteProject(id);
    setProjects((p) => p.filter((x) => x.id !== id));
  };

  return (
    <div className="max-w-4xl mx-auto px-6 py-10">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Projects</h1>
          <p className="text-gray-500 mt-1 text-sm">Manage your development projects</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="bg-brand-600 hover:bg-brand-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          + New Project
        </button>
      </div>

      {showCreate && (
        <form
          onSubmit={handleCreate}
          className="bg-white border border-gray-200 rounded-xl p-6 mb-6 shadow-sm"
        >
          <h2 className="text-lg font-semibold mb-4">New Project</h2>
          <input
            required
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="Project name"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
          <textarea
            value={newDesc}
            onChange={(e) => setNewDesc(e.target.value)}
            placeholder="Description (optional)"
            rows={2}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-4 focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
          <div className="flex gap-3">
            <button
              type="submit"
              className="bg-brand-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-brand-700"
            >
              Create
            </button>
            <button
              type="button"
              onClick={() => setShowCreate(false)}
              className="text-gray-600 px-4 py-2 rounded-lg text-sm border border-gray-300 hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {loading ? (
        <p className="text-gray-500 text-sm">Loading…</p>
      ) : projects.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p className="text-lg font-medium">No projects yet</p>
          <p className="text-sm mt-1">Create your first project to get started</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {projects.map((p) => (
            <div
              key={p.id}
              className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm flex items-start justify-between hover:border-brand-500 transition-colors"
            >
              <div>
                <Link
                  href={`/projects/${p.id}`}
                  className="text-lg font-semibold text-gray-900 hover:text-brand-600"
                >
                  {p.name}
                </Link>
                {p.description && (
                  <p className="text-gray-500 text-sm mt-0.5">{p.description}</p>
                )}
                <p className="text-xs text-gray-400 mt-2">
                  Created {new Date(p.created_at).toLocaleDateString()}
                </p>
              </div>
              <button
                onClick={() => handleDelete(p.id)}
                className="text-gray-400 hover:text-red-500 text-xs mt-1 transition-colors"
              >
                Delete
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
