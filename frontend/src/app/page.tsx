import { redirect } from "next/navigation";

// Root redirects to /projects
export default function Home() {
  redirect("/projects");
}
