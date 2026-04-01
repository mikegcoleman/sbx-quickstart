import axios from "axios";
import Cookies from "js-cookie";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
});

// Attach token from cookie on every request
api.interceptors.request.use((config) => {
  const token = Cookies.get("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Redirect to login on 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && typeof window !== "undefined") {
      Cookies.remove("access_token");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

// ── Auth ──────────────────────────────────────────────────────────────────────

export async function login(username: string, password: string) {
  const form = new URLSearchParams({ username, password });
  const res = await api.post("/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  Cookies.set("access_token", res.data.access_token, { expires: 1 });
  return res.data;
}

export async function register(email: string, username: string, password: string) {
  const res = await api.post("/auth/register", { email, username, password });
  return res.data;
}

export async function getMe() {
  const res = await api.get("/auth/me");
  return res.data;
}

export function logout() {
  Cookies.remove("access_token");
}

// ── Projects ──────────────────────────────────────────────────────────────────

export async function getProjects() {
  const res = await api.get("/projects/");
  return res.data;
}

export async function createProject(name: string, description?: string) {
  const res = await api.post("/projects/", { name, description });
  return res.data;
}

export async function getProject(id: number) {
  const res = await api.get(`/projects/${id}`);
  return res.data;
}

export async function deleteProject(id: number) {
  await api.delete(`/projects/${id}`);
}

// ── Issues ────────────────────────────────────────────────────────────────────

export interface IssueFilters {
  page?: number;
  page_size?: number;
  status?: string;
  priority?: string;
}

export async function getIssues(projectId: number, filters: IssueFilters = {}) {
  const res = await api.get(`/projects/${projectId}/issues/`, { params: filters });
  return res.data; // { total, page, page_size, items }
}

export async function getIssue(projectId: number, issueId: number) {
  const res = await api.get(`/projects/${projectId}/issues/${issueId}`);
  return res.data;
}

export async function createIssue(
  projectId: number,
  data: { title: string; description?: string; priority?: string; assignee_id?: number }
) {
  const res = await api.post(`/projects/${projectId}/issues/`, data);
  return res.data;
}

export async function updateIssue(
  projectId: number,
  issueId: number,
  data: { title?: string; description?: string; status?: string; priority?: string }
) {
  const res = await api.put(`/projects/${projectId}/issues/${issueId}`, data);
  return res.data;
}

export async function searchIssues(projectId: number, q: string) {
  const res = await api.get(`/projects/${projectId}/issues/search`, { params: { q } });
  return res.data;
}

export async function deleteIssue(projectId: number, issueId: number) {
  await api.delete(`/projects/${projectId}/issues/${issueId}`);
}

// ── Comments ──────────────────────────────────────────────────────────────────

export async function getComments(projectId: number, issueId: number) {
  const res = await api.get(`/projects/${projectId}/issues/${issueId}/comments/`);
  return res.data;
}

export async function addComment(projectId: number, issueId: number, content: string) {
  const res = await api.post(`/projects/${projectId}/issues/${issueId}/comments/`, { content });
  return res.data;
}
