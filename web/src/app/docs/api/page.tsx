import type { Metadata } from "next";
import { PageHero, Section, SectionTitle } from "@/components/site/page-parts";
import { cn } from "@/lib/utils";

export const metadata: Metadata = {
  title: "API Reference — AgentMesh",
  description:
    "REST endpoints for organizations, workflow runs, agents, network stats, and health.",
};

type Endpoint = {
  method: "GET" | "POST";
  path: string;
  description: string;
  live?: boolean;
};

const endpoints: Endpoint[] = [
  {
    method: "GET",
    path: "/api/health",
    description: "Service health, including a live database connectivity probe.",
    live: true,
  },
  {
    method: "GET",
    path: "/api/stats",
    description: "Live network statistics (agents, transactions, proposals, TVL).",
    live: true,
  },
  {
    method: "POST",
    path: "/v1/organizations",
    description: "Create an organization with roles, permissions, and wallets.",
  },
  {
    method: "POST",
    path: "/v1/organizations/{id}/runs",
    description: "Submit a goal; the mesh analyzes, debates, and reaches consensus.",
  },
  {
    method: "GET",
    path: "/v1/runs/{id}",
    description: "Fetch a run's status, consensus result, and Casper tx hash.",
  },
  {
    method: "GET",
    path: "/v1/agents",
    description: "List available agents and their capabilities.",
  },
];

const methodColor: Record<Endpoint["method"], string> = {
  GET: "bg-success/15 text-success",
  POST: "bg-brand/15 text-brand",
};

export default function ApiReferencePage() {
  return (
    <>
      <PageHero
        eyebrow="Developers"
        title="API Reference"
        description="A REST API for creating organizations, running workflows, and reading live network data. Endpoints marked live are available in this deployment today."
      />

      <Section>
        <SectionTitle eyebrow="Authentication" title="Bearer tokens" />
        <div className="mt-6 overflow-x-auto rounded-xl border border-border bg-card p-6">
          <pre className="font-mono text-xs leading-relaxed text-muted-foreground sm:text-sm">
{`curl https://api.agentmesh.world/v1/agents \\
  -H "Authorization: Bearer $AGENTMESH_API_KEY"`}
          </pre>
        </div>
      </Section>

      <Section className="border-t border-border bg-secondary/20">
        <SectionTitle eyebrow="Endpoints" title="Core resources" />
        <div className="mt-8 overflow-hidden rounded-xl border border-border">
          {endpoints.map((ep, i) => (
            <div
              key={ep.path}
              className={cn(
                "flex flex-col gap-2 bg-card p-5 sm:flex-row sm:items-center sm:gap-5",
                i !== 0 && "border-t border-border",
              )}
            >
              <span
                className={cn(
                  "inline-flex w-fit items-center rounded-md px-2.5 py-1 font-mono text-xs font-bold",
                  methodColor[ep.method],
                )}
              >
                {ep.method}
              </span>
              <code className="font-mono text-sm text-foreground">
                {ep.path}
              </code>
              <span className="flex-1 text-sm text-muted-foreground">
                {ep.description}
              </span>
              {ep.live && (
                <span className="w-fit rounded-full bg-success/15 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-success">
                  Live
                </span>
              )}
            </div>
          ))}
        </div>
        <p className="mt-4 text-xs text-muted-foreground">
          Try the live endpoints:{" "}
          <a
            href="/api/health"
            className="text-brand underline-offset-4 hover:underline"
          >
            /api/health
          </a>{" "}
          ·{" "}
          <a
            href="/api/stats"
            className="text-brand underline-offset-4 hover:underline"
          >
            /api/stats
          </a>
        </p>
      </Section>
    </>
  );
}
